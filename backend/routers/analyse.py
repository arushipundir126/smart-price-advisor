"""
FILE: backend/routers/analyse.py

WHAT THIS DOES:
POST /api/analyse. Orchestrates the whole analysis engine: guess the category,
fetch prices across marketplaces, pull price history and the next sale from the
database (best effort), fetch news, run the six signals, aggregate them, and ask
Gemini (or the deterministic fallback) for the final verdict. Assembles the full
verdict object the frontend consumes. Rate limited to 10 requests per minute.

CHANGES THIS SESSION:
- Replaced the stub with the full orchestration, brand/vague check, category
  guess, best-effort DB use, six-signal run, and verdict assembly.
- Build signal_summaries and stackable_discounts from our own six signal objects
  instead of Gemini's echo, so all six always show and discounts never vanish.

WHERE IT FITS:
The main user-facing endpoint and the join point of the analysis engine.

CALLED BY / IMPORTS FROM:
Imports the six signals, the aggregator, the service clients, the db helpers, and
the shared limiter. Mounted by main.py.
"""
import re
import statistics

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from limiter import limiter
from services.apify_client import fetch_prices
from services.serpapi_client import fetch_shopping_prices
from services.newsapi_client import get_news
from services.gemini_client import synthesise_verdict
from signals import (
    cross_platform,
    category_elasticity,
    days_to_sale,
    fake_discount,
    news_shock,
    price_trend,
)

router = APIRouter(prefix="/api", tags=["analyse"])

# Generic category words. A query made of ONLY these (plus descriptors, sizes
# and numbers) has no brand, so we ask the user to name one. This is a superset
# of common Indian shopping categories, not an exhaustive list.
_GENERIC_TERMS = {
    "phone", "mobile", "smartphone", "laptop", "computer", "pc", "tablet", "tab",
    "tv", "television", "shoes", "shoe", "sneakers", "sandals", "slippers",
    "watch", "smartwatch", "headphones", "headphone", "earphones", "earphone",
    "earbuds", "speaker", "soundbar", "fridge", "refrigerator", "ac",
    "conditioner", "microwave", "mixer", "grinder", "kettle", "toaster", "oven",
    "washing", "machine", "camera", "mouse", "keyboard", "monitor", "charger",
    "powerbank", "oil", "rice", "atta", "flour", "wheat", "sugar", "salt", "dal",
    "milk", "bread", "butter", "ghee", "tea", "coffee", "shampoo", "soap",
    "toothpaste", "facewash", "wash", "face", "moisturizer", "moisturiser",
    "cream", "lotion", "serum", "foundation", "lipstick", "kajal", "mascara",
    "perfume", "deodorant", "sunscreen", "book", "notebook", "pen", "bag",
    "backpack", "jeans", "shirt", "tshirt", "dress", "kurta", "saree", "jacket",
    "trousers", "top", "petrol", "diesel", "fuel", "power", "bank",
}

# Descriptor words that qualify a product but do NOT identify a brand.
_DESCRIPTOR_TERMS = {
    "sunflower", "mustard", "coconut", "olive", "groundnut", "soybean", "soya",
    "vegetable", "cooking", "refined", "virgin", "extra", "pure", "organic",
    "basmati", "brown", "white", "black", "blue", "green", "red", "matte",
    "liquid", "dewy", "wireless", "bluetooth", "smart", "gaming", "running",
    "sports", "casual", "formal", "mens", "womens", "kids", "men", "women",
    "unisex", "cotton", "silk", "leather", "herbal", "ayurvedic", "whitening",
    "anti", "dandruff", "moisturizing", "hydrating", "premium", "deluxe",
    "classic", "original", "fresh", "natural", "gold", "super", "combo", "pack",
    "set", "piece", "pcs", "size", "large", "medium", "small", "new",
}

# A token that is only a number, or a number with a unit (1l, 500ml, 128gb).
_UNIT_RE = re.compile(
    r"^\d+(ml|l|kg|g|gm|gb|tb|mm|cm|inch|in|w|ltr|litre|liter|pack)?$"
)

# Keyword -> category guesses. First match wins; order matters.
_CATEGORY_HINTS = [
    (("iphone", "galaxy", "redmi", "oneplus", "pixel", "vivo", "oppo", "realme", "smartphone", "phone"), "smartphones"),
    (("macbook", "laptop", "thinkpad", "ideapad", "vivobook"), "laptops"),
    (("ipad", "tablet", "tab "), "tablets"),
    (("tv", "television", "oled", "qled"), "televisions"),
    (("headphone", "earbuds", "earphone", "wh-1000", "airpods", "soundbar"), "audio"),
    (("watch", "band", "smartwatch"), "wearables"),
    (("shoe", "sneaker", "running", "nike", "adidas", "puma"), "footwear"),
    (("shirt", "jeans", "dress", "kurta", "tshirt", "t-shirt", "jacket"), "fashion_clothing"),
    (("lipstick", "serum", "cream", "foundation", "shampoo"), "beauty_skincare"),
    (("refrigerator", "fridge", "washing machine", "air conditioner"), "large_appliances"),
    (("mixer", "grinder", "microwave", "kettle", "toaster"), "kitchen_appliances"),
    (("book",), "books"),
    (("onion", "tomato", "rice", "wheat", "potato", "dal"), "grocery_staples"),
    (("petrol", "diesel"), "fuel"),
]


class AnalyseRequest(BaseModel):
    # product: required, non-empty, max 200 chars (server-side validation rule).
    product: str = Field(min_length=1, max_length=200)
    # wait_tolerance_days: integer 1-365 (presets 7, 30, 90, 180, 365 or custom).
    wait_tolerance_days: int = Field(ge=1, le=365)


def _guess_category(name: str) -> str | None:
    """Best-effort category from the product name. None if nothing matches."""
    low = name.lower()
    for keywords, category in _CATEGORY_HINTS:
        if any(k in low for k in keywords):
            return category
    return None


def _is_vague(name: str) -> bool:
    """True when the query names a category but no brand.

    Strips generic category words, descriptors, sizes and numbers. If nothing is
    left, there is no brand token, so we cannot give an accurate verdict and ask
    the user to add one. 'sunflower oil' -> vague; 'Fortune sunflower oil' -> ok.
    """
    tokens = re.findall(r"[a-z0-9]+", name.lower())
    if not tokens:
        return True
    for tok in tokens:
        if tok in _GENERIC_TERMS or tok in _DESCRIPTOR_TERMS:
            continue
        if _UNIT_RE.match(tok):
            continue
        # A word we do not recognise as generic is treated as a brand/model.
        return False
    return True


def _platform_prices(price_rows: list[dict], limit: int = 6) -> list[dict]:
    """Cheapest price per platform, sorted low to high, for the comparison list.

    Lets the user see the price across trusted sellers, not just the single best.
    """
    cheapest: dict[str, dict] = {}
    for row in price_rows:
        label = row.get("platform_label") or row.get("platform") or "Seller"
        price = float(row["price"])
        if label not in cheapest or price < cheapest[label]["price"]:
            cheapest[label] = {
                "platform": label,
                "price": price,
                "buy_link": row.get("url"),
            }
    return sorted(cheapest.values(), key=lambda r: r["price"])[:limit]


def _clean_snapshots(snapshots: list[dict]) -> list[dict]:
    """Drop outlier snapshots so old junk (Rs 1, accessories) does not skew the
    median, the trend, or the chart. Keeps points within 40% to 300% of the
    median. Snapshots are append-only in the DB, so we filter here for display.
    """
    prices = [float(s["price"]) for s in snapshots if s.get("price") is not None]
    if len(prices) < 3:
        return snapshots
    median = statistics.median(prices)
    lo, hi = median * 0.40, median * 3.0
    return [s for s in snapshots if lo <= float(s["price"]) <= hi]


@router.post("/analyse")
@limiter.limit("10/minute")
def analyse(req: AnalyseRequest, request: Request):
    product = req.product.strip()

    # Edge case: vague query with no brand. Ask for a brand instead of guessing.
    if _is_vague(product):
        return {
            "error": "vague_query",
            "message": "Please include the brand name for an accurate verdict, "
            "for example 'Samsung Galaxy S24' instead of just 'phone'.",
        }

    category = _guess_category(product)

    # 1. Prices across marketplaces (Apify first, SerpAPI fills gaps).
    price_rows = fetch_prices(product)
    price_rows += fetch_shopping_prices(product)

    # 2. Database-backed context. Best effort: if the DB is down, these stay
    #    empty and the history signals simply abstain.
    product_id = None
    median = None
    snapshots: list[dict] = []
    next_sale = None
    try:
        from db.products import find_or_create_product
        from db.price_snapshots import add_snapshot, get_snapshots
        from db.sale_calendar import get_next_sale

        record = find_or_create_product(product, category=category)
        product_id = record["id"]
        # Append this lookup's prices so history grows over time.
        for row in price_rows:
            add_snapshot(
                product_id, row["platform"], row["price"], row.get("mrp")
            )
        snapshots = _clean_snapshots(get_snapshots(product_id))
        # Median from the cleaned history so junk points do not distort it.
        clean_prices = [float(s["price"]) for s in snapshots]
        median = statistics.median(clean_prices) if clean_prices else None
        next_sale = get_next_sale(category)
    except Exception:
        pass  # degrade gracefully; verdict still produced

    # 3. News for the shock signal (mock unless a key is set; cached 1h).
    headlines = get_news(product_id or product, product)

    # 4. Run the six signals.
    entry = category_elasticity.get_entry(category)
    worth_waiting = entry["worth_waiting"] if entry else True

    s_fake = fake_discount.evaluate(price_rows, median)
    s_cross = cross_platform.evaluate(price_rows)
    s_trend = price_trend.evaluate(snapshots)
    s_sale = days_to_sale.evaluate(next_sale, req.wait_tolerance_days, worth_waiting)
    s_cat = category_elasticity.evaluate(category)
    s_news = news_shock.evaluate(headlines)
    signals = [s_fake, s_cross, s_trend, s_sale, s_cat, s_news]

    # 5. Final verdict (Gemini when configured, deterministic fallback otherwise).
    verdict = synthesise_verdict(
        product, category, signals, headlines, req.wait_tolerance_days
    )

    # 6. Assemble the response with the action fields from the signals.
    next_sale_out = None
    if next_sale:
        next_sale_out = {
            "name": next_sale.get("sale_name"),
            "start_date": str(next_sale.get("start_date")),
            "platform": next_sale.get("platform"),
        }

    # Build the signal breakdown and stackable discounts from OUR six signals,
    # not from Gemini's retelling, so all six always show with their real votes
    # and reasons, and bank offers/coupons never silently vanish.
    signal_summaries = [
        {
            "signal": s.get("signal_name", "signal"),
            "vote": s.get("vote"),
            "plain_reason": s.get("reason", ""),
        }
        for s in signals
    ]
    stackable_discounts = []
    for s in signals:
        for offer in s.get("stackable_discounts", []) or []:
            stackable_discounts.append(offer)

    return {
        "product": product,
        "category": category,
        "verdict": verdict.get("verdict"),
        "confidence": verdict.get("confidence"),
        "summary_reason": verdict.get("summary_reason"),
        "wait_estimate_days": verdict.get("wait_estimate_days"),
        "best_price": s_cross.get("best_price"),
        "best_platform": s_cross.get("best_platform_label"),
        "buy_link": s_cross.get("buy_link"),
        "price_vs_median": s_fake.get("price_vs_median"),
        # Oldest to newest price points for the sparkline, plus the median line.
        "price_history": [float(s["price"]) for s in reversed(snapshots)],
        "price_median": median,
        "next_sale": next_sale_out,
        "stackable_discounts": stackable_discounts,
        "signal_summaries": signal_summaries,
        "platform_prices": _platform_prices(price_rows),
        "product_id": product_id,
    }

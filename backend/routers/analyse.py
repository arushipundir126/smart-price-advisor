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

WHERE IT FITS:
The main user-facing endpoint and the join point of the analysis engine.

CALLED BY / IMPORTS FROM:
Imports the six signals, the aggregator, the service clients, the db helpers, and
the shared limiter. Mounted by main.py.
"""
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

# Single generic words that are not specific enough for a verdict (no brand).
_VAGUE_TERMS = {
    "phone", "mobile", "laptop", "tv", "television", "shoes", "shoe",
    "watch", "headphones", "earphones", "fridge", "ac", "washing machine",
}

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
    """True when the query is a bare generic term with no brand or model."""
    return name.strip().lower() in _VAGUE_TERMS


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
        from db.price_snapshots import add_snapshot, get_median_price, get_snapshots
        from db.sale_calendar import get_next_sale

        record = find_or_create_product(product, category=category)
        product_id = record["id"]
        # Append this lookup's prices so history grows over time.
        for row in price_rows:
            add_snapshot(
                product_id, row["platform"], row["price"], row.get("mrp")
            )
        median = get_median_price(product_id)
        snapshots = get_snapshots(product_id)
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
        "next_sale": next_sale_out,
        "stackable_discounts": verdict.get("stackable_discounts", []),
        "signal_summaries": verdict.get("signal_summaries", []),
        "product_id": product_id,
    }

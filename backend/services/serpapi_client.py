"""
FILE: backend/services/serpapi_client.py

WHAT THIS DOES:
Fallback price source using SerpAPI's Google Shopping results (India). Used when
Apify has no actor for a marketplace or a scrape fails, so we can still show a
real price across many Indian sellers. Same two-mode design as the Apify client:
real call when SERPAPI_KEY is set, otherwise built-in mock data.

CHANGES THIS SESSION:
- Added fetch_shopping_prices() with a real SerpAPI path and mock demo data,
  returning the same result shape as services/apify_client.

WHERE IT FITS:
Second service client. Fills gaps left by Apify so Signal 2 (cross-platform best
price) can compare a wide set of sellers. If this also fails, the caller shows a
direct search link, never a guessed number.

CALLED BY / IMPORTS FROM:
Reads SERPAPI_KEY from the environment. Imports httpx lazily (only in the real
path). Uses normalise_name from db/products for demo matching.
"""
import os

from db.products import normalise_name

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"
REQUEST_TIMEOUT_SECONDS = 10

# Mock sellers for demo products. Deliberately includes marketplaces the Apify
# mock does not, to show SerpAPI widening the coverage. Prices in INR.
_MOCK_SHOPPING: dict[str, list[dict]] = {
    "samsung galaxy s24": [
        {"platform": "tata_cliq", "label": "Tata CLiQ", "price": 62499},
        {"platform": "vijay_sales", "label": "Vijay Sales", "price": 63499},
    ],
    "iphone 15": [
        {"platform": "tata_cliq", "label": "Tata CLiQ", "price": 66499},
        {"platform": "vijay_sales", "label": "Vijay Sales", "price": 66990},
    ],
    "sony wh-1000xm5": [
        {"platform": "croma", "label": "Croma", "price": 27990},
    ],
    "nike revolution": [
        {"platform": "tata_cliq", "label": "Tata CLiQ", "price": 3599},
    ],
}


def _real_enabled() -> bool:
    """True only when a SerpAPI key is configured."""
    return bool(os.getenv("SERPAPI_KEY"))


def _fetch_mock(product_name: str) -> list[dict]:
    """Return demo shopping results for a known product, else []."""
    normalised = normalise_name(product_name)
    for key, rows in _MOCK_SHOPPING.items():
        if key in normalised:
            from urllib.parse import quote_plus

            q = quote_plus(product_name)
            return [
                {
                    "platform": r["platform"],
                    "platform_label": r["label"],
                    "product_name": product_name,
                    "price": float(r["price"]),
                    "mrp": None,  # Google Shopping rarely exposes MRP
                    "url": f"https://www.google.com/search?tbm=shop&q={q}",
                    "source": "serpapi_mock",
                }
                for r in rows
            ]
    return []


def _fetch_real(product_name: str) -> list[dict]:
    """Query SerpAPI Google Shopping for Indian prices. Failure returns []."""
    import httpx

    params = {
        "engine": "google_shopping",
        "q": product_name,
        "gl": "in",   # India
        "hl": "en",   # English
        "api_key": os.getenv("SERPAPI_KEY"),
    }
    try:
        resp = httpx.get(
            SERPAPI_ENDPOINT, params=params, timeout=REQUEST_TIMEOUT_SECONDS
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    results = []
    for item in data.get("shopping_results", []):
        price = item.get("extracted_price")
        if price is None:
            continue
        seller = item.get("source") or "Google Shopping"
        results.append(
            {
                "platform": normalise_name(seller).replace(" ", "_"),
                "platform_label": seller,
                "product_name": item.get("title") or product_name,
                "price": float(price),
                "mrp": None,
                "url": item.get("product_link") or item.get("link"),
                "source": "serpapi",
            }
        )
    return results


def fetch_shopping_prices(product_name: str) -> list[dict]:
    """Cross-seller prices via SerpAPI, or built-in demo data when no key is set."""
    if _real_enabled():
        real = _fetch_real(product_name)
        if real:
            return real
    return _fetch_mock(product_name)

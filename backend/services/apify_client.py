"""
FILE: backend/services/apify_client.py

WHAT THIS DOES:
Fetches live price and MRP for a product across trusted Indian marketplaces
using Apify actors. Two modes in one file: a real Apify path (used when a token
and actor ids are configured) and built-in mock data for a few demo products so
the whole app works before any real actor is set up. Callers do not care which
mode runs.

CHANGES THIS SESSION:
- Added the trusted-platform registry, mock demo data, and fetch_prices() with
  a real Apify path (10s per-actor timeout) that falls back to mock.

WHERE IT FITS:
First service client. Feeds Signal 1 (fake-discount, needs price + MRP) and
Signal 2 (cross-platform best price). When an actor is missing for a platform,
SerpAPI (serpapi_client.py) covers it later.

CALLED BY / IMPORTS FROM:
Reads APIFY_API_TOKEN from the environment. Imports ApifyClient lazily (only in
the real path) so mock mode needs nothing installed. Uses normalise_name from
db/products for demo matching.
"""
import os
from typing import Optional

from db.products import normalise_name

# Trusted Indian marketplaces. actor_id stays None until a real Apify actor is
# configured for that platform; platforms without an actor are covered by
# SerpAPI Google Shopping in the cross-platform signal.
PLATFORM_ACTORS: dict[str, dict] = {
    "amazon": {"label": "Amazon India", "actor_id": None},
    "flipkart": {"label": "Flipkart", "actor_id": None},
    "croma": {"label": "Croma", "actor_id": None},
    "reliance_digital": {"label": "Reliance Digital", "actor_id": None},
    "tata_cliq": {"label": "Tata CLiQ", "actor_id": None},
    "vijay_sales": {"label": "Vijay Sales", "actor_id": None},
    "myntra": {"label": "Myntra", "actor_id": None},
    "ajio": {"label": "Ajio", "actor_id": None},
    "nykaa": {"label": "Nykaa", "actor_id": None},
    "jiomart": {"label": "JioMart", "actor_id": None},
    "snapdeal": {"label": "Snapdeal", "actor_id": None},
    "meesho": {"label": "Meesho", "actor_id": None},
}

# Per-actor time budget. Beyond this we drop that platform and move on so one
# slow marketplace never blocks the verdict (CLAUDE.md fallback rule).
ACTOR_TIMEOUT_SECONDS = 10

# Built-in demo data: keyed by a substring of the normalised product name.
# Prices in INR. MRP is deliberately higher so the fake-discount signal has
# something real to measure against.
_MOCK_PRODUCTS: dict[str, list[dict]] = {
    "samsung galaxy s24": [
        {"platform": "amazon", "price": 62999, "mrp": 79999},
        {"platform": "flipkart", "price": 61499, "mrp": 79999},
        {"platform": "croma", "price": 64999, "mrp": 79999},
        {"platform": "reliance_digital", "price": 63999, "mrp": 79999},
    ],
    "iphone 15": [
        {"platform": "amazon", "price": 65999, "mrp": 79900},
        {"platform": "flipkart", "price": 65490, "mrp": 79900},
        {"platform": "croma", "price": 67990, "mrp": 79900},
    ],
    "sony wh-1000xm5": [
        {"platform": "amazon", "price": 26990, "mrp": 34990},
        {"platform": "flipkart", "price": 27499, "mrp": 34990},
    ],
    "nike revolution": [
        {"platform": "myntra", "price": 3495, "mrp": 4995},
        {"platform": "ajio", "price": 3695, "mrp": 4995},
        {"platform": "amazon", "price": 3799, "mrp": 4995},
    ],
}


def _real_enabled() -> bool:
    """True only when a token exists and at least one platform has an actor id."""
    if not os.getenv("APIFY_API_TOKEN"):
        return False
    return any(p["actor_id"] for p in PLATFORM_ACTORS.values())


def _search_url(platform: str, product_name: str) -> str:
    """A direct buy/search link so every result is clickable."""
    from urllib.parse import quote_plus

    q = quote_plus(product_name)
    links = {
        "amazon": f"https://www.amazon.in/s?k={q}",
        "flipkart": f"https://www.flipkart.com/search?q={q}",
        "croma": f"https://www.croma.com/searchB?q={q}",
        "reliance_digital": f"https://www.reliancedigital.in/search?q={q}",
        "tata_cliq": f"https://www.tatacliq.com/search/?searchCategory=all&text={q}",
        "vijay_sales": f"https://www.vijaysales.com/search/{q}",
        "myntra": f"https://www.myntra.com/{q}",
        "ajio": f"https://www.ajio.com/search/?text={q}",
        "nykaa": f"https://www.nykaa.com/search/result/?q={q}",
        "jiomart": f"https://www.jiomart.com/search/{q}",
        "snapdeal": f"https://www.snapdeal.com/search?keyword={q}",
        "meesho": f"https://www.meesho.com/search?q={q}",
    }
    return links.get(platform, f"https://www.google.com/search?q={q}")


def _fetch_mock(product_name: str) -> list[dict]:
    """Return demo results if the product matches a known demo key, else []."""
    normalised = normalise_name(product_name)
    for key, rows in _MOCK_PRODUCTS.items():
        if key in normalised:
            return [
                {
                    "platform": r["platform"],
                    "platform_label": PLATFORM_ACTORS.get(r["platform"], {}).get(
                        "label", r["platform"]
                    ),
                    "product_name": product_name,
                    "price": float(r["price"]),
                    "mrp": float(r["mrp"]) if r.get("mrp") is not None else None,
                    "url": _search_url(r["platform"], product_name),
                    "source": "mock",
                }
                for r in rows
            ]
    return []


def _fetch_real(
    product_name: str, asin: Optional[str], flipkart_pid: Optional[str]
) -> list[dict]:
    """Run each configured actor and collect its result. Failures are skipped."""
    from apify_client import ApifyClient  # lazy: only needed in the real path

    client = ApifyClient(os.getenv("APIFY_API_TOKEN"))
    results: list[dict] = []
    for platform, cfg in PLATFORM_ACTORS.items():
        actor_id = cfg["actor_id"]
        if not actor_id:
            continue
        try:
            # run_input shape depends on the specific actor chosen; adjust per actor.
            run_input = {"search": product_name, "asin": asin, "pid": flipkart_pid}
            run = client.actor(actor_id).call(
                run_input=run_input, timeout_secs=ACTOR_TIMEOUT_SECONDS
            )
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                results.append(
                    {
                        "platform": platform,
                        "platform_label": cfg["label"],
                        "product_name": item.get("title") or product_name,
                        "price": float(item["price"]),
                        "mrp": float(item["mrp"]) if item.get("mrp") else None,
                        "url": item.get("url") or _search_url(platform, product_name),
                        "source": "apify",
                    }
                )
        except Exception:
            # One platform failing must never block the others or the verdict.
            continue
    return results


def fetch_prices(
    product_name: str,
    asin: Optional[str] = None,
    flipkart_pid: Optional[str] = None,
) -> list[dict]:
    """Price + MRP per platform for a product.

    Uses real Apify when configured; otherwise returns built-in demo data. An
    empty list means "no price found here", and the caller falls back to SerpAPI
    or a direct search link.
    """
    if _real_enabled():
        real = _fetch_real(product_name, asin, flipkart_pid)
        if real:
            return real
    return _fetch_mock(product_name)

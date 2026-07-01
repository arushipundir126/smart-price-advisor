"""
FILE: backend/services/newsapi_client.py

WHAT THIS DOES:
Fetches recent news headlines for a product and caches them per product for one
hour in the news_cache table, to protect the limited NewsAPI free-tier quota.
Two modes: real NewsAPI call when NEWSAPI_KEY is set, otherwise mock headlines.

CHANGES THIS SESSION:
- Added get_news() with a best-effort 1-hour cache, plus real and mock fetch.

WHERE IT FITS:
Third service client. Supplies the last-7-days headlines that Signal 6
(news-shock detector) and later Gemini reason over. Uses the news_cache table
created in db/schema.sql.

CALLED BY / IMPORTS FROM:
Reads NEWSAPI_KEY from the environment. Imports httpx lazily (real path only)
and get_client from db/supabase_client for the cache. Called by the news_shock
signal.
"""
import os
from datetime import date, datetime, timedelta, timezone

NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"
REQUEST_TIMEOUT_SECONDS = 10
CACHE_TTL_HOURS = 1
LOOKBACK_DAYS = 7
MAX_HEADLINES = 5


def _real_enabled() -> bool:
    """True only when a NewsAPI key is configured."""
    return bool(os.getenv("NEWSAPI_KEY"))


def _get_cached(product_id: str) -> list[dict] | None:
    """Return fresh cached headlines for a product, or None. Best effort.

    Any database problem returns None so news still works, just uncached.
    """
    try:
        from db.supabase_client import get_client

        now = datetime.now(timezone.utc).isoformat()
        result = (
            get_client()
            .table("news_cache")
            .select("headlines, expires_at")
            .eq("product_id", product_id)
            .gt("expires_at", now)
            .order("cached_at", desc=True)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]["headlines"]
    except Exception:
        return None
    return None


def _store_cache(product_id: str, headlines: list[dict]) -> None:
    """Save headlines with a 1-hour expiry. Best effort, never raises."""
    try:
        from db.supabase_client import get_client

        expires_at = datetime.now(timezone.utc) + timedelta(hours=CACHE_TTL_HOURS)
        (
            get_client()
            .table("news_cache")
            .insert(
                {
                    "product_id": product_id,
                    "headlines": headlines,
                    "expires_at": expires_at.isoformat(),
                }
            )
            .execute()
        )
    except Exception:
        return


def _fetch_mock(query: str) -> list[dict]:
    """Realistic placeholder headlines so the flow works without a key."""
    today = date.today().isoformat()
    return [
        {
            "title": f"{query}: prices steady this week across Indian retailers",
            "description": "Retailers hold pricing ahead of the festive sale season.",
            "published_at": today,
        },
        {
            "title": f"Successor to {query} rumoured for later this year",
            "description": "Reports suggest a new model, which can soften current prices.",
            "published_at": today,
        },
    ]


def _fetch_real(query: str) -> list[dict]:
    """Query NewsAPI for the last 7 days. Failure returns []."""
    import httpx

    from_date = (date.today() - timedelta(days=LOOKBACK_DAYS)).isoformat()
    params = {
        "q": f'{query} AND (price OR launch OR discount)',
        "from": from_date,
        "sortBy": "publishedAt",
        "pageSize": MAX_HEADLINES,
        "language": "en",
        "apiKey": os.getenv("NEWSAPI_KEY"),
    }
    try:
        resp = httpx.get(
            NEWSAPI_ENDPOINT, params=params, timeout=REQUEST_TIMEOUT_SECONDS
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    return [
        {
            "title": a.get("title"),
            "description": a.get("description"),
            "published_at": a.get("publishedAt"),
        }
        for a in data.get("articles", [])[:MAX_HEADLINES]
    ]


def get_news(product_id: str, query: str) -> list[dict]:
    """Headlines for a product: served from the 1-hour cache when fresh.

    On a cache miss, fetch (real or mock), store, and return. Cache issues never
    block the result.
    """
    cached = _get_cached(product_id)
    if cached is not None:
        return cached

    headlines = _fetch_real(query) if _real_enabled() else _fetch_mock(query)
    _store_cache(product_id, headlines)
    return headlines

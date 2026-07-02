"""
FILE: backend/routers/watchlist.py

WHAT THIS DOES:
The API for the side-panel watchlist. Add or update a watched product, list a
session's items with their latest prices, remove an item, and mark an item as
bought. No login: items are tied to the browser's random session id.

CHANGES THIS SESSION:
- Created add, list, remove, and mark-purchased endpoints with validation and
  plain-language error handling.
- Added a 30/minute per-IP rate limit to the write endpoints (security review).
- Store wait_tolerance_days on add and added POST /{session_id}/refresh, which
  re-checks prices on app open at an adaptive per-item interval (replaces the
  daily cron for the free, no-card deployment).

WHERE IT FITS:
Sits on top of db/watchlist.py. Mounted by main.py. Backs the watchlist panel in
the frontend.

CALLED BY / IMPORTS FROM:
Imports the watchlist db helpers. Mounted by main.py.
"""
import math
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from db import watchlist as wl
from db.price_snapshots import add_snapshot, get_snapshots
from limiter import limiter
from services.apify_client import fetch_prices
from services.serpapi_client import fetch_shopping_prices

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])

_FRIENDLY_ERROR = {
    "error": "watchlist_unavailable",
    "message": "We could not reach your watchlist just now. Please try again in "
    "a moment.",
}

# Cap external price fetches per refresh call, so a session with very many items
# cannot drain the SerpAPI quota or make one request run for a long time.
_MAX_REFETCH_PER_CALL = 25


def _valid_session(session_id: str) -> bool:
    """Cheap format guard for the session id path param (defense in depth)."""
    return 8 <= len(session_id) <= 100


def _interval_days(wait_days: int) -> float:
    """Days to wait between price re-checks for a given wait window.

    Number of checks over the window scales with its length (roughly the square
    root), so a 1 week window gets about 3 checks, 1 month about 5, 1 year about
    19. The interval is the window divided by that count, and never below a day.
    """
    checks = max(1, round(math.sqrt(wait_days)))
    return max(1.0, wait_days / checks)


def _last_checked(product_id: str) -> datetime | None:
    """When this product's price was last recorded, or None if never."""
    latest = get_snapshots(product_id, limit=1)
    if not latest:
        return None
    stamp = latest[0].get("recorded_at")
    if not stamp:
        return None
    try:
        return datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    except ValueError:
        return None


class WatchlistAddRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=100)
    product_id: str = Field(min_length=8, max_length=100)
    target_price: float | None = Field(default=None, gt=0)
    wait_tolerance_days: int | None = Field(default=None, ge=1, le=365)


@router.post("")
@limiter.limit("30/minute")
def add_item(req: WatchlistAddRequest, request: Request):
    """Add a product to the watchlist, or update its target price."""
    try:
        item = wl.add_or_update_item(
            req.session_id,
            req.product_id,
            req.target_price,
            req.wait_tolerance_days,
        )
        return {"ok": True, "item": item}
    except Exception:
        return _FRIENDLY_ERROR


@router.post("/{session_id}/refresh")
@limiter.limit("30/minute")
def refresh(session_id: str, request: Request):
    """Re-check prices for items whose adaptive interval has elapsed.

    Called when the user opens the app. Each item is re-checked at most once per
    its interval, so opening the app many times a day triggers at most one check
    per due item. Replaces the old daily cron for the no-card deployment.
    """
    if not _valid_session(session_id):
        return {"ok": True, "items": []}
    try:
        now = datetime.now(timezone.utc)
        refetched = 0
        for item in wl.get_active_for_session(session_id):
            name = item.get("name")
            if not name:
                continue
            wait_days = item.get("wait_tolerance_days") or 30
            last = _last_checked(item["product_id"])
            if last is not None and now - last < timedelta(
                days=_interval_days(wait_days)
            ):
                continue  # checked recently enough; skip
            if refetched >= _MAX_REFETCH_PER_CALL:
                break  # cap external fetches per call (quota / time guard)
            refetched += 1

            rows = fetch_prices(name) + fetch_shopping_prices(name)
            if not rows:
                continue
            for r in rows:
                add_snapshot(
                    item["product_id"], r["platform"], r["price"], r.get("mrp")
                )
            best = min(float(r["price"]) for r in rows)
            target = item.get("target_price")
            if target is not None and best <= float(target) and not item["notified"]:
                wl.mark_notified(item["id"])

        return {"ok": True, "items": wl.list_for_session(session_id)}
    except Exception:
        return _FRIENDLY_ERROR


@router.get("/{session_id}")
def list_items(session_id: str):
    """List everything a session is watching, with each item's latest price."""
    if not _valid_session(session_id):
        return {"ok": True, "items": []}
    try:
        return {"ok": True, "items": wl.list_for_session(session_id)}
    except Exception:
        return _FRIENDLY_ERROR


@router.delete("/{session_id}/{product_id}")
@limiter.limit("30/minute")
def remove_item(session_id: str, product_id: str, request: Request):
    """Remove one product from a session's watchlist."""
    if not _valid_session(session_id):
        return _FRIENDLY_ERROR
    try:
        wl.remove_item(session_id, product_id)
        return {"ok": True}
    except Exception:
        return _FRIENDLY_ERROR


@router.post("/{session_id}/{product_id}/purchased")
@limiter.limit("30/minute")
def mark_purchased(session_id: str, product_id: str, request: Request):
    """Mark a watched product as bought."""
    if not _valid_session(session_id):
        return _FRIENDLY_ERROR
    try:
        item = wl.mark_purchased(session_id, product_id)
        if item is None:
            return {
                "error": "not_found",
                "message": "That item is not on your watchlist.",
            }
        return {"ok": True, "item": item}
    except Exception:
        return _FRIENDLY_ERROR

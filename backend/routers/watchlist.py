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

WHERE IT FITS:
Sits on top of db/watchlist.py. Mounted by main.py. Backs the watchlist panel in
the frontend.

CALLED BY / IMPORTS FROM:
Imports the watchlist db helpers. Mounted by main.py.
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from db import watchlist as wl
from limiter import limiter

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])

_FRIENDLY_ERROR = {
    "error": "watchlist_unavailable",
    "message": "We could not reach your watchlist just now. Please try again in "
    "a moment.",
}


class WatchlistAddRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=100)
    product_id: str = Field(min_length=8, max_length=100)
    target_price: float | None = Field(default=None, gt=0)


@router.post("")
@limiter.limit("30/minute")
def add_item(req: WatchlistAddRequest, request: Request):
    """Add a product to the watchlist, or update its target price."""
    try:
        item = wl.add_or_update_item(
            req.session_id, req.product_id, req.target_price
        )
        return {"ok": True, "item": item}
    except Exception:
        return _FRIENDLY_ERROR


@router.get("/{session_id}")
def list_items(session_id: str):
    """List everything a session is watching, with each item's latest price."""
    try:
        return {"ok": True, "items": wl.list_for_session(session_id)}
    except Exception:
        return _FRIENDLY_ERROR


@router.delete("/{session_id}/{product_id}")
@limiter.limit("30/minute")
def remove_item(session_id: str, product_id: str, request: Request):
    """Remove one product from a session's watchlist."""
    try:
        wl.remove_item(session_id, product_id)
        return {"ok": True}
    except Exception:
        return _FRIENDLY_ERROR


@router.post("/{session_id}/{product_id}/purchased")
@limiter.limit("30/minute")
def mark_purchased(session_id: str, product_id: str, request: Request):
    """Mark a watched product as bought."""
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

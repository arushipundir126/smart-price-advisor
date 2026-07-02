"""
FILE: backend/db/watchlist.py

WHAT THIS DOES:
Read and write helpers for the watchlist_items table. Watchlists are tied to a
browser session id (no login in v1). Handles add/update, listing with each
item's latest price, removing an item, marking an item as bought, and marking
a drop as already notified.

CHANGES THIS SESSION:
- Added add_or_update_item(), list_for_session(), remove_item(),
  mark_purchased(), and mark_notified().
- Store wait_tolerance_days per item and expose it plus last_checked, and added
  get_active_for_session() so the on-open refresh can pace re-checks per item.
- Made the wait_tolerance_days column optional: add and list now work even if
  that column was never added to the database, so the watchlist never fails.

WHERE IT FITS:
Sits on top of db/supabase_client.py and reuses db/price_snapshots for the
latest price. Called by the watchlist router and the scheduled price checks.

CALLED BY / IMPORTS FROM:
Imports get_client from db/supabase_client and get_snapshots from
db/price_snapshots. Called by routers/watchlist.py.
"""
from datetime import datetime, timezone
from typing import Optional

from db.price_snapshots import get_snapshots
from db.supabase_client import get_client

# Columns we read back, including the embedded product name/brand/category.
# Named explicitly, never SELECT * (security rule). wait_tolerance_days is left
# out here so listing works even if that (optional) column was never added.
_COLUMNS = (
    "id, session_id, product_id, target_price, notified, purchased, "
    "purchased_at, created_at, products(name, brand, category)"
)


def add_or_update_item(
    session_id: str,
    product_id: str,
    target_price: Optional[float] = None,
    wait_tolerance_days: Optional[int] = None,
) -> dict:
    """Add a product to a session's watchlist, or update its target price.

    Stores the wait window when the column exists so re-checks can be paced to it.
    If that optional column was never added, we still add the item (without the
    window) rather than fail. Uses the unique (session_id, product_id) constraint
    so re-adding the same product updates the existing row.
    """
    client = get_client()
    base = {
        "session_id": session_id,
        "product_id": product_id,
        "target_price": target_price,
    }
    try:
        result = (
            client.table("watchlist_items")
            .upsert({**base, "wait_tolerance_days": wait_tolerance_days},
                    on_conflict="session_id,product_id")
            .execute()
        )
    except Exception:
        # Column not present: add without the wait window so the watchlist works.
        result = (
            client.table("watchlist_items")
            .upsert(base, on_conflict="session_id,product_id")
            .execute()
        )
    return result.data[0]


def get_active_for_session(session_id: str) -> list[dict]:
    """Not-yet-bought items for one session, with product name and wait window.

    Used by the on-open refresh to decide which items are due for a re-check. The
    wait window is read only if that optional column exists; otherwise it is None
    and the refresh falls back to a default cadence.
    """
    client = get_client()

    def _query(columns: str):
        return (
            client.table("watchlist_items")
            .select(columns)
            .eq("session_id", session_id)
            .eq("purchased", False)
            .execute()
        )

    try:
        result = _query(
            "id, product_id, target_price, notified, wait_tolerance_days, products(name)"
        )
    except Exception:
        result = _query("id, product_id, target_price, notified, products(name)")

    return [
        {
            "id": r["id"],
            "product_id": r["product_id"],
            "target_price": r["target_price"],
            "notified": r["notified"],
            "wait_tolerance_days": r.get("wait_tolerance_days"),
            "name": (r.get("products") or {}).get("name"),
        }
        for r in result.data
    ]


def list_for_session(session_id: str) -> list[dict]:
    """Everything a session is watching, each with its latest known price."""
    client = get_client()
    result = (
        client.table("watchlist_items")
        .select(_COLUMNS)
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .execute()
    )

    items = []
    for row in result.data:
        latest = get_snapshots(row["product_id"], limit=1)
        latest_price = float(latest[0]["price"]) if latest else None
        latest_platform = latest[0]["platform"] if latest else None
        last_checked = latest[0]["recorded_at"] if latest else None
        product = row.get("products") or {}
        items.append(
            {
                "id": row["id"],
                "product_id": row["product_id"],
                "name": product.get("name"),
                "category": product.get("category"),
                "target_price": row["target_price"],
                "notified": row["notified"],
                "purchased": row["purchased"],
                "purchased_at": row["purchased_at"],
                "wait_tolerance_days": row.get("wait_tolerance_days"),
                "latest_price": latest_price,
                "latest_platform": latest_platform,
                "last_checked": last_checked,
            }
        )
    return items


def get_all_active() -> list[dict]:
    """Every not-yet-bought watched item across all sessions, with product name.

    Used by the daily cron to refresh prices and flag items that hit their target.
    """
    client = get_client()
    result = (
        client.table("watchlist_items")
        .select("id, product_id, target_price, notified, products(name)")
        .eq("purchased", False)
        .execute()
    )
    return [
        {
            "id": r["id"],
            "product_id": r["product_id"],
            "target_price": r["target_price"],
            "notified": r["notified"],
            "name": (r.get("products") or {}).get("name"),
        }
        for r in result.data
    ]


def remove_item(session_id: str, product_id: str) -> None:
    """Remove one product from a session's watchlist."""
    client = get_client()
    (
        client.table("watchlist_items")
        .delete()
        .eq("session_id", session_id)
        .eq("product_id", product_id)
        .execute()
    )


def mark_purchased(session_id: str, product_id: str) -> Optional[dict]:
    """Mark a watched product as bought, stamping the time. Returns the row."""
    client = get_client()
    result = (
        client.table("watchlist_items")
        .update(
            {
                "purchased": True,
                "purchased_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("session_id", session_id)
        .eq("product_id", product_id)
        .execute()
    )
    return result.data[0] if result.data else None


def mark_notified(item_id: str) -> None:
    """Flag that we have already alerted this drop, so we do not repeat it."""
    client = get_client()
    (
        client.table("watchlist_items")
        .update({"notified": True})
        .eq("id", item_id)
        .execute()
    )

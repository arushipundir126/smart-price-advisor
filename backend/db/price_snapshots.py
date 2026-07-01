"""
FILE: backend/db/price_snapshots.py

WHAT THIS DOES:
Read and write helpers for the price_snapshots table, the app's price history.
Writing is append only: we add a reading, never edit or delete old ones. Reading
gives other code the raw history plus the median (typical price).

CHANGES THIS SESSION:
- Added add_snapshot(), get_snapshots(), and get_median_price() with a pure
  _median() helper.

WHERE IT FITS:
Sits on top of db/supabase_client.py. Feeds Signal 1 (fake-discount, needs the
median) and Signal 3 (price trend, needs the ordered history).

CALLED BY / IMPORTS FROM:
Imports get_client from db/supabase_client. Called by the analyse flow and the
scheduled watchlist price checks.
"""
from statistics import median
from typing import Optional

from db.supabase_client import get_client

# Columns we read back. Named explicitly, never SELECT * (security rule).
_COLUMNS = "id, product_id, platform, price, mrp, currency, recorded_at"


def _median(values: list[float]) -> Optional[float]:
    """Middle value of the list, or None if empty. Pure, no database."""
    if not values:
        return None
    return float(median(values))


def add_snapshot(
    product_id: str,
    platform: str,
    price: float,
    mrp: Optional[float] = None,
    currency: str = "INR",
) -> dict:
    """Append one price reading. This table is never updated or deleted."""
    client = get_client()
    inserted = (
        client.table("price_snapshots")
        .insert(
            {
                "product_id": product_id,
                "platform": platform,
                "price": price,
                "mrp": mrp,
                "currency": currency,
            }
        )
        .execute()
    )
    return inserted.data[0]


def get_snapshots(product_id: str, limit: int = 100) -> list[dict]:
    """Return recent snapshots for a product, newest first (for trend analysis)."""
    client = get_client()
    result = (
        client.table("price_snapshots")
        .select(_COLUMNS)
        .eq("product_id", product_id)
        .order("recorded_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


def get_median_price(product_id: str) -> Optional[float]:
    """Median of all stored prices for a product, or None if we have no history."""
    client = get_client()
    result = (
        client.table("price_snapshots")
        .select("price")
        .eq("product_id", product_id)
        .execute()
    )
    prices = [float(row["price"]) for row in result.data]
    return _median(prices)

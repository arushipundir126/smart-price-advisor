"""
FILE: backend/db/products.py

WHAT THIS DOES:
Read and write helpers for the products table. Two jobs: find-or-create a
product by its normalised name (so we never store the same product twice), and
fetch one product by id.

CHANGES THIS SESSION:
- Added normalise_name(), find_or_create_product(), and get_product().
- Added update_category() so a Gemini-classified category is cached on the row.

WHERE IT FITS:
Sits on top of db/supabase_client.py. Used by the analyse flow to resolve a
search query into a stored product row, and by the watchlist and price-history
code to look products up.

CALLED BY / IMPORTS FROM:
Imports get_client from db/supabase_client. Called by the analyse router and
the price-snapshot / watchlist helpers.
"""
import re
from typing import Optional

from db.supabase_client import get_client

# Columns we read back. Named explicitly, never SELECT * (security rule).
_COLUMNS = "id, name, brand, category, asin, flipkart_pid, created_at"


def normalise_name(name: str) -> str:
    """Lowercase, trim, and collapse inner whitespace so equal products match.

    Example: "  Samsung  Galaxy S24 " -> "samsung galaxy s24".
    """
    return re.sub(r"\s+", " ", name).strip().lower()


def find_or_create_product(
    name: str,
    brand: Optional[str] = None,
    category: Optional[str] = None,
    asin: Optional[str] = None,
    flipkart_pid: Optional[str] = None,
) -> dict:
    """Return the existing product row for this name, or create and return it."""
    client = get_client()
    normalised = normalise_name(name)

    existing = (
        client.table("products")
        .select(_COLUMNS)
        .eq("name", normalised)
        .limit(1)
        .execute()
    )
    if existing.data:
        return existing.data[0]

    inserted = (
        client.table("products")
        .insert(
            {
                "name": normalised,
                "brand": brand,
                "category": category,
                "asin": asin,
                "flipkart_pid": flipkart_pid,
            }
        )
        .execute()
    )
    return inserted.data[0]


def update_category(product_id: str, category: str) -> None:
    """Save a classified category on the product so we never classify it again."""
    client = get_client()
    (
        client.table("products")
        .update({"category": category})
        .eq("id", product_id)
        .execute()
    )


def get_recent_products(limit: int = 10) -> list[dict]:
    """Most recently added products, newest first. Used by the daily refresh to
    keep building price history for what people actually search."""
    client = get_client()
    result = (
        client.table("products")
        .select("id, name")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


def get_product(product_id: str) -> Optional[dict]:
    """Fetch one product by id, or None if it does not exist."""
    client = get_client()
    result = (
        client.table("products")
        .select(_COLUMNS)
        .eq("id", product_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None

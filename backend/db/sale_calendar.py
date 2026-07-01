"""
FILE: backend/db/sale_calendar.py

WHAT THIS DOES:
Reads the sale_calendar table and works out which sales matter for a product.
Considers every sale type: category-specific sales (matched by tags), general
all-category events (empty tags, e.g. Republic Day), and sales that are live
right now, not only future ones. Returns each with its bank offers.

CHANGES THIS SESSION:
- Added _annotate_sales() (pure), get_relevant_sales(), and get_next_sale().

WHERE IT FITS:
Sits on top of db/supabase_client.py. Feeds Signal 4 (days-to-next-sale), which
is weighted heavily because a known sale date is a fact, not a guess. The bank
offers it returns feed the stackable-discounts part of the verdict.

CALLED BY / IMPORTS FROM:
Imports get_client from db/supabase_client. Called by the days_to_sale signal.
"""
from datetime import date
from typing import Optional

from db.supabase_client import get_client

# Columns we read back. Named explicitly, never SELECT * (security rule).
_COLUMNS = "id, sale_name, platform, category_tags, start_date, end_date, bank_offers"


def _parse_date(value) -> date:
    """Accept a date or an ISO date string and return a date."""
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _annotate_sales(
    rows: list[dict], category: Optional[str], on_date: date
) -> list[dict]:
    """Filter to sales relevant on on_date for this category, and annotate them.

    A sale is relevant when it has not ended yet (end_date >= on_date) AND it
    either has no category tags (applies to everything) or lists this category.
    Each returned row gains days_until_start (0 if already live) and is_live.
    Sorted soonest first. Pure function, no database.
    """
    relevant = []
    for row in rows:
        start = _parse_date(row["start_date"])
        end = _parse_date(row["end_date"])
        if end < on_date:
            continue  # already over

        tags = row.get("category_tags") or []
        applies_to_all = len(tags) == 0
        matches_category = category is not None and category in tags
        if not (applies_to_all or matches_category):
            continue

        is_live = start <= on_date <= end
        days_until_start = max((start - on_date).days, 0)
        relevant.append(
            {**row, "is_live": is_live, "days_until_start": days_until_start}
        )

    relevant.sort(key=lambda r: (not r["is_live"], r["days_until_start"]))
    return relevant


def get_relevant_sales(
    category: Optional[str] = None, on_date: Optional[date] = None
) -> list[dict]:
    """All sales that are live or upcoming for this category, soonest first."""
    on_date = on_date or date.today()
    client = get_client()
    result = (
        client.table("sale_calendar")
        .select(_COLUMNS)
        .gte("end_date", on_date.isoformat())
        .execute()
    )
    return _annotate_sales(result.data, category, on_date)


def get_next_sale(
    category: Optional[str] = None, on_date: Optional[date] = None
) -> Optional[dict]:
    """The single most relevant sale (live now or soonest), or None."""
    sales = get_relevant_sales(category, on_date)
    return sales[0] if sales else None

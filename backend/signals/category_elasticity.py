"""
FILE: backend/signals/category_elasticity.py

WHAT THIS DOES:
Signal 5. Loads the category rule table and votes based on how much a category
actually moves in sales. Categories that move (electronics, fashion) get a mild
wait lean; categories that barely move (staples, fuel, books) vote buy_now
firmly, so the app never advises waiting for a sale on salt. Unknown category
abstains. Also exposes get_entry() so Signal 4 knows if a category is worth
waiting for.

CHANGES THIS SESSION:
- Added cached table loader, get_entry(), and evaluate().

WHERE IT FITS:
Fifth of the six signals. Reads data/category_elasticity.json. get_entry() is
also used by routers/analyse to inform days_to_sale (Signal 4).

CALLED BY / IMPORTS FROM:
Reads the JSON table from disk (cached). Called by routers/analyse.
"""
import json
import os
from functools import lru_cache
from typing import Optional

SIGNAL_NAME = "category_elasticity"

_TABLE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "category_elasticity.json"
)


@lru_cache(maxsize=1)
def _load_table() -> dict[str, dict]:
    """Load the rule table once, keyed by category name."""
    with open(_TABLE_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return {row["category"]: row for row in data.get("categories", [])}


def get_entry(category: Optional[str]) -> Optional[dict]:
    """Return the rule row for a category, or None if unknown."""
    if not category:
        return None
    return _load_table().get(category.strip().lower())


def evaluate(category: Optional[str]) -> dict:
    """Vote based on whether this category moves enough in sales to wait."""
    entry = get_entry(category)
    if entry is None:
        return {
            "signal_name": SIGNAL_NAME,
            "vote": None,
            "weight": 0,
            "reason": "We do not have sale-behaviour data for this category.",
        }

    low, high = entry["typical_sale_drop_pct"]
    if entry["worth_waiting"]:
        return {
            "signal_name": SIGNAL_NAME,
            "vote": "wait",
            "weight": 0.8,
            "reason": f"This category typically drops about {low} to {high}% in "
            f"sales, so waiting can pay off.",
        }
    return {
        "signal_name": SIGNAL_NAME,
        "vote": "buy_now",
        "weight": 1.5,
        "reason": f"This category barely moves in sales (about {low} to {high}%), "
        f"so waiting is unlikely to help.",
    }

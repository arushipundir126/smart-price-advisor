"""
FILE: backend/signals/days_to_sale.py

WHAT THIS DOES:
Signal 4, weighted heavily. Uses the sale-calendar result to decide if a known
sale is worth waiting for. A live sale votes buy_now (buy during it). A sale
starting within the user's wait window, for a category that moves in sales, votes
wait and attaches that sale's bank offers as stackable discounts. A sale beyond
the wait window votes a weak buy_now. No sale, or a category that does not move,
abstains.

CHANGES THIS SESSION:
- Added evaluate() with live / within-window / beyond-window / abstain branches,
  and _offers_to_discounts() to expose bank offers.

WHERE IT FITS:
Fourth of the six signals. Consumes db/sale_calendar.get_next_sale and the
category elasticity's worth_waiting flag.

CALLED BY / IMPORTS FROM:
Pure Python, no imports. Called by routers/analyse with the next sale resolved.
"""
from typing import Optional

SIGNAL_NAME = "days_to_next_sale"


def _abstain(reason: str) -> dict:
    return {
        "signal_name": SIGNAL_NAME,
        "vote": None,
        "weight": 0,
        "reason": reason,
        "wait_days": None,
        "stackable_discounts": [],
    }


def _offers_to_discounts(bank_offers) -> list[dict]:
    """Turn stored bank_offers JSON into stackable-discount entries."""
    discounts = []
    for offer in bank_offers or []:
        bank = offer.get("bank", "Bank")
        card = offer.get("card_type", "card")
        pct = offer.get("discount_pct")
        cap = offer.get("cap_inr")
        desc = f"{pct}% off with {bank} {card}" if pct else f"{bank} {card} offer"
        if cap:
            desc += f", up to Rs {cap}"
        discounts.append(
            {
                "type": "bank_offer",
                "description": desc,
                "estimated_saving_inr": cap if cap else 0,
            }
        )
    return discounts


def evaluate(
    next_sale: Optional[dict],
    wait_tolerance_days: int,
    worth_waiting: bool = True,
) -> dict:
    """Vote on whether an upcoming or live sale should change the timing."""
    if next_sale is None:
        return _abstain("No known sale is coming up for this category.")
    if not worth_waiting:
        return _abstain(
            "Prices in this category barely move during sales, so a sale date "
            "does not change the advice."
        )

    name = next_sale.get("sale_name", "A sale")
    platform = next_sale.get("platform", "")
    offers = _offers_to_discounts(next_sale.get("bank_offers"))

    if next_sale.get("is_live"):
        return {
            "signal_name": SIGNAL_NAME,
            "vote": "buy_now",
            "weight": 2.0,
            "reason": f"{name} is live now on {platform}, so the sale price is "
            f"already available.",
            "wait_days": 0,
            "stackable_discounts": offers,
        }

    days = next_sale.get("days_until_start", 0)
    if days <= wait_tolerance_days:
        weight = 2.5 if days <= 7 else 2.0 if days <= 30 else 1.5
        return {
            "signal_name": SIGNAL_NAME,
            "vote": "wait",
            "weight": weight,
            "reason": f"{name} starts in about {days} days on {platform}, when "
            f"prices in this category usually drop.",
            "wait_days": days,
            "stackable_discounts": offers,
        }

    return {
        "signal_name": SIGNAL_NAME,
        "vote": "buy_now",
        "weight": 0.8,
        "reason": f"The next sale ({name}) is about {days} days away, beyond how "
        f"long you want to wait, so buying now is reasonable.",
        "wait_days": days,
        "stackable_discounts": offers,
    }

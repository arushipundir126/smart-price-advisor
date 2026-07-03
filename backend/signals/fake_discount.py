"""
FILE: backend/signals/fake_discount.py

WHAT THIS DOES:
Signal 1. Judges whether today's best price is a genuine deal or a fake one by
comparing it to the product's own stored median (typical) price, to the real
MRP (the strikethrough "was" price from shopping results), and to Google's own
deal badge (LOW PRICE / PRICE DROP). A price clearly below its usual level or
deep below MRP votes buy_now. A price at or above its usual level, dressed up
as a big discount off an inflated MRP, votes wait. With no evidence at all it
abstains rather than guess.

CHANGES THIS SESSION:
- Added evaluate() with genuine/fake logic, weight scaling, and abstain paths.
- Now uses the real MRP and Google's deal tag: votes even without price history
  when the MRP discount is deep or Google flags a low price, and strengthens
  the vote when several kinds of evidence agree.

WHERE IT FITS:
First of the six signals. Uses prices from services/apify_client and
services/serpapi_client, and the median from db/price_snapshots. Its
price_vs_median value fills that field on the verdict.

CALLED BY / IMPORTS FROM:
Pure Python, no imports. Called by routers/analyse with data already fetched.
"""
from typing import Optional

SIGNAL_NAME = "fake_discount"

# How far below median counts as a genuine deal, and how far above counts as
# "not a good time", both in percent.
GENUINE_BELOW_PCT = -3.0
ABOVE_TYPICAL_PCT = 2.0
# An MRP discount at least this deep counts as a real deal on its own.
DEEP_MRP_DISCOUNT_PCT = 15.0
MAX_WEIGHT = 2.0

# Google badge values that mean "this price is good right now".
_GOOD_TAGS = ("LOW PRICE", "PRICE DROP")


def _abstain(reason: str) -> dict:
    return {
        "signal_name": SIGNAL_NAME,
        "vote": None,
        "weight": 0,
        "reason": reason,
        "price_vs_median": None,
        "best_price": None,
    }


def _mrp_for(rows: list[dict], best_price: float) -> Optional[float]:
    """Best available MRP for this product: the highest valid 'was' price seen.

    Sellers list slightly different MRPs; the highest one above the current
    best price is the most honest ceiling to measure a discount against.
    """
    mrps = [float(r["mrp"]) for r in rows if r.get("mrp")]
    mrps = [m for m in mrps if m > best_price]
    return max(mrps) if mrps else None


def _has_deal_tag(rows: list[dict]) -> bool:
    """True if Google flagged any listing of this product as a low price."""
    for r in rows:
        tag = (r.get("deal_tag") or "").upper()
        if any(good in tag for good in _GOOD_TAGS):
            return True
    return False


def evaluate(price_rows: list[dict], median: Optional[float]) -> dict:
    """Vote on whether the current best price is a real deal.

    price_rows: list of {price, mrp, deal_tag, platform, ...} from the sources.
    median: the product's stored median price, or None if we have no history.
    """
    if not price_rows:
        return _abstain("No live price was available to judge.")

    best = min(price_rows, key=lambda r: r["price"])
    best_price = float(best["price"])
    mrp = _mrp_for(price_rows, best_price)
    google_says_low = _has_deal_tag(price_rows)
    mrp_discount_pct = (
        round((mrp - best_price) / mrp * 100, 1) if mrp else None
    )

    # No history yet: fall back to MRP depth and Google's own badge.
    if median is None or median <= 0:
        if mrp_discount_pct is not None and mrp_discount_pct >= DEEP_MRP_DISCOUNT_PCT:
            reason = f"The price is about {mrp_discount_pct:.0f}% below MRP"
            if google_says_low:
                reason += ", and Google also flags this as a low price"
            return {
                "signal_name": SIGNAL_NAME,
                "vote": "buy_now",
                "weight": 1.4 if google_says_low else 1.1,
                "reason": reason + ", so this looks like a genuine deal.",
                "price_vs_median": None,
                "best_price": best_price,
            }
        if google_says_low:
            return {
                "signal_name": SIGNAL_NAME,
                "vote": "buy_now",
                "weight": 1.0,
                "reason": "Google's own price tracker flags this as a low price right now.",
                "price_vs_median": None,
                "best_price": best_price,
            }
        return _abstain(
            "This is the first time we have seen this product, so there is no "
            "price history to compare against yet."
        )

    pct_vs_median = round((best_price - median) / median * 100, 1)

    if pct_vs_median <= GENUINE_BELOW_PCT:
        weight = min(MAX_WEIGHT, 1.0 + abs(pct_vs_median) / 10)
        reason = (
            f"The best price is about {abs(pct_vs_median):.0f}% below its usual "
            f"level"
        )
        if mrp_discount_pct is not None and mrp_discount_pct >= DEEP_MRP_DISCOUNT_PCT:
            reason += f" and {mrp_discount_pct:.0f}% below MRP"
            weight = min(MAX_WEIGHT, weight + 0.3)
        if google_says_low:
            reason += ", and Google also flags it as a low price"
            weight = min(MAX_WEIGHT, weight + 0.3)
        reason += ", so this is a genuine deal."
        vote = "buy_now"
    elif pct_vs_median >= ABOVE_TYPICAL_PCT:
        weight = min(MAX_WEIGHT, 1.0 + pct_vs_median / 10)
        if mrp and best_price < float(mrp):
            reason = (
                f"The price is about {pct_vs_median:.0f}% above its usual level. "
                f"The discount off MRP looks bigger than the real saving."
            )
        else:
            reason = (
                f"The price is about {pct_vs_median:.0f}% above its usual level, "
                f"so this is not a good time."
            )
        vote = "wait"
    else:
        weight = 0.8
        reason = "The price is about its usual level, neither high nor low."
        if google_says_low:
            reason = (
                "The price is near its usual level, but Google flags it as a "
                "low price, so it leans towards a fair buy."
            )
            weight = 1.0
        vote = "buy_now"

    return {
        "signal_name": SIGNAL_NAME,
        "vote": vote,
        "weight": round(weight, 3),
        "reason": reason,
        "price_vs_median": pct_vs_median,
        "best_price": best_price,
    }

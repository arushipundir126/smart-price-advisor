"""
FILE: backend/signals/fake_discount.py

WHAT THIS DOES:
Signal 1. Judges whether today's best price is a genuine deal or a fake one by
comparing it to the product's own stored median (typical) price, and to MRP.
A price clearly below the median votes buy_now. A price at or above its usual
level, especially when dressed up as a big discount off an inflated MRP, votes
wait. With no price history yet, it abstains rather than guess.

CHANGES THIS SESSION:
- Added evaluate() with genuine/fake logic, weight scaling, and abstain paths.

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
MAX_WEIGHT = 2.0


def _abstain(reason: str) -> dict:
    return {
        "signal_name": SIGNAL_NAME,
        "vote": None,
        "weight": 0,
        "reason": reason,
        "price_vs_median": None,
        "best_price": None,
    }


def evaluate(price_rows: list[dict], median: Optional[float]) -> dict:
    """Vote on whether the current best price is a real deal.

    price_rows: list of {price, mrp, platform, ...} from the price sources.
    median: the product's stored median price, or None if we have no history.
    """
    if not price_rows:
        return _abstain("No live price was available to judge.")
    if median is None or median <= 0:
        return _abstain(
            "This is the first time we have seen this product, so there is no "
            "price history to compare against yet."
        )

    best = min(price_rows, key=lambda r: r["price"])
    best_price = float(best["price"])
    pct_vs_median = round((best_price - median) / median * 100, 1)

    if pct_vs_median <= GENUINE_BELOW_PCT:
        weight = min(MAX_WEIGHT, 1.0 + abs(pct_vs_median) / 10)
        reason = (
            f"The best price is about {abs(pct_vs_median):.0f}% below its usual "
            f"level, so this is a genuine deal."
        )
        vote = "buy_now"
    elif pct_vs_median >= ABOVE_TYPICAL_PCT:
        weight = min(MAX_WEIGHT, 1.0 + pct_vs_median / 10)
        mrp = best.get("mrp")
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
        vote = "buy_now"

    return {
        "signal_name": SIGNAL_NAME,
        "vote": vote,
        "weight": round(weight, 3),
        "reason": reason,
        "price_vs_median": pct_vs_median,
        "best_price": best_price,
    }

"""
FILE: backend/signals/price_trend.py

WHAT THIS DOES:
Signal 3. Reads the product's stored price history and measures direction (is the
price drifting down or up) and volatility (how much it swings). A falling price
votes wait, a rising price votes buy_now, and wide swings lean slightly to wait
because a low point may appear. With fewer than two history points, it abstains.

CHANGES THIS SESSION:
- Added evaluate() plus a pure _trend() helper computing direction and swing.

WHERE IT FITS:
Third of the six signals. Consumes snapshots from db/price_snapshots.get_snapshots
(newest first) and turns them into a timing vote.

CALLED BY / IMPORTS FROM:
Pure Python, no imports. Called by routers/analyse with history already fetched.
"""
SIGNAL_NAME = "price_trend"

# Percent change between the older and recent halves that counts as a real move.
MOVE_PCT = 2.0
# Swing (range over average, percent) above which we call the price volatile.
VOLATILE_PCT = 10.0
MAX_WEIGHT = 1.8


def _abstain(reason: str) -> dict:
    return {"signal_name": SIGNAL_NAME, "vote": None, "weight": 0, "reason": reason}


def _trend(prices_chrono: list[float]) -> tuple[float, float]:
    """Return (pct_change_recent_vs_older, volatility_pct). Pure, no database."""
    n = len(prices_chrono)
    mid = max(1, n // 2)
    older = prices_chrono[:mid]
    recent = prices_chrono[mid:] or older
    older_avg = sum(older) / len(older)
    recent_avg = sum(recent) / len(recent)
    pct_change = (recent_avg - older_avg) / older_avg * 100 if older_avg else 0.0

    mean = sum(prices_chrono) / n
    volatility = (max(prices_chrono) - min(prices_chrono)) / mean * 100 if mean else 0.0
    return round(pct_change, 1), round(volatility, 1)


def evaluate(snapshots: list[dict]) -> dict:
    """Vote on timing from the price history (snapshots come newest first)."""
    if not snapshots or len(snapshots) < 2:
        return _abstain(
            "We do not have enough price history yet to spot a trend. We are "
            "tracking this product now."
        )

    # get_snapshots returns newest first; reverse to oldest -> newest.
    prices_chrono = [float(s["price"]) for s in reversed(snapshots)]
    pct_change, volatility = _trend(prices_chrono)

    if pct_change <= -MOVE_PCT:
        weight = min(MAX_WEIGHT, 1.0 + abs(pct_change) / 10)
        return {
            "signal_name": SIGNAL_NAME,
            "vote": "wait",
            "weight": round(weight, 3),
            "reason": f"The price has been falling lately (down about "
            f"{abs(pct_change):.0f}%), so waiting may pay off.",
        }
    if pct_change >= MOVE_PCT:
        weight = min(MAX_WEIGHT, 1.0 + pct_change / 10)
        return {
            "signal_name": SIGNAL_NAME,
            "vote": "buy_now",
            "weight": round(weight, 3),
            "reason": f"The price has been rising lately (up about "
            f"{pct_change:.0f}%), so buying sooner avoids paying more.",
        }
    if volatility >= VOLATILE_PCT:
        return {
            "signal_name": SIGNAL_NAME,
            "vote": "wait",
            "weight": 0.8,
            "reason": "The price swings quite a bit, so a lower point may appear "
            "if you wait.",
        }
    return {
        "signal_name": SIGNAL_NAME,
        "vote": "buy_now",
        "weight": 0.7,
        "reason": "The price has been steady, so waiting is unlikely to help.",
    }

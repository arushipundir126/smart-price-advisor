"""
FILE: backend/signals/aggregator.py

WHAT THIS DOES:
Combines the six signal votes into one verdict and an honest confidence BAND
(High / Medium / Low, never a false-precise percentage). Each signal votes
buy_now or wait with a weight; abstaining signals (vote None or weight 0) are
ignored. The band reflects both how strongly the signals agree and how many
actually voted, so a single signal can never read as High.

CHANGES THIS SESSION:
- Added aggregate_votes() with tie handling and a no-data default.
- Replaced the numeric confidence with a High/Medium/Low band.

WHERE IT FITS:
The core of the analysis engine. Called by services/gemini_client (fallback) and
by routers/analyse to decide the verdict when Gemini is not used.

CALLED BY / IMPORTS FROM:
Pure Python, no imports. Consumes signal dicts produced by the six signal files.
"""
_VALID_VOTES = {"buy_now", "wait"}


def _confidence_band(buy_weight: float, wait_weight: float, participating: int) -> str:
    """Map agreement and signal count to High / Medium / Low.

    High needs strong agreement AND several voting signals. Medium needs moderate
    agreement from at least two. Everything else, including no data or a tie, is
    Low. No percentage is exposed, to avoid false precision.
    """
    total = buy_weight + wait_weight
    if total == 0:
        return "Low"
    share = max(buy_weight, wait_weight) / total
    if participating >= 3 and share >= 0.75:
        return "High"
    if participating >= 2 and share >= 0.60:
        return "Medium"
    return "Low"


def aggregate_votes(signals: list[dict]) -> dict:
    """Reduce signal votes to a verdict and a confidence band.

    A signal participates only when its vote is buy_now or wait and its weight is
    greater than zero. With no participating signals we default to Buy Now at Low
    confidence, because advising a wait needs positive evidence. A tie leans Buy
    Now.
    """
    buy_weight = 0.0
    wait_weight = 0.0
    participating = 0

    for s in signals:
        vote = s.get("vote")
        weight = s.get("weight", 0) or 0
        if vote not in _VALID_VOTES or weight <= 0:
            continue  # abstain
        participating += 1
        if vote == "buy_now":
            buy_weight += weight
        else:
            wait_weight += weight

    total = buy_weight + wait_weight
    if total == 0:
        return {
            "verdict": "Buy Now",
            "confidence": "Low",
            "buy_weight": 0.0,
            "wait_weight": 0.0,
            "participating": 0,
        }

    verdict = "Buy Now" if buy_weight >= wait_weight else "Wait"  # tie leans Buy Now
    confidence = _confidence_band(buy_weight, wait_weight, participating)

    return {
        "verdict": verdict,
        "confidence": confidence,
        "buy_weight": round(buy_weight, 3),
        "wait_weight": round(wait_weight, 3),
        "participating": participating,
    }

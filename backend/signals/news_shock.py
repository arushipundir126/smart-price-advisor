"""
FILE: backend/signals/news_shock.py

WHAT THIS DOES:
Signal 6. Scans recent headlines for words that hint at a price shock history
cannot foresee. Wait shocks (successor launch, price cut, oversupply) vote wait.
Buy-now shocks (shortage, import ban, price hike, discontinued) vote buy_now. If
both kinds or none appear, it abstains. Deliberately simple keyword matching;
Gemini refines this from the same headlines in real mode.

CHANGES THIS SESSION:
- Added evaluate() with wait/buy keyword sets and both/none abstain handling.

WHERE IT FITS:
Sixth of the six signals. Consumes headlines from services/newsapi_client (or
data.gov feeds for grocery/fuel).

CALLED BY / IMPORTS FROM:
Pure Python, no imports. Called by routers/analyse with headlines already fetched.
"""
SIGNAL_NAME = "news_shock"

# Words suggesting the price is likely to FALL soon, so waiting helps.
_WAIT_KEYWORDS = [
    "successor",
    "next model",
    "new model",
    "price cut",
    "price drop",
    "slashed",
    "cheaper",
    "oversupply",
    "glut",
    "sale begins",
]

# Words suggesting the price is likely to RISE soon, so buying now helps.
_BUY_KEYWORDS = [
    "shortage",
    "import ban",
    "tariff",
    "price hike",
    "hike",
    "surge",
    "costlier",
    "discontinued",
    "supply crunch",
    "out of stock",
]


def evaluate(headlines: list[dict]) -> dict:
    """Vote from recent headlines. Abstain when the signal is mixed or absent."""
    if not headlines:
        return {
            "signal_name": SIGNAL_NAME,
            "vote": None,
            "weight": 0,
            "reason": "No recent news that affects the price.",
        }

    text = " ".join(
        f"{h.get('title', '')} {h.get('description', '')}" for h in headlines
    ).lower()

    wait_hits = [kw for kw in _WAIT_KEYWORDS if kw in text]
    buy_hits = [kw for kw in _BUY_KEYWORDS if kw in text]

    if wait_hits and not buy_hits:
        return {
            "signal_name": SIGNAL_NAME,
            "vote": "wait",
            "weight": 1.2,
            "reason": f"Recent news ({wait_hits[0]}) suggests the price may fall "
            f"soon, so waiting could help.",
        }
    if buy_hits and not wait_hits:
        return {
            "signal_name": SIGNAL_NAME,
            "vote": "buy_now",
            "weight": 1.2,
            "reason": f"Recent news ({buy_hits[0]}) suggests the price may rise "
            f"soon, so buying now avoids paying more.",
        }
    if wait_hits and buy_hits:
        return {
            "signal_name": SIGNAL_NAME,
            "vote": None,
            "weight": 0,
            "reason": "Recent news points both ways, so it does not tip the "
            "decision.",
        }
    return {
        "signal_name": SIGNAL_NAME,
        "vote": None,
        "weight": 0,
        "reason": "No recent news that clearly affects the price.",
    }

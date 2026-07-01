"""
FILE: backend/signals/cross_platform.py

WHAT THIS DOES:
Signal 2. Scans every marketplace price we fetched and picks the cheapest place
to buy right now, with its direct link. Votes a modest buy_now, because the
saving is available today by choosing the right platform, no waiting needed. Its
main job is to supply best_price, best_platform and buy_link for the verdict.

CHANGES THIS SESSION:
- Added evaluate() returning the cheapest source, spread, and a weak buy vote.

WHERE IT FITS:
Second of the six signals. Consumes the merged price rows from
services/apify_client and services/serpapi_client.

CALLED BY / IMPORTS FROM:
Pure Python, no imports. Called by routers/analyse with prices already fetched.
"""
SIGNAL_NAME = "cross_platform"

# A price spread wider than this (percent) means switching platform clearly pays.
MEANINGFUL_SPREAD_PCT = 3.0


def _abstain(reason: str) -> dict:
    return {
        "signal_name": SIGNAL_NAME,
        "vote": None,
        "weight": 0,
        "reason": reason,
        "best_price": None,
        "best_platform": None,
        "best_platform_label": None,
        "buy_link": None,
    }


def evaluate(price_rows: list[dict]) -> dict:
    """Find the cheapest platform and vote weakly to buy there now."""
    if not price_rows:
        return _abstain("No live price was available across platforms.")

    best = min(price_rows, key=lambda r: r["price"])
    highest = max(price_rows, key=lambda r: r["price"])
    best_price = float(best["price"])
    label = best.get("platform_label") or best.get("platform")

    result = {
        "signal_name": SIGNAL_NAME,
        "best_price": best_price,
        "best_platform": best.get("platform"),
        "best_platform_label": label,
        "buy_link": best.get("url"),
    }

    if len(price_rows) == 1:
        result.update(
            {
                "vote": "buy_now",
                "weight": 0.6,
                "reason": f"Only {label} had a live price, at Rs {int(best_price)}.",
            }
        )
        return result

    spread_pct = round((float(highest["price"]) - best_price) / best_price * 100, 1)
    if spread_pct >= MEANINGFUL_SPREAD_PCT:
        saving = int(float(highest["price"]) - best_price)
        reason = (
            f"{label} is cheapest at Rs {int(best_price)}, about Rs {saving} less "
            f"than the priciest seller. You can save today by buying there."
        )
    else:
        reason = (
            f"{label} is cheapest at Rs {int(best_price)}; prices are close across "
            f"sellers right now."
        )
    result.update({"vote": "buy_now", "weight": 1.0, "reason": reason})
    return result

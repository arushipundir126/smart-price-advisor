"""
FILE: backend/services/gemini_client.py

WHAT THIS DOES:
Turns the six signal results plus news headlines into the final consumer verdict.
Real mode asks Gemini to reason over the provided evidence only (never its own
stale price memory) and return strict JSON. If Gemini is unavailable or returns
bad JSON, or when no key is set, a deterministic fallback builds the verdict
directly from the signal votes, so the app always produces an answer.

CHANGES THIS SESSION:
- Added SYSTEM_PROMPT, synthesise_verdict(), a real Gemini path, and a
  deterministic fallback that defers to signals/aggregator when available.
- Added classify_category(): one cached Gemini call that maps an unknown
  product to an elasticity category, validated against the real table.

WHERE IT FITS:
Fifth service client and the last step of the analysis engine. Called by the
analyse route after the six signals have voted.

CALLED BY / IMPORTS FROM:
Reads GEMINI_API_KEY from the environment. Imports google.generativeai lazily
(real path only) and signals/aggregator lazily (fallback only). Called by
routers/analyse.py.
"""
import json
import os
from typing import Optional

# System prompt. Plain hyphens only, no em dashes (style rule).
SYSTEM_PROMPT = (
    "You are the analysis engine for Smart Price Advisor, a shopping timing "
    "app for Indian consumers. Reason ONLY over the signal data and headlines "
    "provided in the user message. Do NOT use your own memory of prices, which "
    "is stale. Your verdict must be backed by the signals, never a guess. "
    "Return ONLY valid JSON matching this schema, with no preamble, no markdown, "
    "no explanation:\n"
    '{"verdict": "Buy Now" | "Wait", "confidence": "High" | "Medium" | "Low", '
    '"summary_reason": "one sentence, plain English, no jargon", '
    '"wait_estimate_days": null | number, '
    '"stackable_discounts": [{"type": "bank_offer" | "coupon" | "gift_card", '
    '"description": string, "estimated_saving_inr": number}], '
    '"signal_summaries": [{"signal": string, "vote": "buy_now" | "wait", '
    '"plain_reason": string}]}'
)


def _real_enabled() -> bool:
    """True only when a Gemini key is configured."""
    return bool(os.getenv("GEMINI_API_KEY"))


def _parse_json(text: str) -> Optional[dict]:
    """Parse Gemini output, tolerating stray ```json fences. None on failure."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lstrip().lower().startswith("json"):
            cleaned = cleaned.lstrip()[4:]
    try:
        return json.loads(cleaned)
    except Exception:
        return None


def _tally(signals: list[dict]) -> tuple[str, str]:
    """Stopgap weighted vote used only if signals/aggregator is not importable.

    Returns (verdict, confidence_band). Confidence is High/Medium/Low based on
    how strongly the signals agree.
    """
    buy = sum(s.get("weight", 0) for s in signals if s.get("vote") == "buy_now")
    wait = sum(s.get("weight", 0) for s in signals if s.get("vote") == "wait")
    total = buy + wait
    if total == 0:
        return "Buy Now", "Low"
    share = max(buy, wait) / total
    band = "High" if share >= 0.75 else "Medium" if share >= 0.60 else "Low"
    verdict = "Buy Now" if buy >= wait else "Wait"
    return verdict, band


def _aggregate(signals: list[dict]) -> tuple[str, str]:
    """Prefer the real aggregator; fall back to the local tally if absent."""
    try:
        from signals.aggregator import aggregate_votes

        result = aggregate_votes(signals)
        return result["verdict"], result["confidence"]
    except Exception:
        return _tally(signals)


def _fallback_verdict(
    product: str,
    category: Optional[str],
    signals: list[dict],
    wait_tolerance_days: int,
) -> dict:
    """Deterministic verdict from signal votes, no AI. Always returns valid data."""
    verdict, confidence = _aggregate(signals)

    driver = max(signals, key=lambda s: s.get("weight", 0)) if signals else None
    lead = "Better to wait" if verdict == "Wait" else "Buy now"
    reason = driver["reason"] if driver else "based on the available signals"
    summary_reason = f"{lead}: {reason}"

    # If any signal carries a wait_days hint, use the soonest within tolerance.
    wait_days_hints = [
        s["wait_days"]
        for s in signals
        if s.get("wait_days") is not None
    ]
    wait_estimate_days = None
    if verdict == "Wait" and wait_days_hints:
        wait_estimate_days = min(min(wait_days_hints), wait_tolerance_days)

    signal_summaries = [
        {
            "signal": s.get("signal_name", "signal"),
            "vote": s.get("vote", "wait"),
            "plain_reason": s.get("reason", ""),
        }
        for s in signals
    ]

    # Bank offers / coupons are attached upstream by the days_to_sale signal.
    stackable_discounts = []
    for s in signals:
        for offer in s.get("stackable_discounts", []) or []:
            stackable_discounts.append(offer)

    return {
        "verdict": verdict,
        "confidence": confidence,
        "summary_reason": summary_reason,
        "wait_estimate_days": wait_estimate_days,
        "stackable_discounts": stackable_discounts,
        "signal_summaries": signal_summaries,
    }


def _fetch_real(
    product: str,
    category: Optional[str],
    signals: list[dict],
    headlines: list[dict],
    wait_tolerance_days: int,
) -> Optional[dict]:
    """Ask Gemini for the verdict JSON. None on any failure (caller falls back)."""
    try:
        import google.generativeai as genai

        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel(
            "gemini-2.5-flash", system_instruction=SYSTEM_PROMPT
        )
        user_message = json.dumps(
            {
                "product": product,
                "category": category,
                "signal_results": signals,
                "news_headlines": [h.get("title") for h in headlines],
                "wait_tolerance_days": wait_tolerance_days,
            }
        )
        resp = model.generate_content(user_message)
        return _parse_json(resp.text)
    except Exception:
        return None


def classify_category(product_name: str) -> Optional[str]:
    """Ask Gemini which elasticity category a product belongs to.

    Used only when the keyword guesser fails, and the answer is cached on the
    product row by the caller, so this costs one call per new product ever.
    The reply is validated against the real category list; None on any failure
    or when no key is set, so the caller simply proceeds without a category.
    """
    if not _real_enabled():
        return None
    try:
        import json as _json
        import os as _os

        table_path = _os.path.join(
            _os.path.dirname(_os.path.dirname(__file__)),
            "data",
            "category_elasticity.json",
        )
        with open(table_path) as f:
            table = _json.load(f)
        # The table is {"_comment": ..., "categories": [{"category": name, ...}]}
        # so collect the names from the entry list.
        valid = {e["category"] for e in table.get("categories", [])}
        if not valid:
            return None

        import google.generativeai as genai

        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = (
            "Classify this Indian shopping product into exactly one category "
            f"from this list: {', '.join(sorted(valid))}. "
            f"Product: {product_name}. Reply with only the category name."
        )
        resp = model.generate_content(prompt)
        answer = resp.text.strip().lower().replace(" ", "_")
        return answer if answer in valid else None
    except Exception:
        return None


def synthesise_verdict(
    product: str,
    category: Optional[str],
    signals: list[dict],
    headlines: list[dict],
    wait_tolerance_days: int,
) -> dict:
    """Produce the final verdict dict. Real Gemini when configured, else fallback.

    Even in real mode, a missing or malformed AI response falls back to the
    deterministic verdict, so this never fails to return an answer.
    """
    if _real_enabled():
        real = _fetch_real(
            product, category, signals, headlines, wait_tolerance_days
        )
        if real is not None:
            return real
    return _fallback_verdict(product, category, signals, wait_tolerance_days)

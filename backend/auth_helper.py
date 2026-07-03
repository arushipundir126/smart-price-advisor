"""
FILE: backend/auth_helper.py

WHAT THIS DOES:
Everything auth. One router (POST /api/auth/signup) that validates the email
and password server-side and creates the user via the Supabase admin API with
the email pre-confirmed (no verification mail, per product decision), and one
dependency (require_user_id) that watchlist routes use to turn a Bearer token
into a verified user id.

SECURITY CONTRACT
- Auth required: signup is anonymous (rate limited 5/min/IP); require_user_id
  demands a valid Supabase access token and returns 401 otherwise.
- Input validated: email format (sensible username, dotted domain), password
  at least 8 chars with a letter and a number, both length-capped.
- Watchlist identity: ONLY the verified token user id. Any client-supplied
  session or user id is ignored.
- Sensitive data: passwords, tokens and emails are never logged and never
  echoed back; all failures return one generic plain-language message.

CHANGES THIS SESSION:
- Created signup route, email/password validation, and require_user_id.

WHERE IT FITS:
Mounted by main.py. routers/watchlist.py depends on require_user_id.

CALLED BY / IMPORTS FROM:
Uses db/supabase_client.get_client (service role, backend only) and the shared
limiter. Called by main.py and routers/watchlist.py.
"""
import re
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from db.supabase_client import get_client
from limiter import limiter

router = APIRouter(prefix="/api/auth", tags=["auth"])

# One generic message for every signup failure, so responses never reveal
# whether an email is already registered (no user enumeration).
_GENERIC_SIGNUP_ERROR = {
    "error": "signup_failed",
    "message": "We could not create an account with these details. Check the "
    "email and password, or sign in if you already have an account.",
}

_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9][a-zA-Z0-9._%+-]{0,63}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)


def valid_email(email: str) -> bool:
    """True for a real-looking address: sensible username, dotted domain."""
    email = email.strip()
    if len(email) > 254 or not _EMAIL_RE.match(email):
        return False
    local = email.split("@", 1)[0]
    # The username part must contain at least 2 letters or digits.
    return len(re.sub(r"[^a-zA-Z0-9]", "", local)) >= 2


def valid_password(password: str) -> bool:
    """At least 8 chars with at least one letter and one number."""
    return (
        8 <= len(password) <= 72
        and re.search(r"[a-zA-Z]", password) is not None
        and re.search(r"[0-9]", password) is not None
    )


class SignupRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=72)


@router.post("/signup")
@limiter.limit("5/minute")
def signup(req: SignupRequest, request: Request):
    """Create an account with the email pre-confirmed (no verification mail)."""
    email = req.email.strip().lower()
    if not valid_email(email):
        return {
            "error": "invalid_email",
            "message": "That email address does not look right. Please check it.",
        }
    if not valid_password(req.password):
        return {
            "error": "weak_password",
            "message": "Please use at least 8 characters, with at least one "
            "letter and one number.",
        }
    try:
        client = get_client()
        client.auth.admin.create_user(
            {
                "email": email,
                "password": req.password,
                "email_confirm": True,
            }
        )
        return {"ok": True}
    except Exception:
        # Covers duplicate emails and provider errors alike, on purpose.
        return _GENERIC_SIGNUP_ERROR


def require_user_id(authorization: Optional[str] = Header(default=None)) -> str:
    """FastAPI dependency: turn a Bearer token into a verified user id.

    Raises 401 with a friendly message when the token is missing, malformed,
    expired or forged. The returned id is the only identity watchlist code uses.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Please sign in to use your watchlist."
        )
    token = authorization.removeprefix("Bearer ").strip()
    try:
        user = get_client().auth.get_user(token)
        user_id = user.user.id if user and user.user else None
    except Exception:
        user_id = None
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Your session has expired. Please sign in again.",
        )
    return user_id

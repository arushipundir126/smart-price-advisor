"""
FILE: backend/limiter.py

WHAT THIS DOES:
Holds the single shared rate limiter so both main.py (which registers it) and the
routers (which decorate endpoints with it) use the same instance. Keeping it in
its own file avoids a circular import between main.py and the routers.

CHANGES THIS SESSION:
- Created the shared Limiter keyed by client IP.

WHERE IT FITS:
Imported by main.py to register the limiter and its error handler, and by
routers/analyse.py to enforce 10 requests per minute on the paid endpoint.

CALLED BY / IMPORTS FROM:
Uses slowapi. Imported by main.py and routers/analyse.py.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Keyed by client IP. The /api/analyse route applies "10/minute" to protect the
# paid Apify and Gemini calls (security rule).
limiter = Limiter(key_func=get_remote_address)

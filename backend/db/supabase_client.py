"""
FILE: backend/db/supabase_client.py

WHAT THIS DOES:
The single doorway to the Supabase (PostgreSQL) database. Reads the database
URL and the backend-only service-role key from the environment and builds one
reusable client. Every other db/ file goes through this, nothing else connects
to Supabase directly.

CHANGES THIS SESSION:
- Created a lazy, cached get_client() with a clear error when config is missing.

WHERE IT FITS:
Foundation of the data layer. Imported by db/products.py, db/price_snapshots.py,
db/sale_calendar.py and db/watchlist.py.

CALLED BY / IMPORTS FROM:
Uses the supabase-py library. Reads SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
from backend/.env (loaded via python-dotenv).
"""
import os
from functools import lru_cache

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


@lru_cache(maxsize=1)
def get_client() -> Client:
    """Return a single shared Supabase client, built on first use and reused after.

    The service-role key is used because the backend needs to write price
    snapshots. This key is backend only and must never reach the frontend.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "Supabase is not configured. Add SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY to backend/.env, then restart."
        )
    return create_client(url, key)

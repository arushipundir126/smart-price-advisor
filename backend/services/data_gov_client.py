"""
FILE: backend/services/data_gov_client.py

WHAT THIS DOES:
Reads official daily prices for groceries and fuel from data.gov.in, filtered by
city. These categories do not go on marketplace "sale", so we use government
feeds instead of scrapers. Two modes: real data.gov.in call when DATA_GOV_API_KEY
is set, otherwise built-in mock prices.

CHANGES THIS SESSION:
- Added fetch_commodity_price() with real and mock paths, plus resource-id
  placeholders for the mandi and fuel datasets.

WHERE IT FITS:
Fourth service client. It is the price source for grocery and fuel categories
and supports Signal 6 for those categories (prices barely move, so "wait" is
rarely worth it).

CALLED BY / IMPORTS FROM:
Reads DATA_GOV_API_KEY from the environment. Imports httpx lazily (real path
only). Called by the grocery/fuel branch of the analyse flow.
"""
import os
from datetime import date
from typing import Optional

DATA_GOV_ENDPOINT = "https://api.data.gov.in/resource"
REQUEST_TIMEOUT_SECONDS = 10

# Dataset resource ids on data.gov.in. Fill these in when the exact datasets are
# chosen; until then the client uses mock data.
RESOURCE_IDS = {
    "grocery": None,  # daily mandi / commodity prices
    "fuel": None,     # daily petrol / diesel prices
}

# Mock daily prices by commodity and city. Prices in INR; unit noted per item.
_MOCK_PRICES: dict[str, dict[str, dict]] = {
    "onion": {
        "delhi": {"price": 32, "unit": "per kg"},
        "mumbai": {"price": 38, "unit": "per kg"},
        "bengaluru": {"price": 30, "unit": "per kg"},
    },
    "tomato": {
        "delhi": {"price": 28, "unit": "per kg"},
        "mumbai": {"price": 34, "unit": "per kg"},
    },
    "rice": {
        "delhi": {"price": 52, "unit": "per kg"},
        "mumbai": {"price": 58, "unit": "per kg"},
    },
    "petrol": {
        "delhi": {"price": 94.72, "unit": "per litre"},
        "mumbai": {"price": 103.44, "unit": "per litre"},
    },
    "diesel": {
        "delhi": {"price": 87.62, "unit": "per litre"},
        "mumbai": {"price": 89.97, "unit": "per litre"},
    },
}


def _real_enabled(kind: str) -> bool:
    """True only when a key and the resource id for this kind are configured."""
    return bool(os.getenv("DATA_GOV_API_KEY")) and bool(RESOURCE_IDS.get(kind))


def _kind_for(commodity: str) -> str:
    """Fuel commodities use the fuel dataset; everything else is grocery."""
    return "fuel" if commodity.lower() in {"petrol", "diesel"} else "grocery"


def _fetch_mock(commodity: str, city: str) -> Optional[dict]:
    """Return a mock daily price for a commodity/city, or None if unknown."""
    row = _MOCK_PRICES.get(commodity.lower(), {}).get(city.lower())
    if not row:
        return None
    return {
        "commodity": commodity.lower(),
        "city": city.lower(),
        "price": float(row["price"]),
        "unit": row["unit"],
        "date": date.today().isoformat(),
        "source": "data_gov_mock",
    }


def _fetch_real(commodity: str, city: str) -> Optional[dict]:
    """Query data.gov.in for the latest price. Failure returns None."""
    import httpx

    kind = _kind_for(commodity)
    resource_id = RESOURCE_IDS[kind]
    params = {
        "api-key": os.getenv("DATA_GOV_API_KEY"),
        "format": "json",
        "limit": 1,
        "filters[commodity]": commodity,
        "filters[market]": city,
    }
    try:
        resp = httpx.get(
            f"{DATA_GOV_ENDPOINT}/{resource_id}",
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        records = resp.json().get("records", [])
    except Exception:
        return None

    if not records:
        return None
    record = records[0]
    # Field names vary by dataset; modal_price is common for mandi data.
    price = record.get("modal_price") or record.get("price")
    if price is None:
        return None
    return {
        "commodity": commodity.lower(),
        "city": city.lower(),
        "price": float(price),
        "unit": record.get("unit", ""),
        "date": record.get("arrival_date") or date.today().isoformat(),
        "source": "data_gov",
    }


def fetch_commodity_price(commodity: str, city: str) -> Optional[dict]:
    """Latest official price for a grocery/fuel commodity in a city, or None."""
    kind = _kind_for(commodity)
    if _real_enabled(kind):
        real = _fetch_real(commodity, city)
        if real:
            return real
    return _fetch_mock(commodity, city)

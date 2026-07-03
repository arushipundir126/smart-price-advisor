"""
FILE: backend/jobs/refresh_watchlist_prices.py

WHAT THIS DOES:
The daily background job. For every not-yet-bought watched product it re-fetches
prices once, stores a fresh snapshot, and flags the item as notified when the
best price has reached the user's target. It then refreshes up to 3 recently
searched products beyond the watchlist, so price history (and the trend signal)
keeps growing every day even when nobody opens the app. Runs daily via the
GitHub Actions workflow.

CHANGES THIS SESSION:
- Created run() that groups items by product, refreshes prices, and flags targets.
- Also refreshes up to 3 recently searched non-watchlist products daily, capped
  to stay inside the free SerpAPI quota.

WHERE IT FITS:
The "scheduled checks" piece of the stack. Reads the watchlist, writes snapshots,
and updates the notified flag the frontend banner reads.

CALLED BY / IMPORTS FROM:
Run with: python -m jobs.refresh_watchlist_prices
Imports the watchlist, product and price-snapshot db helpers and the price
service clients.
"""
from db.price_snapshots import add_snapshot
from db.products import get_recent_products
from db.watchlist import get_all_active, mark_notified
from services.apify_client import fetch_prices
from services.serpapi_client import fetch_shopping_prices

# How many recently searched (non-watchlist) products to also refresh each day.
# 3 per day is ~90 SerpAPI searches a month, safely inside the free quota.
RECENT_PRODUCTS_PER_RUN = 3


def _refresh_one(product_id: str, name: str) -> float | None:
    """Fetch prices for one product and store snapshots. Returns best price."""
    rows = fetch_prices(name) + fetch_shopping_prices(name)
    if not rows:
        return None
    for row in rows:
        add_snapshot(product_id, row["platform"], row["price"], row.get("mrp"))
    return min(float(r["price"]) for r in rows)


def run() -> None:
    """Refresh watched products, flag target hits, then top up recent history."""
    items = get_all_active()

    # Group by product so each product's price is fetched only once.
    by_product: dict[str, dict] = {}
    for item in items:
        group = by_product.setdefault(
            item["product_id"], {"name": item["name"], "items": []}
        )
        group["items"].append(item)

    checked = 0
    flagged = 0
    for product_id, group in by_product.items():
        name = group["name"]
        if not name:
            continue

        best = _refresh_one(product_id, name)
        if best is None:
            continue
        checked += 1

        for item in group["items"]:
            target = item["target_price"]
            if target is not None and best <= float(target) and not item["notified"]:
                mark_notified(item["id"])
                flagged += 1
                print(f"Target hit: {name} at Rs {int(best)} (target Rs {int(target)})")

    # Beyond the watchlist: keep history growing for what people search, so the
    # price-trend signal has data. Capped to protect the free search quota.
    recent_checked = 0
    try:
        for prod in get_recent_products(limit=10):
            if recent_checked >= RECENT_PRODUCTS_PER_RUN:
                break
            if prod["id"] in by_product:
                continue  # already refreshed above via the watchlist
            if _refresh_one(prod["id"], prod["name"]) is not None:
                recent_checked += 1
    except Exception as exc:
        print(f"Recent-product refresh skipped: {exc}")

    print(
        f"Done. Refreshed {checked} watched and {recent_checked} recent "
        f"product(s); flagged {flagged} price drop(s)."
    )


if __name__ == "__main__":
    run()

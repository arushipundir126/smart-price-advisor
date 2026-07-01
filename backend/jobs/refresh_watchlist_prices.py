"""
FILE: backend/jobs/refresh_watchlist_prices.py

WHAT THIS DOES:
The daily job behind the watchlist. For every not-yet-bought watched product it
re-fetches prices once, stores a fresh snapshot, and flags the item as notified
when the best price has reached the user's target. Runs once a day as a Render
cron, so drops are caught without the user reopening the app, and prices are
checked at most once a day rather than on every visit.

CHANGES THIS SESSION:
- Created run() that groups items by product, refreshes prices, and flags targets.

WHERE IT FITS:
The "scheduled checks" piece of the stack. Reads the watchlist, writes snapshots,
and updates the notified flag the frontend banner reads.

CALLED BY / IMPORTS FROM:
Run with: python -m jobs.refresh_watchlist_prices
Imports the watchlist and price-snapshot db helpers and the price service clients.
"""
from db.price_snapshots import add_snapshot
from db.watchlist import get_all_active, mark_notified
from services.apify_client import fetch_prices
from services.serpapi_client import fetch_shopping_prices


def run() -> None:
    """Refresh prices for all watched products and flag any that hit target."""
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

        rows = fetch_prices(name) + fetch_shopping_prices(name)
        if not rows:
            continue

        for row in rows:
            add_snapshot(product_id, row["platform"], row["price"], row.get("mrp"))
        best = min(float(r["price"]) for r in rows)
        checked += 1

        for item in group["items"]:
            target = item["target_price"]
            if target is not None and best <= float(target) and not item["notified"]:
                mark_notified(item["id"])
                flagged += 1
                print(f"Target hit: {name} at Rs {int(best)} (target Rs {int(target)})")

    print(f"Done. Refreshed {checked} product(s); flagged {flagged} price drop(s).")


if __name__ == "__main__":
    run()

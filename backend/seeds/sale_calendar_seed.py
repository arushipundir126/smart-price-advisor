"""
FILE: backend/seeds/sale_calendar_seed.py

WHAT THIS DOES:
One-time script that fills the sale_calendar table with known Indian sales, each
with category tags and common bank offers. Idempotent: re-running skips any sale
whose name and start date already exist, so it never duplicates rows.

CHANGES THIS SESSION:
- Added build_entries() (pure data) and a main() that inserts missing rows.

WHERE IT FITS:
Run once after Supabase keys are set: python -m seeds.sale_calendar_seed
Makes Signal 4 (days-to-next-sale) work with real dates. Update quarterly or
when new sale dates are announced.

CALLED BY / IMPORTS FROM:
Imports get_client from db/supabase_client. Run manually, not imported by the app.
"""

# Common bank offers reused across the big sales.
_STANDARD_BANK_OFFERS = [
    {"bank": "HDFC", "card_type": "Credit Card", "discount_pct": 10, "cap_inr": 1500},
    {"bank": "ICICI", "card_type": "Credit Card", "discount_pct": 10, "cap_inr": 2000},
    {"bank": "SBI", "card_type": "Credit Card", "discount_pct": 10, "cap_inr": 1750},
]

_ELECTRONICS = [
    "smartphones", "laptops", "tablets", "televisions", "audio",
    "wearables", "cameras", "large_appliances", "small_appliances",
    "kitchen_appliances",
]
_FASHION_BEAUTY = ["fashion_clothing", "footwear", "beauty_skincare"]


def build_entries() -> list[dict]:
    """Return the sale rows to seed. Pure data, no database. Update quarterly."""
    return [
        {
            "sale_name": "Independence Day Sale",
            "platform": "Amazon / Flipkart",
            "category_tags": [],  # empty means all categories
            "start_date": "2026-08-08",
            "end_date": "2026-08-15",
            "bank_offers": _STANDARD_BANK_OFFERS,
        },
        {
            "sale_name": "Amazon Great Indian Festival",
            "platform": "Amazon",
            "category_tags": _ELECTRONICS + _FASHION_BEAUTY,
            "start_date": "2026-10-03",
            "end_date": "2026-10-18",
            "bank_offers": _STANDARD_BANK_OFFERS,
        },
        {
            "sale_name": "Flipkart Big Billion Days",
            "platform": "Flipkart",
            "category_tags": _ELECTRONICS + _FASHION_BEAUTY,
            "start_date": "2026-10-03",
            "end_date": "2026-10-10",
            "bank_offers": _STANDARD_BANK_OFFERS,
        },
        {
            "sale_name": "Nykaa Pink Friday Sale",
            "platform": "Nykaa",
            "category_tags": ["beauty_skincare", "fashion_clothing"],
            "start_date": "2026-11-20",
            "end_date": "2026-11-30",
            "bank_offers": _STANDARD_BANK_OFFERS,
        },
        {
            "sale_name": "Myntra End of Reason Sale",
            "platform": "Myntra",
            "category_tags": _FASHION_BEAUTY,
            "start_date": "2026-12-12",
            "end_date": "2026-12-18",
            "bank_offers": _STANDARD_BANK_OFFERS,
        },
        {
            "sale_name": "Republic Day Sale",
            "platform": "Amazon / Flipkart",
            "category_tags": [],  # all categories
            "start_date": "2027-01-20",
            "end_date": "2027-01-26",
            "bank_offers": _STANDARD_BANK_OFFERS,
        },
    ]


def main() -> None:
    """Insert any sale rows that are not already present. Idempotent."""
    from db.supabase_client import get_client

    client = get_client()
    inserted = 0
    for entry in build_entries():
        existing = (
            client.table("sale_calendar")
            .select("id")
            .eq("sale_name", entry["sale_name"])
            .eq("start_date", entry["start_date"])
            .limit(1)
            .execute()
        )
        if existing.data:
            continue
        client.table("sale_calendar").insert(entry).execute()
        inserted += 1
        print(f"Seeded: {entry['sale_name']} ({entry['start_date']})")

    print(f"Done. Inserted {inserted} new sale(s); skipped existing ones.")


if __name__ == "__main__":
    main()

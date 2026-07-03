"""
FILE: backend/seeds/create_demo_user.py

WHAT THIS DOES:
One-time script that creates (or resets) the shared demo account used to show
the app to reviewers. Creates the user via the Supabase admin API with the
email pre-confirmed, so it can sign in immediately.

CHANGES THIS SESSION:
- Created the script with a fixed demo email and password.

WHERE IT FITS:
Run once by hand, like the sale-calendar seed. Not part of the running app.

CALLED BY / IMPORTS FROM:
Run with: python -m seeds.create_demo_user
Uses db/supabase_client.get_client (service role key required).
"""
from db.supabase_client import get_client

DEMO_EMAIL = "demo@smartpriceadvisor.app"
DEMO_PASSWORD = "Demo2026Pass"


def run() -> None:
    client = get_client()
    try:
        client.auth.admin.create_user(
            {
                "email": DEMO_EMAIL,
                "password": DEMO_PASSWORD,
                "email_confirm": True,
            }
        )
        print(f"Demo user created: {DEMO_EMAIL}")
    except Exception as exc:
        # Most likely it already exists; reset the password so the shared
        # credentials always work.
        try:
            users = client.auth.admin.list_users()
            match = next((u for u in users if u.email == DEMO_EMAIL), None)
            if match:
                client.auth.admin.update_user_by_id(
                    match.id, {"password": DEMO_PASSWORD}
                )
                print(f"Demo user already existed; password reset: {DEMO_EMAIL}")
            else:
                print(f"Could not create demo user: {exc}")
        except Exception as inner:
            print(f"Could not create or reset demo user: {inner}")


if __name__ == "__main__":
    run()

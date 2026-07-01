# Smart Price Advisor

An evidence-based shopping intelligence web app for Indian consumers: "Buy now or wait?"

You enter a branded product and how long you are willing to wait. The app checks the live price against price history, the upcoming sale calendar, and recent market news, then returns a clear verdict, Buy Now or Wait, with a confidence band (High, Medium, Low), the best price right now, where to buy it, stackable discounts, and how long to wait for the likely best deal. It never fortune-tells an exact future price; it states evidenced odds.

## Why not just ask a chatbot?

A general assistant has a knowledge cutoff, so it does not know today's price, today's news, or that a sale starts in six days. Smart Price Advisor feeds live, verified data into the reasoning step, so the verdict is backed by evidence, not memory.

## How the verdict is made

Six independent signals each vote Buy Now or Wait with a weight. They are combined into one verdict, and the confidence band reflects how strongly they agree (a single signal can never read as High).

1. Fake-discount check: live price vs MRP and vs the product's own stored median.
2. Cross-platform best price: the cheapest seller right now, with a direct link.
3. Price-history trend: direction and volatility from stored snapshots.
4. Days-to-next-sale: a deterministic calendar of Indian sales, weighted heavily.
5. Category elasticity: how much a category actually moves in sales.
6. News-shock detector: recent headlines that history cannot foresee.

If a live source is unavailable, the app falls back to a Google Shopping price or a direct search link, so a verdict is always produced.

## Tech stack

- Frontend: React (Vite), deployed on Vercel
- Backend: Python (FastAPI), deployed on Render
- Database: Supabase (PostgreSQL): price history and watchlists
- Prices: Apify actors (Amazon India, Flipkart and more), SerpAPI Google Shopping fallback, data.gov.in for groceries and fuel
- News: NewsAPI
- AI synthesis: Gemini (with a deterministic fallback so it never fails)

All service clients are mock-first: the app runs on realistic sample data until you add real keys, then switches to live automatically.

## Project layout

```
backend/    FastAPI app, six signals, service clients, db helpers, seed, cron job
frontend/   React (Vite) app: search, verdict, and the watchlist side panel
render.yaml Render blueprint (web service + daily cron)
docs/       this README
```

## Setup

### Backend

```
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then fill in the values you have
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000/docs for the Swagger UI.

One-time database setup (needs Supabase keys in .env):

1. In the Supabase SQL Editor, run `backend/db/schema.sql`.
2. Seed the sale calendar: `python -m seeds.sale_calendar_seed`.

The app works without any keys using built-in mock data. Add keys to go live:
Supabase (history and watchlist), Apify and SerpAPI (real prices), NewsAPI
(real news), Gemini (AI wording), data.gov.in (groceries and fuel).

### Frontend

```
cd frontend
npm install
cp .env.example .env             # set VITE_API_BASE_URL to the backend URL
npm run dev                      # http://localhost:5173
```

## Environment variables

Backend (`backend/.env`): SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, APIFY_API_TOKEN, SERPAPI_KEY, NEWSAPI_KEY, GEMINI_API_KEY, DATA_GOV_API_KEY, FRONTEND_ORIGIN.

Frontend (`frontend/.env`): VITE_API_BASE_URL.

All keys are backend-only. Never put them in the frontend. Real `.env` files are gitignored.

## Deployment

### Backend on Render

Push to GitHub and create a Blueprint from `render.yaml`. It provisions the web
service and the daily watchlist cron. Set every environment variable in the
Render dashboard. Set `FRONTEND_ORIGIN` to your Vercel URL so CORS allows only it.

### Frontend on Vercel

Import the repo, set the root directory to `frontend`, and set `VITE_API_BASE_URL`
to the Render backend URL. Vercel auto-deploys on push to main.

## Watchlist

Add a product to the watchlist with a target price. The side panel (bottom-right)
lists your items with their current price and status: Tracking, Price dropped, or
Bought. The daily cron re-checks prices once a day and flags an item when it hits
your target; you see an in-app banner on your next visit. You can remove an item
or mark it as bought.

## Sample verdict

Request:

```
POST /api/analyse
{ "product": "Samsung Galaxy S24", "wait_tolerance_days": 30 }
```

Response (abridged):

```
{
  "verdict": "Wait",
  "confidence": "Medium",
  "summary_reason": "Better to wait: recent news suggests the price may fall soon.",
  "best_price": 61499,
  "best_platform": "Flipkart",
  "buy_link": "https://www.flipkart.com/search?q=Samsung+Galaxy+S24",
  "signal_summaries": [ ... six signals with plain reasons ... ]
}
```

## What it does not do

- Does not predict an exact future price; it states evidenced probabilities.
- Does not handle vague or unbranded queries; a brand name is required.
- Does not give financial or investment advice.
- Does not store personal data beyond a session-scoped watchlist.

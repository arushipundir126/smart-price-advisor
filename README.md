# Smart Price Advisor

**Buy now, or wait?** Evidence-based shopping intelligence for Indian consumers.

Enter a branded product and how long you are willing to wait. Smart Price Advisor checks the live price across trusted Indian marketplaces, weighs it against price history, the Indian sale calendar, category behaviour, and market news, then returns a clear verdict: **Buy Now** or **Wait**, with a confidence band, the best price right now, where to buy it, stackable bank offers, and how long to wait for the likely best deal.

**Live app:** https://smart-price-advisor.vercel.app
**Demo account:** `demo@smartpriceadvisor.app` / `Demo2026Pass`

---

## Why this exists

A general chatbot has a knowledge cutoff. It does not know today's price, that a sale starts in six days, or that a successor phone was announced yesterday. Smart Price Advisor feeds **live, verifiable data** into the decision, so the verdict is backed by evidence, never a confident guess from memory.

Three principles:

1. **Evidence over vibes.** Every verdict is traceable to six named signals with plain-English reasons.
2. **Honest confidence.** Confidence is a band (High, Medium, Low), never a false-precise percentage.
3. **Never a dead end.** If a data source is down, the app falls back (cached price, last known price, direct search link) instead of erroring.

## Features

- **Buy Now / Wait verdict** with a High / Medium / Low confidence band and a one-line reason
- **Best live price** from trusted Indian sellers only (grey-market and refurbished listings are filtered out)
- **Cross-platform comparison** across Amazon, Flipkart, Croma, Reliance Digital, Tata CLiQ / Neu, JioMart, Nykaa, Myntra, Ajio, Vijay Sales, Meesho, official brand stores, and more
- **Fake-discount detection** using the real MRP (strikethrough price), the product's own price history, and Google's LOW PRICE badge
- **Sale calendar awareness**: Great Indian Festival, Big Billion Days, Nykaa Pink Friday, Myntra EORS, Republic Day and Independence Day sales, with associated bank-card offers surfaced as stackable discounts
- **Price-history trend chart** built from stored snapshots, cleaned of outliers
- **Accounts and watchlist**: sign in with email and password; every product you search is added to your watchlist automatically and follows you across devices
- **Adaptive price re-checks**: watched items are re-checked on a schedule scaled to your wait window (about 3 checks for a week, 5 for a month), never on every visit
- **Price-drop alerts** shown in-app on your next visit when a target price is hit
- **Vague-query protection**: "sunflower oil" is asked to include a brand; "Fortune Sunflower Oil" goes through
- **Light and dark theme**, mobile-first, fast on slow connections (system fonts, ~2 kB of CSS, no heavy assets)

## How the verdict is made

Six independent signals each vote `buy_now` or `wait` with a weight. A weighted aggregate produces the verdict; Gemini synthesises the plain-English summary (with a deterministic fallback so the app works even without an AI key). Confidence reflects how strongly the signals agree, and a single signal can never present as High confidence.

| # | Signal | What it checks |
|---|--------|----------------|
| 1 | Fake-discount check | Live price vs real MRP, vs the product's stored median, plus Google's own LOW PRICE / PRICE DROP badge |
| 2 | Cross-platform best price | The cheapest trusted seller right now, with the buy link |
| 3 | Price-history trend | Direction and volatility of stored snapshots; falling or swinging prices reward waiting |
| 4 | Days to next sale | A deterministic calendar of known Indian sales mapped to categories, weighted heavily |
| 5 | Category elasticity | How much this category actually drops in sales (electronics fall sharply, staples barely move) |
| 6 | News shock | Headlines that history cannot foresee: successor launches, import bans, price cuts |

If the keyword-based category guesser cannot classify a product, Gemini classifies it once and the result is cached on the product row, so signal 5 works for the whole catalogue.

## Architecture

```
React (Vite + TS)          FastAPI (Python)              Data
Vercel                     Render                        sources
┌──────────────┐  HTTPS   ┌────────────────────┐
│ Search        │ ───────► │ POST /api/analyse   │ ───►  SerpAPI (Google Shopping IN)
│ Verdict       │          │  6 signals + agg    │ ───►  Apify actors (optional)
│ Watchlist     │          │  Gemini synthesis   │ ───►  NewsAPI (1h cache)
│ Sign in       │          │ /api/watchlist/*    │ ───►  Gemini (verdict + category)
└──────┬───────┘          │ /api/auth/signup    │
       │ supabase-js       └─────────┬──────────┘
       ▼                             ▼
   Supabase Auth               Supabase Postgres
   (email + password)          products, price_snapshots (append-only),
                               sale_calendar, watchlist_items, news_cache

GitHub Actions (daily): refreshes watchlist prices + 3 recent products,
flags target-price hits, keeps the trend signal growing.
```

Design decisions worth knowing:

- **Mock-first services.** Every external client (prices, news, AI) runs on realistic mock data when its key is missing and switches to live automatically when the key is present. The app is fully demoable with zero keys.
- **Best-effort database.** If Supabase is unreachable, the analyse route still returns a verdict; history-based signals simply abstain.
- **Result caching.** Identical searches within 6 hours are served from an in-memory cache, protecting the free SerpAPI quota and making repeats near-instant.
- **Trusted sellers only.** Price rows are filtered for accessories, wrong model variants (an S24 query never matches an S24 FE), refurbished or used listings, junk outliers, and unknown resellers.

## Getting started

### Prerequisites

- Python 3.12+
- Node 18+
- A Supabase project (free tier is fine)

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in values (see table below)
uvicorn main:app --reload --port 8000
```

Swagger UI: http://localhost:8000/docs

### 2. Database (one time)

1. In the Supabase SQL Editor, run [`backend/db/schema.sql`](backend/db/schema.sql).
2. Seed the sale calendar: `python -m seeds.sale_calendar_seed`
3. Create the demo account (optional): `python -m seeds.create_demo_user`

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env             # set the three values below
npm run dev                      # http://localhost:5173
```

### Environment variables

**Backend (`backend/.env`)** - all keys are server-side only, never exposed to the client:

| Variable | Required | Purpose |
|----------|----------|---------|
| `SUPABASE_URL` | yes | Supabase project URL |
| `SUPABASE_ANON_KEY` | yes | Client-safe key (used for token checks) |
| `SUPABASE_SERVICE_ROLE_KEY` | yes | Admin key for DB writes and signup. Keep secret |
| `SERPAPI_KEY` | for live prices | Google Shopping India prices (free: 100 searches/month) |
| `GEMINI_API_KEY` | for AI verdicts | Verdict wording + category classification (free tier) |
| `NEWSAPI_KEY` | for live news | News-shock signal (free tier) |
| `APIFY_API_TOKEN` | optional | Direct marketplace scraping actors |
| `DATA_GOV_API_KEY` | optional | Grocery and fuel prices by city |
| `FRONTEND_ORIGIN` | yes | Allowed CORS origin(s), comma-separated |

**Frontend (`frontend/.env`)** - client-safe values only:

| Variable | Purpose |
|----------|---------|
| `VITE_API_BASE_URL` | Backend URL (local: `http://localhost:8000`) |
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key (client-safe by design) |

Without any optional keys the app runs end to end on built-in mock data.

## API reference

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| POST | `/api/analyse` | none | `{ product, wait_tolerance_days }` → full verdict object. Rate limit 10/min/IP |
| POST | `/api/auth/signup` | none | Create an account (email validated server-side, no verification mail). 5/min/IP |
| GET | `/api/watchlist/me` | Bearer | The signed-in user's watchlist with latest prices |
| POST | `/api/watchlist` | Bearer | Add or update a watched product (target price, wait window) |
| POST | `/api/watchlist/me/refresh` | Bearer | Re-check due items (adaptive interval). 30/min/IP |
| DELETE | `/api/watchlist/me/{product_id}` | Bearer | Remove an item |
| POST | `/api/watchlist/me/{product_id}/purchased` | Bearer | Mark an item as bought |
| GET | `/api/health` | none | Liveness check (safe for uptime monitors) |

Sign-in itself happens in the browser against Supabase Auth; the backend only ever sees the resulting access token and verifies it server-side on every watchlist call.

## Deployment

| Piece | Where | Notes |
|-------|-------|-------|
| Frontend | Vercel | Root directory `frontend`, set the three `VITE_*` variables |
| Backend | Render (free web service) | Root directory `backend`, start command `uvicorn main:app --host 0.0.0.0 --port $PORT`, set all backend variables and `PYTHON_VERSION=3.12.7` |
| Daily refresh | GitHub Actions | [`daily-price-refresh.yml`](.github/workflows/daily-price-refresh.yml) runs the snapshot job; needs `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SERPAPI_KEY` as repo secrets |
| Keep-awake | UptimeRobot (optional) | Ping `/api/health` every 5-10 min so the free Render instance never cold-starts |

Every push to `main` auto-deploys both Vercel and Render. Set `FRONTEND_ORIGIN` on Render to the Vercel URL so CORS only admits the real frontend.

## Security

- All API keys live server-side; the frontend ships only client-safe values
- Watchlist identity comes exclusively from the verified Supabase token; client-supplied ids are ignored
- Signup is rate limited, validates email and password server-side, and returns one generic failure message (no account enumeration)
- CORS locked to the deployed frontend origin; all DB access is parameterised; no `SELECT *`
- External buy links are protocol-sanitised before rendering
- Passwords are handled entirely by Supabase Auth and never touch this codebase

## What it deliberately does not do

- Does not predict an exact future price. It states evidenced probabilities, not guarantees
- Does not accept vague, unbranded queries. A brand is required for an honest answer
- Does not give financial or investment advice
- Does not store personal data beyond the sign-in email and the user's own watchlist
- Does not auto-place orders or touch marketplace accounts

## Project structure

```
backend/
  main.py               FastAPI app, CORS, rate limiter
  auth_helper.py        Signup route + token verification
  routers/              analyse.py, watchlist.py
  signals/              the six signals + aggregator
  services/             serpapi, apify, newsapi, gemini, data.gov clients (mock-first)
  db/                   supabase client, products, snapshots, sale calendar, watchlist
  seeds/                sale_calendar_seed.py, create_demo_user.py
  jobs/                 refresh_watchlist_prices.py (daily)
  data/                 category_elasticity.json
frontend/
  src/components/       VerdictCard, ActionStrip, AuthPage, WatchlistPanel, ...
  src/hooks/            useAnalyse, useWatchlist, useAuth
  src/lib/              supabase client
.github/workflows/      daily price refresh
```

## Known limitations

- Free SerpAPI tier allows ~100 live searches a month; beyond that the app serves cached or last-known prices (it degrades, it does not break)
- Google Shopping data occasionally lacks the MRP; the fake-discount signal then falls back to the stored median
- The price-trend signal needs a week or two of accumulated snapshots before it votes with conviction
- The sale calendar is seeded manually and reviewed quarterly

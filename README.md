<div align="center">

# Smart Price Advisor

### Buy Now, or Wait? Evidence-based shopping intelligence for Indian consumers.

**[Live App](https://smart-price-advisor.vercel.app)** &nbsp;|&nbsp; Demo login: `demo@smartpriceadvisor.app` / `Demo2026Pass`

</div>

---

## Table of Contents

1. [Project Description](#project-description)
2. [Problem Statement](#problem-statement)
3. [Solution Overview](#solution-overview)
4. [Key Features](#key-features)
5. [Live Demo](#live-demo)
6. [Screenshots](#screenshots)
7. [System Architecture](#system-architecture)
8. [Workflow](#workflow)
9. [Technology Stack](#technology-stack)
10. [Data Sources](#data-sources)
11. [Data Cleaning](#data-cleaning)
12. [Signal Design (Feature Engineering)](#signal-design-feature-engineering)
13. [Decision Pipeline](#decision-pipeline)
14. [Verdict Synthesis (No Trained Model)](#verdict-synthesis-no-trained-model)
15. [System Reliability & Evaluation](#system-reliability--evaluation)
16. [Price Prediction Methodology](#price-prediction-methodology)
17. [Recommendation Engine](#recommendation-engine)
18. [Explainability](#explainability)
19. [Folder Structure](#folder-structure)
20. [Installation Guide](#installation-guide)
21. [Prerequisites](#prerequisites)
22. [Environment Variables](#environment-variables)
23. [Running the Project](#running-the-project)
24. [API Documentation](#api-documentation)
25. [Usage Guide](#usage-guide)
26. [Sample Input & Output](#sample-input--output)
27. [Performance Characteristics](#performance-characteristics)
28. [Challenges Faced](#challenges-faced)
29. [Future Enhancements / Roadmap](#future-enhancements--roadmap)
30. [License](#license)

---

## Project Description

Smart Price Advisor is a web app that answers one question for Indian online shoppers: **should I buy this now, or is it worth waiting?**

You type a branded product and how long you're willing to wait. The app checks the live price across trusted Indian marketplaces, compares it against price history, the Indian sale calendar, how much that product category typically moves during sales, and recent market news, then returns a verdict, **Buy Now** or **Wait**, with an honest confidence band, the best price available right now, a direct buy link, stackable bank offers, and (when waiting is advised) how long the wait is likely to be worth it.

## Problem Statement

Online shoppers in India face three recurring problems:

1. **Fake discounts.** Sellers inflate the "before" price so a sale looks bigger than it is.
2. **No memory of price history.** A shopper sees today's price with no sense of whether it's actually low.
3. **No visibility into timing.** Sale calendars, bank offers, and category-specific discount depth (electronics vs. groceries) are scattered across sites, if published at all.

A general AI chatbot cannot fix this: its knowledge has a cutoff, so it doesn't know today's price, that a sale starts in six days, or that a successor product launched yesterday.

## Solution Overview

Smart Price Advisor feeds **live, verifiable data** into the decision instead of relying on a model's memory. Six independent, named signals each vote `buy_now` or `wait` with a weight and a plain-English reason. A weighted aggregator combines them into a verdict and an honest confidence band; an LLM (Gemini) only writes the final wording, it never invents facts the signals didn't provide. If any data source is unavailable, the app degrades gracefully (cache, last known price, direct search link) rather than failing.

## Key Features

- **Buy Now / Wait verdict** with a High / Medium / Low confidence band and a one-line plain-English reason (never a false-precise percentage)
- **Best live price** from trusted Indian sellers only; grey-market resellers, wrong model variants, and refurbished listings are filtered out
- **Cross-platform comparison** across Amazon, Flipkart, Croma, Reliance Digital, Tata CLiQ / Neu, JioMart, Nykaa, Myntra, Ajio, Vijay Sales, Meesho, official brand stores, and more
- **Fake-discount detection** using the real MRP (the strikethrough price), the product's own price history, and Google's own LOW PRICE / PRICE DROP badge
- **Sale calendar awareness**: Great Indian Festival, Big Billion Days, Nykaa Pink Friday, Myntra EORS, Republic Day and Independence Day sales, with bank-card offers surfaced as stackable discounts
- **Price-history trend chart** built from stored snapshots, cleaned of outliers
- **Accounts and watchlist**: sign in with email and password; every product you search is added to your watchlist automatically and follows you across devices
- **Adaptive price re-checks**: watched items are re-checked on a cadence scaled to your wait window (about 3 checks over a week, 5 over a month), never on every visit
- **In-app price-drop alerts** shown on your next visit when a target price is hit
- **Vague-query protection**: "sunflower oil" is asked to name a brand; "Fortune Sunflower Oil" goes straight through
- **Light and dark theme**, mobile-first, fast on slow connections (system fonts only, ~2 kB of CSS, no heavy assets)

## Live Demo

**App:** https://smart-price-advisor.vercel.app
**Demo account:** `demo@smartpriceadvisor.app` / password `Demo2026Pass`

Search any branded product (for example `Samsung Galaxy S24`, `Maybelline Fit Me Foundation`, `Fortune Sunflower Oil`) and set a wait window to see the full verdict.

## Screenshots

Screenshots are not yet committed to the repo. Placeholder folder: `docs/DEMO_SCREENSHOTS/`. Recommended set to add: search screen, verdict hero card, signal breakdown, watchlist panel, sign-in screen.

## System Architecture

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

- **Mock-first services.** Every external client (prices, news, AI) runs on realistic mock data when its key is missing and switches to live automatically once the key is present. The app is fully demoable with zero keys.
- **Best-effort database.** If Supabase is unreachable, the analyse route still returns a verdict; history-based signals simply abstain.
- **Result caching.** Identical searches within 6 hours are served from an in-memory cache, protecting the free SerpAPI quota and making repeats near-instant.
- **Trusted sellers only.** Price rows are filtered for accessories, wrong model variants (an "S24" query never matches an "S24 FE"), refurbished or used listings, junk outliers, and unknown resellers.

## Workflow

```
1. User submits a product name + wait tolerance (1 week to 1 year)
2. Vague-query guard: reject bare category terms with no brand ("sunflower oil")
3. Category guess: keyword match, else one cached Gemini classification call
4. Fetch live prices: SerpAPI (Google Shopping India) + optional Apify actors
5. Clean results: drop accessories, wrong variants, used/refurbished items,
   untrusted sellers, and statistical outliers
6. Store a price snapshot (append-only) and pull cleaned history + median
7. Run six signals against the cleaned data
8. Aggregate signal votes into a verdict + confidence band
9. Gemini writes the plain-English summary from the signal data only
   (deterministic fallback if no Gemini key is set)
10. Return verdict, best price, buy link, platform comparison, discounts,
    signal breakdown, and price history to the client
11. If signed in: the product is added to the user's watchlist automatically
12. Daily job (GitHub Actions): re-checks watchlist + recent products,
    flags any that hit their target price
```

## Technology Stack

| Layer | Choice |
|---|---|
| Frontend | React (Vite, TypeScript), deployed on Vercel |
| Backend | Python, FastAPI, deployed on Render |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth (email + password) |
| Live prices | SerpAPI (Google Shopping India), optional Apify actors |
| News | NewsAPI (free tier, 1-hour cache) |
| AI synthesis & classification | Google Gemini (`gemini-2.5-flash`), free tier |
| Scheduled jobs | GitHub Actions (daily cron, no paid Render add-on needed) |
| Rate limiting | slowapi |
| Version control | Git / GitHub |

## Data Sources

This project does not train a model on a static labeled dataset. Its "data" is live and accumulated over time:

| Source | What it provides | Refresh |
|---|---|---|
| SerpAPI (Google Shopping India) | Live price, seller, strikethrough MRP, deal badge | On every search (cached 6h) |
| `price_snapshots` table | Historical prices per product, append-only | Grows with every fresh search + daily job |
| `sale_calendar` table | Seeded Indian sale events + bank offers | Seeded manually, reviewed quarterly |
| `category_elasticity.json` | Rule table: typical sale-drop % per category | Static, hand-curated from domain knowledge |
| NewsAPI | Recent headlines per product | Cached 1 hour |
| Gemini | Category classification for products the keyword list misses | One call per new product, cached forever |

## Data Cleaning

Live shopping results are noisy. Before any price reaches a signal, it passes through:

1. **Accessory filter** - drops covers, cables, protectors, and similar items masquerading as the product
2. **Condition filter** - drops refurbished, renewed, open-box, and used listings
3. **Model-variant filter** - a query for "Galaxy S24" must not match "Galaxy S24 FE" or "S24 Ultra"
4. **Trusted-seller filter** - only known Indian marketplaces and official brand stores qualify as the recommended price
5. **Statistical outlier filter** - anything priced below 40% of the cleaned median is dropped (catches stray ₹1 / ₹99 junk listings)
6. **History cleaning** - stored snapshots are filtered the same way before computing the median or feeding the trend signal, so old junk data can never resurface

## Signal Design (Feature Engineering)

There's no traditional feature matrix here; instead, each signal derives a small set of interpretable values from the cleaned live data:

| Derived value | Used by |
|---|---|
| `price_vs_median` (%) | Fake-discount signal |
| `mrp_discount_pct` (from strikethrough price) | Fake-discount signal |
| Google `deal_tag` (LOW PRICE / PRICE DROP) | Fake-discount signal |
| Cheapest trusted platform + spread vs. priciest | Cross-platform signal |
| Trend direction + volatility over stored history | Price-trend signal |
| Days until next matching sale + bank offers | Days-to-sale signal |
| Category typical sale-drop range + worth-waiting flag | Category-elasticity signal |
| Keyword hits in recent headlines (buy vs. wait) | News-shock signal |

## Decision Pipeline

```
price rows ─┬─► Signal 1: Fake-discount check ─┐
            ├─► Signal 2: Cross-platform price  │
            ├─► Signal 3: Price-history trend   ├─► Weighted aggregator ─► Verdict + Confidence
            ├─► Signal 4: Days to next sale      │
            ├─► Signal 5: Category elasticity    │
            └─► Signal 6: News shock            ─┘
                                                       │
                                                       ▼
                                          Gemini (wording only, or
                                          deterministic fallback)
```

Each signal returns `{ signal_name, vote, weight, reason }`. Votes with no evidence abstain (weight 0) rather than guessing. The aggregator combines the weighted votes into `Buy Now` or `Wait`, and confidence reflects how strongly the participating signals agree.

## Verdict Synthesis (No Trained Model)

This project does **not** train or fine-tune a machine learning model. There is no dataset of past purchase outcomes to learn from, and predicting "the right answer" for a subjective buy/wait decision has no ground truth to train against. Instead:

- The six signals are **rule-based and deterministic**, derived from live data and hand-curated domain tables (`category_elasticity.json`, `sale_calendar`).
- **Gemini** (a pre-trained, hosted LLM accessed via API) is used only for two narrow, verifiable jobs: (1) writing the plain-English verdict summary from signal data it is given, with an explicit instruction not to use its own memory of prices, and (2) classifying a product into one of 19 fixed categories when the keyword matcher fails.
- If Gemini is unavailable, a deterministic fallback builds the same verdict shape directly from the signal votes, so the app never depends on the AI call to function.

This is a conscious design choice: an evidence-driven, auditable rule system is more trustworthy for a "should you spend money now" decision than an opaque model with no way to verify its reasoning.

## System Reliability & Evaluation

Since there is no trained classifier, there are no accuracy/precision/recall metrics to report. What is measured and true today:

| Property | Measured value |
|---|---|
| Repeat-search cache speedup | 14.5s (live fetch) → 2.6s (cached) |
| Free SerpAPI quota | ~100 searches/month; degrades to cached/last-known price when exhausted, never errors |
| Confidence discipline | A single voting signal can never present as High confidence (requires ≥3 participating signals) |
| Category coverage | 19 curated categories via keyword match + Gemini fallback for anything unmatched |
| Vague-query rejection | Verified against 18 test cases (generic terms, branded terms, edge cases) |
| Trusted-seller matching | Verified against 20 test cases including word-boundary safety (e.g. "pineapple store" correctly not matched) |

## Price Prediction Methodology

Smart Price Advisor does **not** predict an exact future price. It states an evidenced direction and, when advising to wait, an estimated number of days based on:

- The soonest matching upcoming sale within the user's wait tolerance
- How deep that category typically drops in a sale (from `category_elasticity.json`)
- Whether the current price is already trending down (from stored history)

The output is deliberately a **range of confidence, not a number**: "Wait, Medium confidence, expected best deal in about 12 days" rather than "the price will be ₹41,203 on July 14."

## Recommendation Engine

The "recommendation" is the aggregated verdict plus its supporting detail:

- **Verdict**: Buy Now or Wait
- **Confidence band**: High / Medium / Low
- **Best price + direct buy link** on a trusted seller
- **Cross-platform comparison list**
- **Stackable discounts**: bank/card offers tied to the next relevant sale
- **Wait estimate**: only shown when the verdict is Wait

## Explainability

Every verdict ships with a full breakdown of **all six signals**, each with its own vote and plain-English reason, e.g.:

> Price-trend: `wait` — "The price has been falling over your recent searches, so waiting is likely to pay off."

This is built from the app's own signal objects, not from the LLM's retelling, so the explanation is always traceable to the exact rule that fired. There is no black-box feature-importance score; the six signals themselves are the full explanation.

## Folder Structure

```
backend/
  main.py               FastAPI app, CORS, rate limiter
  auth_helper.py         Signup route + Supabase token verification
  routers/                analyse.py, watchlist.py
  signals/                the six signals + aggregator
  services/               serpapi, apify, newsapi, gemini, data.gov clients (mock-first)
  db/                     supabase client, products, snapshots, sale calendar, watchlist
  seeds/                  sale_calendar_seed.py, create_demo_user.py
  jobs/                   refresh_watchlist_prices.py (daily)
  data/                   category_elasticity.json
frontend/
  src/components/         VerdictCard, ActionStrip, AuthPage, WatchlistPanel, ...
  src/hooks/               useAnalyse, useWatchlist, useAuth
  src/lib/                 supabase client
.github/workflows/        daily price refresh
```

## Installation Guide

### Prerequisites

- Python 3.12+
- Node 18+
- A Supabase project (free tier is sufficient)

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in values, see table below
uvicorn main:app --reload --port 8000
```

Swagger UI: available at the `/docs` path of whatever address `uvicorn` prints in your terminal (default port 8000).

### 2. Database (one time)

1. In the Supabase SQL editor, run [`backend/db/schema.sql`](backend/db/schema.sql).
2. Seed the sale calendar: `python -m seeds.sale_calendar_seed`
3. Create a demo account (optional): `python -m seeds.create_demo_user`

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env             # set the three values below
npm run dev                      # open the address Vite prints in your terminal
```

### Environment Variables

**Backend (`backend/.env`)** — server-side only, never exposed to the client:

| Variable | Required | Purpose |
|---|---|---|
| `SUPABASE_URL` | yes | Supabase project URL |
| `SUPABASE_ANON_KEY` | yes | Client-safe key (used for token checks) |
| `SUPABASE_SERVICE_ROLE_KEY` | yes | Admin key for DB writes and signup. Keep secret |
| `SERPAPI_KEY` | for live prices | Google Shopping India prices (free tier: 100 searches/month) |
| `GEMINI_API_KEY` | for AI verdicts | Verdict wording + category classification (free tier) |
| `NEWSAPI_KEY` | for live news | News-shock signal (free tier) |
| `APIFY_API_TOKEN` | optional | Direct marketplace scraping actors |
| `DATA_GOV_API_KEY` | optional | Grocery and fuel prices by city |
| `FRONTEND_ORIGIN` | yes | Allowed CORS origin(s), comma-separated |

**Frontend (`frontend/.env`)** — client-safe values only:

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Backend URL. Production: `https://smart-price-advisor.onrender.com` |
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key (client-safe by design) |

Without any optional keys, the app runs end to end on built-in mock data.

## Running the Project

- **Live production app:** https://smart-price-advisor.vercel.app (backed by `https://smart-price-advisor.onrender.com`)
- **Locally:** follow [Installation Guide](#installation-guide) above; run the backend (`uvicorn`) and the frontend (`npm run dev`) in separate terminals, each printing the address to open

## API Documentation

| Method | Route | Auth | Description |
|---|---|---|---|
| POST | `/api/analyse` | none | `{ product, wait_tolerance_days }` → full verdict object. Rate limit 10/min/IP |
| POST | `/api/auth/signup` | none | Create an account (email validated server-side, no verification mail). 5/min/IP |
| GET | `/api/watchlist/me` | Bearer | The signed-in user's watchlist with latest prices |
| POST | `/api/watchlist` | Bearer | Add or update a watched product (target price, wait window) |
| POST | `/api/watchlist/me/refresh` | Bearer | Re-check due items (adaptive interval). 30/min/IP |
| DELETE | `/api/watchlist/me/{product_id}` | Bearer | Remove an item |
| POST | `/api/watchlist/me/{product_id}/purchased` | Bearer | Mark an item as bought |
| GET | `/api/health` | none | Liveness check (safe for uptime monitors) |

Sign-in happens in the browser against Supabase Auth directly; the backend only ever sees the resulting access token and verifies it server-side on every watchlist call. Interactive Swagger docs are available at `/docs` on the backend URL.

## Usage Guide

1. Open **https://smart-price-advisor.vercel.app**
2. Type a **branded** product name (a bare category like "phone" or "shampoo" will prompt you to add a brand)
3. Choose how long you're willing to wait (1 week to 1 year, or a custom number of days)
4. Read the verdict card: **Buy Now** or **Wait**, with its confidence band and reason
5. Check the best price and buy link, the platform comparison, and any stackable bank offers
6. Expand **How we decided** to see all six signals and their individual reasoning
7. Click **Sign in** (top right) to create a free account; every product you search from then on is added to your watchlist automatically
8. Open the **Watchlist** panel to see tracked items, set a target price for an alert, remove items, or mark them as bought

## Sample Input & Output

**Request**

```
POST /api/analyse
{
  "product": "Samsung Galaxy S24",
  "wait_tolerance_days": 90
}
```

**Response (abridged)**

```json
{
  "verdict": "Wait",
  "confidence": "Medium",
  "summary_reason": "The price has been trending upward and no major sale falls within your wait window, but the category typically sees a real drop during festive sales.",
  "best_price": 40999,
  "best_platform": "Flipkart",
  "buy_link": "https://www.flipkart.com/...",
  "price_vs_median": -2.1,
  "platform_prices": [
    { "platform": "Flipkart", "price": 40999 },
    { "platform": "JioMart", "price": 46998 },
    { "platform": "amazon.in", "price": 62999 }
  ],
  "next_sale": { "name": "Independence Day Sale", "start_date": "2026-08-08", "platform": "Amazon / Flipkart" },
  "stackable_discounts": [
    { "type": "bank_offer", "description": "10% off with HDFC Credit Card", "estimated_saving_inr": 1500 }
  ],
  "signal_summaries": [
    { "signal": "fake_discount", "vote": "buy_now", "plain_reason": "The price is about its usual level, neither high nor low." },
    { "signal": "cross_platform", "vote": "buy_now", "plain_reason": "Flipkart is cheapest right now." },
    { "signal": "price_trend", "vote": "wait", "plain_reason": "The price has been trending upward." },
    { "signal": "days_to_next_sale", "vote": "wait", "plain_reason": "A relevant sale is coming, with bank offers attached." },
    { "signal": "category_elasticity", "vote": "wait", "plain_reason": "Smartphones typically drop 18-35% in sales." },
    { "signal": "news_shock", "vote": null, "plain_reason": "No relevant news shock detected." }
  ]
}
```

## Performance Characteristics

- **Cold start:** the free Render tier sleeps after ~15 minutes idle; first request after sleep takes ~30-50s to wake (a keep-alive ping to `/api/health` via UptimeRobot avoids this)
- **Cached repeat search:** ~2.6s (measured) vs. ~14.5s for a fresh live fetch
- **Frontend payload:** ~2 kB gzipped CSS, no web fonts, no image assets on first load, suitable for a mid-range Android phone on slow 4G
- **Rate limits:** 10 req/min/IP on `/api/analyse`, 30 req/min/IP on watchlist writes, 5 req/min/IP on signup

## Challenges Faced

- **Grey-market and accessory prices winning "best price."** Google Shopping mixes accessories, wrong model variants, and refurbished listings into the same results as the real product; solved with a multi-stage filter (accessory keywords, condition keywords, model-variant matching, trusted-seller allowlist, statistical outlier floor).
- **Missing MRP data.** Most live shopping results carry no explicit MRP; the fake-discount signal was redesigned to use the strikethrough "was" price when present, Google's own deal badge, and the product's own historical median as a three-way fallback chain.
- **Category gaps.** A fixed keyword list cannot cover every product; unmatched products now get a single cached Gemini classification call so the category-elasticity signal works for the whole catalogue.
- **Free-tier quota management.** SerpAPI's 100 searches/month is easy to exhaust; solved with a 6-hour in-memory result cache and a capped daily background refresh (3 recent products/day) instead of refreshing everything.
- **Deploying without a card.** Render requires payment details for Blueprint deployments and cron jobs; solved by deploying as a plain free web service and moving the scheduled job to GitHub Actions instead.
- **Auth without over-collecting data.** Balancing "no personal data" against needing accounts for a cross-device watchlist; resolved by collecting only an email and password (handled entirely by Supabase Auth, no verification email required).

## Future Enhancements / Roadmap

- Add more live price sources (direct Apify actors) to reduce reliance on a single free-tier API
- Track a genuine "lowest price ever seen" per product once history has accumulated for longer
- Expand the trusted-seller and category-elasticity tables from real usage data
- Add optional email notifications for price-drop alerts (currently in-app only)
- Capture and commit demo screenshots to `docs/DEMO_SCREENSHOTS/`
- Consider passwordless (magic-link) sign-in as a lighter alternative to passwords

## License

Released under the [MIT License](LICENSE).

---

## Security Notes

- All API keys live server-side; the frontend ships only client-safe values
- Watchlist identity comes exclusively from the verified Supabase token; client-supplied ids are ignored
- Signup is rate limited, validates email and password server-side, and returns one generic failure message (no account enumeration)
- CORS is locked to the deployed frontend origin; all DB access is parameterised; no `SELECT *`
- External buy links are protocol-sanitised before rendering
- Passwords are handled entirely by Supabase Auth and never touch this codebase

## What This App Deliberately Does Not Do

- Does not predict an exact future price; it states evidenced probabilities, not guarantees
- Does not accept vague, unbranded queries; a brand is required for an honest answer
- Does not give financial or investment advice
- Does not store personal data beyond the sign-in email and the user's own watchlist
- Does not auto-place orders or touch marketplace accounts

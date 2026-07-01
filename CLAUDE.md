# CLAUDE.md - Smart Price Advisor

Standing instructions for this project. Claude Code reads this every session. Follow it for every task.

## What this project is

Smart Price Advisor is an evidence-based shopping intelligence web app for Indian consumers ("Buy Now or Wait?"). A user enters a branded product and how long they are willing to wait. The app analyses the live price against price history, the upcoming sale calendar, and live market news, then returns a clear verdict, Buy Now or Wait, with a confidence band (High, Medium or Low, never a false-precise percentage), the best price available right now, where to buy it, stackable discounts that lower it further, and how long to wait for the likely best deal.

Core principle: the verdict is always backed by live, verifiable data, never a confident guess from memory. Every signal used must be reliably available and directly relevant to the timing decision. Nothing decorative is included. An inconsistent signal makes the confidence less trustworthy. Confidence is shown as a band (High, Medium, Low), not a percentage, because a precise number invites doubt and implies false accuracy.

Target users: Indian consumers buying branded goods online who want honest advice on whether to buy today or wait for a genuine price drop.

## Working rules (read first) - IMPORTANT

These are the user's personal requests. They are IMPORTANT and non-negotiable. Do not skip, shortcut, or forget them, even under time pressure or when a change looks trivial.

1. Ask before creating any new file. When a step needs a new file, first state the path, what the file does in one line, and how it fits, then wait for the user's go-ahead before writing it.
2. Explain any API integration before writing its code. For Apify, SerpAPI, NewsAPI, Gemini, data.gov.in and Supabase, walk through how the integration works (auth, endpoint, request and response shape, cost and rate limits, fallback) and only start the code after the user is happy.

## Writing and style rules (apply to ALL output)

- NEVER use em dashes anywhere. Not in UI copy, code comments, file headers, commit messages, AI system prompts, or AI-generated text. Use a comma, a period, parentheses, or a plain hyphen with spaces instead. Non-negotiable.
- Every clickable element must use cursor: pointer. Disabled controls use cursor: not-allowed.
- Every interactive element (button, card, nav item, list row) must have a visible hover state. Use lift plus shadow: the element rises a couple px with a soft shadow on hover and presses down on click.
- The app must be fully usable on a mid-range Android phone on a slow 4G connection. No heavy assets on initial load.
- All error messages are in plain language. Never show a technical error to the user.
- Loading states always show something useful. Never a blank screen.

## Tech stack (exact, do not deviate)

- Frontend: React (Vite), deployed on Vercel
- Backend: Python (FastAPI), deployed on Render
- Database: Supabase (PostgreSQL), price history and watchlists
- Price data: Apify actors (Amazon India, Flipkart) for price and MRP; SerpAPI / Google Shopping fallback; data.gov.in for groceries and fuel (by city)
- News data: NewsAPI (free tier), real-time Indian market news
- AI analysis: Gemini API (free tier), synthesises signals into a verdict
- Scheduled jobs: Cron job on Render, price snapshots for watchlisted products
- Version control: GitHub
- Package managers: pip (backend), npm (frontend)

## Environment variables

Backend only, never expose to the client: SUPABASE_SERVICE_ROLE_KEY, APIFY_API_TOKEN, SERPAPI_KEY, NEWSAPI_KEY, GEMINI_API_KEY.
Shared / client-safe: SUPABASE_URL, SUPABASE_ANON_KEY.
Frontend: VITE_API_BASE_URL (points to the Render backend URL).

All keys live server-side only. Set them in the Vercel and Render dashboards, never in code.

## The analysis engine (six signals)

The verdict is a weighted scoring model. Each signal votes Buy Now or Wait with a weight. Gemini synthesises them into one evidenced recommendation. The confidence band (High, Medium, Low) reflects how strongly the signals agree and how many actually voted. When many signals agree, confidence is High. When they split or few voted, it is Medium or Low, and honestly reported. Never a percentage.

Each signal returns: { signal_name, vote ("buy_now" | "wait"), weight, reason }.

1. Fake-discount check. Compare the live price against the listed MRP and against the app's own stored median price for that product. Exposes pre-sale inflation. Source: Apify actors.
2. Cross-platform best price. Check the same product across major Indian platforms. Identify the cheapest source right now with a direct buy link.
3. Price-history trend. Store a snapshot on every lookup in Supabase. Measure direction (rising or falling) and volatility. A falling or widely swinging price makes waiting more rewarding.
4. Days-to-next-sale. A deterministic database of known Indian sales (Amazon Great Indian Festival, Flipkart Big Billion Days, Nykaa Pink Friday, Myntra EORS), mapped to categories with associated bank-card offers. A fact, not a guess. Weighted heavily.
5. Category elasticity. A rule table of how much each category actually moves during sales (electronics fall sharply, staples barely move). Prevents nonsensical advice.
6. News-shock detector. NewsAPI signals for export bans, successor-product launches, currency moves. For groceries and fuel, data.gov.in feeds. A strong shock can override the historical pattern.

Fallback rule: when a scraping source is temporarily unavailable, fall back to a Google Shopping price or a direct search link so a verdict can always be produced. Never return an error when a fallback exists.

## How prices are sourced

Marketplaces block automated scraping. Only use legitimate sources.

- Branded goods: live price and MRP via Apify actors, direct buy links included. Not limited to Amazon and Flipkart: the client supports all trusted Indian marketplaces (Amazon India, Flipkart, Croma, Reliance Digital, Tata CLiQ, Vijay Sales, Myntra, Ajio, Nykaa, JioMart, Snapdeal, Meesho) via an Apify actor where one exists, with SerpAPI Google Shopping covering platforms that do not have a dedicated actor. Ships with built-in mock data for a few demo products so the flow works before real actor IDs are configured.
- Groceries and fuel: official daily data from data.gov.in, filtered by the user's city.
- Fallback (no API returns a price): show a direct Amazon or Flipkart search link. Never show a guessed number.

## Watchlist behaviour (collapsible side panel)

The watchlist is a persistent, collapsible side panel like the Claude sidebar: always reachable, minimise and reopen on demand.

- On open, show each watched item with its current lowest price.
- Do not re-check on every open. Throttle to at most once per day even if the user opens it many times. Serve the cached price the rest of the time, using a last-checked timestamp.
- Notify when an item hits the predicted lowest / target price, OR drops a meaningful amount below the last price the user saw.
- Notifications are in-app, shown on the next visit (a banner / badge on the side panel). No email or browser push in v1, consistent with the no-auth, no-personal-data scope.
- On a drop, re-run the verdict and advise buy now or keep waiting. Example: a phone first seen at Rs 44,000 with a "wait 3 months" verdict, reopened a month later at Rs 38,000, triggers a notification and a fresh buy-vs-wait decision.

### Meaningful-drop threshold (adaptive, not a flat percent)

A fixed percent is wrong: 3% of an expensive phone is a real deal, 5% of a cheap book is noise. The threshold adapts to category and price band.

Notify when: drop_amount >= max(category_pct x last_seen_price, price_band_floor), OR target / predicted-low is reached.

Category percentage (reuses the Signal 5 elasticity category list, one source of truth):
- smartphones, laptops, televisions, large_appliances: 3%
- small_appliances, beauty_skincare: 5%
- fashion_clothing: 8% (deep-sale, noisy category)
- books: 10%
- grocery_staples, fuel: target only, do not fire a meaningful-drop alert

Absolute rupee floor by price band (prevents trivial alerts even when the percent clears):
- under Rs 1,000: Rs 50
- Rs 1,000 to Rs 10,000: Rs 300
- Rs 10,000 to Rs 50,000: Rs 1,000
- over Rs 50,000: Rs 2,000

Example: a Rs 80,000 phone fires at a Rs 2,400 drop (3%); a Rs 400 book needs a 10% move and must still clear the Rs 50 floor.

## Build phases (strict order)

Phase 1, backend, data and analysis engine: a FastAPI backend that accepts a product query and returns a fully scored verdict backed by live data. No frontend yet. Test via Swagger UI or curl. Covers Supabase schema, Apify integration, NewsAPI integration, the six signals plus aggregator, FastAPI routes, and the sale-calendar seed.

Phase 2, React frontend and deployment: search screen, verdict screen, watchlist side panel, error and edge-case states, deployment to Vercel and Render.

## FastAPI routes

- POST /api/analyse. Body: { product: string, wait_tolerance_days: number }. Returns the full verdict object.

Wait-tolerance input (WaitTolerancePicker): the user either picks a preset from a dropdown or types a custom number of days. Presets map to days: 1 week = 7, 1 month = 30, 3 months = 90, 6 months = 180, 1 year = 365. The value sent to the API is always wait_tolerance_days.
- POST /api/watchlist. Body: { product_id, target_price, session_id }.
- GET /api/watchlist/{session_id}. Returns watched products with latest prices.
- DELETE /api/watchlist/{session_id}/{product_id}.

Verdict object fields: verdict, confidence ("High" | "Medium" | "Low"), summary_reason, wait_estimate (days, null if Buy Now), best_price (INR), best_platform, buy_link, stackable_discounts [{ type, description, estimated_saving }], next_sale (null or { name, start_date, platform }), price_vs_median (percent above or below stored median).

## Database schema (Supabase / PostgreSQL)

products: id uuid PK default gen_random_uuid(), name text NOT NULL, brand text, category text, asin text, flipkart_pid text, created_at timestamptz default now().

price_snapshots (append-only, never update or delete): id uuid PK, product_id uuid FK products.id, platform text NOT NULL ('amazon' | 'flipkart' | 'serpapi'), price numeric(10,2) NOT NULL, mrp numeric(10,2), recorded_at timestamptz default now().

sale_calendar (seeded manually, update quarterly): id uuid PK, sale_name text NOT NULL, platform text NOT NULL, category_tags text[], start_date date NOT NULL, end_date date NOT NULL, bank_offers jsonb [{ bank, card_type, discount_pct, cap_inr }].

watchlist_items: id uuid PK, session_id text NOT NULL, product_id uuid FK products.id, target_price numeric(10,2), notified boolean default false, purchased boolean default false, purchased_at timestamptz, created_at timestamptz default now(). The user can remove an item or mark it as bought (purchased).

news_cache: id uuid PK, product_id uuid FK products.id, headlines jsonb, cached_at timestamptz default now(), expires_at timestamptz (cached_at + 1 hour).

No user auth in v1. Watchlists are tied to a random client-side UUID session ID stored in the browser.

## File structure

backend: main.py; routers/ (analyse.py, watchlist.py); services/ (apify_client.py, serpapi_client.py, newsapi_client.py, data_gov_client.py, gemini_client.py); signals/ (fake_discount.py, cross_platform.py, price_trend.py, days_to_sale.py, category_elasticity.py, news_shock.py, aggregator.py); db/ (supabase_client.py, price_snapshots.py, sale_calendar.py, watchlist.py, products.py); seeds/ (sale_calendar_seed.py); data/ (category_elasticity.json); requirements.txt; .env.example.

frontend/src: components/ (SearchBar, WaitTolerancePicker, VerdictCard, ActionStrip, StackableDiscounts, SignalBreakdown, WatchlistButton, PriceSparkline, WatchlistPanel, AlertBanner, ErrorState, LoadingState); hooks/ (useAnalyse, useWatchlist); utils/ (session, formatting); App.tsx, main.tsx, index.html, vite.config.ts, package.json, .env.example.

docs: README.md, DEMO_SCREENSHOTS/.

## Gemini prompt spec

The Gemini call receives the output of all six signals and synthesises one consumer-friendly verdict.

System prompt must: instruct Gemini to reason over the provided signal data only and not use its own memory of prices (stale); require a verdict backed by the signals, never a guess; specify the output format; return ONLY valid JSON, no preamble, no markdown.

Output JSON schema: { "verdict": "Buy Now" | "Wait", "confidence": "High" | "Medium" | "Low", "summary_reason": "one sentence, plain English", "wait_estimate_days": null | number, "stackable_discounts": [{ "type": "bank_offer" | "coupon" | "gift_card", "description": string, "estimated_saving_inr": number }], "signal_summaries": [{ "signal": string, "vote": "buy_now" | "wait", "plain_reason": string }] }.

User message to Gemini: Product, Category, Signal results (JSON array), News headlines (last 7 days), User's wait tolerance (days).

## Category elasticity table

Stored in backend/data/category_elasticity.json. Each entry: { category, typical_sale_drop_pct, worth_waiting (bool) }.

Key entries: smartphones 18-35% true; laptops 10-25% true; televisions 15-30% true; large_appliances 10-20% true; small_appliances 5-15% true; fashion_clothing 30-70% true; beauty_skincare 20-40% true; grocery_staples 0-5% false; fuel 0% false; books 5-10% false. Populate the rest from domain knowledge.

## Sale calendar seed

Seed sale_calendar with at least: Amazon Great Indian Festival (Oct), Flipkart Big Billion Days (Oct), Nykaa Pink Friday (Nov), Myntra End of Reason Sale (Jun, Dec), Republic Day sales (Jan), Independence Day sales (Aug). Each entry includes commonly associated bank offers and a category mapping of which categories see major drops.

## What the app does NOT do

- Does not predict an exact future price. It states evidenced probabilities, not guarantees.
- Does not handle vague or unbranded queries. A brand name is required.
- Does not give financial or investment advice.
- Does not store personal data beyond a session-scoped watchlist.
- Does not auto-place orders or interact with marketplace accounts.

## Security requirements

- All API keys live server-side only. Never in frontend code.
- CORS in production: allow only the deployed Vercel URL. In development: allow localhost:5173.
- Rate limit POST /api/analyse: 10 req/min/IP. Apify and Gemini have per-call costs, protect them.
- Never SELECT *. Always name columns in DB queries.
- All DB writes use parameterised queries via the Supabase client.
- Watchlist session IDs are random UUIDs generated client-side. No session ID should be predictable.
- Validate all inputs server-side: product string max 200 chars, must not be empty; wait_tolerance_days integer 1-365 only (presets 7, 30, 90, 180, 365, or a custom value in range).

## Workflow (same for every feature)

1. THINK. Surface tradeoffs, alternatives, hidden constraints before writing any code.
2. PLAN. Numbered tasks, dependencies, files touched, success criteria, what "done" looks like.
3. STOP AND SHOW. Present the full plan. Do not write application code until the user types "approved" or "go". Revise if requested, show again, repeat until approved.
4. BUILD. Complete one task at a time. Never batch unrelated changes.
5. VERIFY. After each route or component, test it. Backend: curl or Swagger UI. Frontend: browser plus mobile viewport. Do not move on if the current task is not working.
6. SECURITY CHECK. At the end of each phase, run a security review. Fix all Critical and High findings before the next phase. Format findings as: Severity | Issue | File:Line | Fix.
7. COMMIT GATE. List changed files. Write a commit message. Stop and wait for "commit" before running git commit. Never auto-commit.

## Skills - mandatory invocation

These are not optional. The listed skill MUST be invoked before proceeding with the associated task. Skipping a skill invocation is a violation of these rules.

Before any UI component or screen:
1. /ui-ux-pro-max - layout, spacing, accessibility, interaction patterns
2. /frontend-design - color, typography, component hierarchy

Before any auth, upload, or payment route:
3. /secure-code-guardian - threat model plus security contract before writing the route

When planning any feature (before coding):
4. /superpowers-brainstorming - surface alternatives and hidden constraints first
5. /superpowers-writing-plans - produce a numbered plan; do not write code until the plan is approved

End of every phase (before commit):
6. /vibe-security - full security scan; fix ALL Critical and High findings before moving to the next phase. Format: Severity | Issue | File:Line | Fix

When something is broken or behaving unexpectedly:
7. /superpowers-systematic-debugging - diagnose root cause before attempting any fix

When writing or reviewing complex logic:
8. /superpowers-advanced-reasoning - use for check algorithms, risk scoring, parsing edge cases

When producing user-facing copy, labels, or error messages:
9. /superpowers-writing - consistent tone, no jargon, clear action guidance

Enforcement rule: if a trigger condition above is met and the corresponding skill was NOT invoked, stop, invoke it, incorporate the output, then continue.

## CI/CD (after every push)

Run tsc --noEmit, pytest, and docker-compose build to catch breakage early.

## File comment block (every file touched)

Every file gets this block. If it already has the block, update CHANGES only. No file is committed without it.

```
"""
FILE: [path from root]

WHAT THIS DOES:
[Single responsibility of this file]

CHANGES THIS SESSION:
- [change 1]
- [change 2]

WHERE IT FITS:
[How it connects to the rest of the project]

CALLED BY / IMPORTS FROM:
[Key consumers or dependencies]
"""
```

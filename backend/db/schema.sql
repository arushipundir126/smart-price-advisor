-- FILE: backend/db/schema.sql
--
-- WHAT THIS DOES:
-- Creates the five tables Smart Price Advisor needs. Run this once by hand in
-- the Supabase SQL Editor (paste, then Run).
--
-- CHANGES THIS SESSION:
-- - Initial schema: products, price_snapshots, sale_calendar, watchlist_items,
--   news_cache, with foreign keys and indexes.
-- - Added watchlist_items.wait_tolerance_days (drives the adaptive re-check
--   cadence), with a safe ALTER for tables created before this column.
--
-- WHERE IT FITS:
-- The database foundation. The db/ Python files read from and write to these
-- tables through db/supabase_client.py.
--
-- CALLED BY / IMPORTS FROM:
-- Run manually in Supabase. Not imported by Python.

-- Products: one row per branded product we have looked up.
create table if not exists products (
    id            uuid primary key default gen_random_uuid(),
    name          text not null,
    brand         text,
    category      text,
    asin          text,
    flipkart_pid  text,
    created_at    timestamptz not null default now()
);

-- Price snapshots: APPEND ONLY. Every lookup adds one row per platform.
-- Never update or delete rows here; the history is the whole point.
create table if not exists price_snapshots (
    id           uuid primary key default gen_random_uuid(),
    product_id   uuid not null references products (id) on delete cascade,
    platform     text not null,          -- 'amazon' | 'flipkart' | 'serpapi'
    price        numeric(10, 2) not null,
    mrp          numeric(10, 2),
    currency     text not null default 'INR',
    recorded_at  timestamptz not null default now()
);

-- Fast lookup of a product's most recent prices.
create index if not exists idx_price_snapshots_product_recorded
    on price_snapshots (product_id, recorded_at desc);

-- Sale calendar: seeded by hand from known Indian sales. Updated quarterly.
create table if not exists sale_calendar (
    id             uuid primary key default gen_random_uuid(),
    sale_name      text not null,
    platform       text not null,
    category_tags  text[],
    start_date     date not null,
    end_date       date not null,
    bank_offers    jsonb                 -- [{ bank, card_type, discount_pct, cap_inr }]
);

-- Fast lookup of upcoming sales by date.
create index if not exists idx_sale_calendar_start
    on sale_calendar (start_date);

-- Watchlist: session-scoped, no user auth in v1.
create table if not exists watchlist_items (
    id            uuid primary key default gen_random_uuid(),
    session_id    text not null,
    product_id    uuid not null references products (id) on delete cascade,
    target_price  numeric(10, 2),
    notified            boolean not null default false,
    purchased           boolean not null default false,   -- user marked it as bought
    purchased_at        timestamptz,                       -- when they bought it
    wait_tolerance_days integer,                           -- drives re-check cadence
    created_at          timestamptz not null default now(),
    -- One watch per product per session; re-adding updates the same row.
    unique (session_id, product_id)
);

-- Fast lookup of everything a session is watching.
create index if not exists idx_watchlist_session
    on watchlist_items (session_id);

-- If watchlist_items existed before these columns, add them safely.
alter table watchlist_items add column if not exists purchased boolean not null default false;
alter table watchlist_items add column if not exists purchased_at timestamptz;
alter table watchlist_items add column if not exists wait_tolerance_days integer;

-- News cache: raw NewsAPI results kept for one hour to save API quota.
create table if not exists news_cache (
    id          uuid primary key default gen_random_uuid(),
    product_id  uuid not null references products (id) on delete cascade,
    headlines   jsonb,
    cached_at   timestamptz not null default now(),
    expires_at  timestamptz not null
);

-- Fast lookup of fresh (non-expired) cache for a product.
create index if not exists idx_news_cache_product_expires
    on news_cache (product_id, expires_at);

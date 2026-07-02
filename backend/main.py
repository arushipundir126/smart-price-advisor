"""
FILE: backend/main.py

WHAT THIS DOES:
FastAPI application entry point. Configures CORS, sets up the rate limiter,
exposes a health check, and mounts the API routers.

CHANGES THIS SESSION:
- Created the app with CORS (single allowed frontend origin), a /api/health
  route, and the analyse router mounted (walking skeleton).
- Moved the rate limiter into limiter.py and imported it here.

WHERE IT FITS:
This is what uvicorn runs on Render. It is the front door for every API route.

CALLED BY / IMPORTS FROM:
Run via `uvicorn main:app`. Imports routers.analyse. Reads FRONTEND_ORIGIN from
the environment for CORS.
"""
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from limiter import limiter
from routers import analyse, watchlist

load_dotenv()

app = FastAPI(title="Smart Price Advisor API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: allow only the configured frontend origin(s).
# Dev default is the Vite dev server. In prod set FRONTEND_ORIGIN to the Vercel
# URL. Multiple origins can be given as a comma-separated list (for example the
# stable production domain plus a custom domain).
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
allowed_origins = [o.strip() for o in frontend_origin.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyse.router)
app.include_router(watchlist.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}

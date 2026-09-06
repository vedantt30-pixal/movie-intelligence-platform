import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Make the repo root importable regardless of where this process is
# launched from. Without this, `uvicorn backend.main:app` (run from
# the repo root) works, but `cd backend && uvicorn main:app` fails
# with `ModuleNotFoundError: No module named 'src'` — confirmed by
# actually running both, not just assumed.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.recommendation_engine import MovieRecommendationEngine

# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("movie_intelligence")


# ============================================================
# Environment
# ============================================================

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not TMDB_API_KEY:
    raise RuntimeError(
        "TMDB_API_KEY is missing. Check your .env file."
    )

TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# Comma-separated list, e.g. "https://myapp.vercel.app,http://localhost:5173"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]

# Data paths resolved relative to this file, not the process's cwd —
# so it doesn't matter whether you launch uvicorn from the repo root,
# from backend/, or from a deploy platform's arbitrary working dir.
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
MOVIES_PATH = DATA_DIR / "tmdb_5000_movies.csv"
CREDITS_PATH = DATA_DIR / "tmdb_5000_credits.csv"

POSTER_FETCH_WORKERS = int(os.getenv("POSTER_FETCH_WORKERS", "8"))
POSTER_FETCH_TIMEOUT = (5, 10)  # (connect, read) seconds, per attempt


# ============================================================
# API Response Models
# ============================================================

class Recommendation(BaseModel):
    id: int
    title: str
    vote_average: float = Field(ge=0, le=10)
    popularity: float = Field(ge=0)
    similarity_score: float = Field(ge=0)
    poster_url: str | None = None


class RecommendationResponse(BaseModel):
    movie: str
    recommendations: list[Recommendation]


# ============================================================
# FastAPI
# ============================================================

app = FastAPI(
    title="Movie Intelligence API",
    description="Movie recommendation API powered by TF-IDF similarity",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Recommendation Engine
# ============================================================

logger.info("Loading recommendation engine from %s", DATA_DIR)
engine = MovieRecommendationEngine(
    movies_path=str(MOVIES_PATH),
    credits_path=str(CREDITS_PATH),
)
logger.info("Recommendation engine ready (%d movies)", len(engine.df))


# ============================================================
# TMDB HTTP Session
# ============================================================
#
# A single retry layer, not two. urllib3's Retry already respects
# the Retry-After header on 429 responses by default, so a manual
# retry-and-sleep loop on top of it was pure duplication that could
# multiply worst-case latency by up to 3x for no benefit.
# ============================================================

session = requests.Session()

retry_strategy = Retry(
    total=3,
    connect=2,
    read=2,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
    respect_retry_after_header=True,
)

adapter = HTTPAdapter(
    max_retries=retry_strategy,
    pool_connections=POSTER_FETCH_WORKERS,
    pool_maxsize=POSTER_FETCH_WORKERS,
)

session.mount("https://", adapter)
session.mount("http://", adapter)

session.headers.update(
    {
        "User-Agent": "MovieIntelligencePlatform/1.0",
        "Accept": "application/json",
    }
)


# ============================================================
# Poster Cache
#
# We only cache successful poster URLs, never None — a transient
# TMDB/network failure should be retried on the next request rather
# than permanently sticking as "no poster". A lock guards writes
# since poster fetches now run concurrently across threads.
# ============================================================

poster_cache: dict[int, str] = {}
poster_cache_lock = Lock()


def tmdb_get(url: str, params: dict) -> dict | None:
    """Single-attempt-with-adapter-retries TMDB GET. Returns JSON or None."""
    try:
        response = session.get(url, params=params, timeout=POSTER_FETCH_TIMEOUT)
    except requests.RequestException as exc:
        logger.warning("TMDB request failed for %s: %s", url, exc)
        return None

    if response.status_code == 200:
        return response.json()

    logger.warning("TMDB returned HTTP %s for %s", response.status_code, url)
    return None


def get_poster_url(movie_id: int, title: str | None = None) -> str | None:
    """
    Find a poster for a movie.

    Order: in-memory cache -> TMDB movie/{id} -> TMDB search/movie by title.
    Only successful URLs are cached.
    """
    cache_key = int(movie_id)

    with poster_cache_lock:
        cached = poster_cache.get(cache_key)
    if cached:
        return cached

    movie_data = tmdb_get(
        f"{TMDB_API_BASE_URL}/movie/{movie_id}",
        {"api_key": TMDB_API_KEY, "language": "en-US"},
    )

    if movie_data:
        poster_path = movie_data.get("poster_path")
        if poster_path:
            poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}"
            with poster_cache_lock:
                poster_cache[cache_key] = poster_url
            return poster_url

    if title:
        search_data = tmdb_get(
            f"{TMDB_API_BASE_URL}/search/movie",
            {
                "api_key": TMDB_API_KEY,
                "query": title,
                "include_adult": False,
                "language": "en-US",
            },
        )

        if search_data:
            results = search_data.get("results", [])
            normalized_title = title.lower().strip()

            # Prefer an exact title match; fall back to first result with a poster.
            exact = next(
                (
                    r for r in results
                    if r.get("poster_path")
                    and r.get("title", "").lower().strip() == normalized_title
                ),
                None,
            )
            best = exact or next((r for r in results if r.get("poster_path")), None)

            if best:
                poster_url = f"{TMDB_IMAGE_BASE_URL}{best['poster_path']}"
                with poster_cache_lock:
                    poster_cache[cache_key] = poster_url
                return poster_url

    logger.info("No poster found for movie_id=%s title=%r", movie_id, title)
    return None


def attach_posters(movies: list[dict]) -> None:
    """
    Fetch posters for all recommended movies concurrently instead of
    one-by-one. With N recommendations and up to POSTER_FETCH_WORKERS
    in flight at once, worst-case latency is bounded by the slowest
    single TMDB call rather than by N sequential calls.
    """
    if not movies:
        return

    with ThreadPoolExecutor(max_workers=min(POSTER_FETCH_WORKERS, len(movies))) as pool:
        future_to_movie = {
            pool.submit(get_poster_url, int(m["id"]), m["title"]): m
            for m in movies
        }
        for future in as_completed(future_to_movie):
            movie = future_to_movie[future]
            try:
                movie["poster_url"] = future.result()
            except Exception as exc:  # a single poster failure shouldn't break the response
                logger.warning("Poster fetch failed for %s: %s", movie.get("title"), exc)
                movie["poster_url"] = None


# ============================================================
# Root Endpoint
# ============================================================

@app.get("/")
def root():
    return {"message": "Movie Intelligence API is running"}


@app.get("/health")
def health():
    return {"status": "ok", "movies_loaded": len(engine.df)}


# ============================================================
# Recommendations Endpoint
# ============================================================

@app.get(
        "/recommendations/{title}",
        response_model=RecommendationResponse,
        )
def get_recommendations(
    title: str,
    n: int = Query(default=10, ge=1, le=50),
    diversify: bool = Query(default=True, description="Filter out same-franchise duplicates"),
):
    recommendations = engine.get_recommendations(title=title, n=n, diversify=diversify)

    if recommendations.empty:
        raise HTTPException(status_code=404, detail=f"Movie '{title}' not found")

    recommendation_list = recommendations.to_dict(orient="records")
    attach_posters(recommendation_list)

    return {
        "movie": title,
        "recommendations": recommendation_list,
    }
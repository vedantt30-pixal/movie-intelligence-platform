from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.recommendation_engine import MovieRecommendationEngine


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
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Recommendation Engine
# ============================================================

engine = MovieRecommendationEngine(
    movies_path="data/raw/tmdb_5000_movies.csv",
    credits_path="data/raw/tmdb_5000_credits.csv",
)


# ============================================================
# TMDB HTTP Session
# ============================================================

session = requests.Session()

retry_strategy = Retry(
    total=3,
    connect=3,
    read=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)

adapter = HTTPAdapter(
    max_retries=retry_strategy,
    pool_connections=10,
    pool_maxsize=10,
)

session.mount("https://", adapter)
session.mount("http://", adapter)

session.headers.update(
    {
        "User-Agent": "MovieIntelligencePlatform/1.0",
        "Accept": "application/json",
        "Connection": "keep-alive",
    }
)


# ============================================================
# Poster Cache
#
# IMPORTANT:
# We only cache successful poster URLs.
# We DO NOT cache None.
#
# This means a temporary TMDB/network failure can recover
# on the next request instead of permanently becoming null.
# ============================================================

poster_cache = {}


# ============================================================
# TMDB Request Helper
# ============================================================

def tmdb_get(url, params):
    """
    Make a reliable TMDB GET request.

    Retries transient connection failures several times.
    Returns JSON data on success, otherwise None.
    """

    for attempt in range(3):

        try:

            response = session.get(
                url,
                params=params,
                timeout=(5, 15),
            )

            if response.status_code == 200:
                return response.json()

            # Rate limited
            if response.status_code == 429:

                retry_after = response.headers.get(
                    "Retry-After",
                    "2"
                )

                try:
                    sleep_time = min(
                        int(retry_after),
                        10
                    )
                except ValueError:
                    sleep_time = 2

                print(
                    f"TMDB rate limit reached. "
                    f"Waiting {sleep_time}s..."
                )

                time.sleep(sleep_time)
                continue

            print(
                f"TMDB returned HTTP "
                f"{response.status_code} "
                f"for {url}"
            )

        except requests.RequestException as e:

            print(
                f"TMDB request attempt "
                f"{attempt + 1}/3 failed: {e}"
            )

            if attempt < 2:
                time.sleep(1 + attempt)

    return None


# ============================================================
# TMDB Poster Helper
# ============================================================

def get_poster_url(movie_id: int, title: str = None):
    """
    Find a poster for a movie.

    Order:
        1. In-memory cache
        2. TMDB movie/{id}
        3. TMDB search/movie by title

    Only successful URLs are cached.
    """

    cache_key = int(movie_id)

    # --------------------------------------------------------
    # 1. Cache
    # --------------------------------------------------------

    if cache_key in poster_cache:

        print(
            f"Poster cache hit: "
            f"{movie_id} - {title}"
        )

        return poster_cache[cache_key]

    # --------------------------------------------------------
    # 2. Direct TMDB ID lookup
    # --------------------------------------------------------

    movie_url = (
        f"{TMDB_API_BASE_URL}/movie/{movie_id}"
    )

    movie_data = tmdb_get(
        movie_url,
        {
            "api_key": TMDB_API_KEY,
            "language": "en-US",
        },
    )

    if movie_data:

        poster_path = movie_data.get(
            "poster_path"
        )

        if poster_path:

            poster_url = (
                f"{TMDB_IMAGE_BASE_URL}"
                f"{poster_path}"
            )

            poster_cache[cache_key] = poster_url

            print(
                f"Poster found by ID: "
                f"{movie_id} - {title}"
            )

            return poster_url

        print(
            f"TMDB movie has no poster: "
            f"{movie_id} - {title}"
        )

    # --------------------------------------------------------
    # 3. Search by title
    # --------------------------------------------------------

    if title:

        search_url = (
            f"{TMDB_API_BASE_URL}/search/movie"
        )

        search_data = tmdb_get(
            search_url,
            {
                "api_key": TMDB_API_KEY,
                "query": title,
                "include_adult": False,
                "language": "en-US",
            },
        )

        if search_data:

            results = search_data.get(
                "results",
                []
            )

            # First try an exact title match
            for result in results:

                result_title = result.get(
                    "title",
                    ""
                )

                poster_path = result.get(
                    "poster_path"
                )

                if (
                    poster_path
                    and result_title.lower().strip()
                    == title.lower().strip()
                ):

                    poster_url = (
                        f"{TMDB_IMAGE_BASE_URL}"
                        f"{poster_path}"
                    )

                    poster_cache[cache_key] = poster_url

                    print(
                        f"Poster found by exact title: "
                        f"{title}"
                    )

                    return poster_url

            # If exact match wasn't found,
            # accept the first result that has a poster.
            for result in results:

                poster_path = result.get(
                    "poster_path"
                )

                if poster_path:

                    poster_url = (
                        f"{TMDB_IMAGE_BASE_URL}"
                        f"{poster_path}"
                    )

                    poster_cache[cache_key] = poster_url

                    print(
                        f"Poster found by title search: "
                        f"{title}"
                    )

                    return poster_url

    # --------------------------------------------------------
    # No poster
    #
    # IMPORTANT:
    # Do NOT cache None.
    # A temporary network failure should be retried later.
    # --------------------------------------------------------

    print(
        f"No poster found: "
        f"{movie_id} - {title}"
    )

    return None


# ============================================================
# Root Endpoint
# ============================================================

@app.get("/")
def root():

    return {
        "message": "Movie Intelligence API is running"
    }


# ============================================================
# Recommendations Endpoint
# ============================================================

@app.get("/recommendations/{title}")
def get_recommendations(
    title: str,
    n: int = 10,
):

    if n < 1 or n > 50:

        raise HTTPException(
            status_code=400,
            detail="n must be between 1 and 50",
        )

    recommendations = engine.get_recommendations(
        title=title,
        n=n,
    )

    if recommendations.empty:

        raise HTTPException(
            status_code=404,
            detail=f"Movie '{title}' not found",
        )

    recommendation_list = (
        recommendations.to_dict(
            orient="records"
        )
    )

    # --------------------------------------------------------
    # Get posters
    # --------------------------------------------------------

    for movie in recommendation_list:

        movie_id = int(movie["id"])
        movie_title = movie["title"]

        movie["poster_url"] = get_poster_url(
            movie_id,
            movie_title,
        )

    return {
        "movie": title,
        "recommendations": recommendation_list,
    }
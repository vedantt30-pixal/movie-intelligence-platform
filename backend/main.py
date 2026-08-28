from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
import os
import requests

from src.recommendation_engine import MovieRecommendationEngine

# Load environment variables from .env
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
TMDB_API_BASE_URL = "https://api.themoviedb.org/3"

app = FastAPI(
    title="Movie Intelligence API",
    description="Movie recommendation API powered by TF-IDF similarity",
    version="1.0.0"
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


# --------------------------------------------------
# Recommendation Engine
# --------------------------------------------------

engine = MovieRecommendationEngine(
    movies_path="data/raw/tmdb_5000_movies.csv",
    credits_path="data/raw/tmdb_5000_credits.csv"
)


# --------------------------------------------------
# TMDB Poster Helper
# --------------------------------------------------

def get_poster_url(movie_id: int):

    url = f"{TMDB_API_BASE_URL}/movie/{movie_id}"

    params = {
        "api_key": TMDB_API_KEY
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=5
        )

        if response.status_code != 200:
            return None

        data = response.json()

        poster_path = data.get("poster_path")

        if not poster_path:
            return None

        return f"{TMDB_IMAGE_BASE_URL}{poster_path}"

    except requests.RequestException:
        return None


# --------------------------------------------------
# Root Endpoint
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Movie Intelligence API is running"
    }


# --------------------------------------------------
# Recommendation Endpoint
# --------------------------------------------------

@app.get("/recommendations/{title}")
def get_recommendations(title: str, n: int = 10):

    recommendations = engine.get_recommendations(
        title=title,
        n=n
    )

    if recommendations.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Movie '{title}' not found"
        )

    recommendation_list = recommendations.to_dict(
        orient="records"
    )

    for movie in recommendation_list:
        movie["poster_url"] = get_poster_url(movie["id"])

    return {
        "movie": title,
        "recommendations": recommendation_list
    }
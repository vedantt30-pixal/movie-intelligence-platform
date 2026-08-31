import pandas as pd
import pytest

from src.recommendation_engine import MovieRecommendationEngine


MOVIES_PATH = "data/raw/tmdb_5000_movies.csv"
CREDITS_PATH = "data/raw/tmdb_5000_credits.csv"


@pytest.fixture(scope="session")
def engine():
    return MovieRecommendationEngine(
        movies_path=MOVIES_PATH,
        credits_path=CREDITS_PATH
    )


def test_avatar_recommendations(engine):
    result = engine.get_recommendations("Avatar", n=10)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 10
    assert "title" in result.columns
    assert "similarity_score" in result.columns
    assert "Avatar" not in result["title"].values


def test_interstellar_recommendations(engine):
    result = engine.get_recommendations("Interstellar", n=10)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 10
    assert "title" in result.columns
    assert "similarity_score" in result.columns
    assert "Interstellar" not in result["title"].values


def test_dark_knight_recommendations(engine):
    result = engine.get_recommendations("The Dark Knight", n=10)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 10
    assert "The Dark Knight" not in result["title"].values

    assert "The Dark Knight Rises" in result["title"].values


def test_toy_story_recommendations(engine):
    result = engine.get_recommendations("Toy Story", n=10)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 10
    assert "Toy Story" not in result["title"].values

    assert "Toy Story 2" in result["title"].values


def test_unknown_movie_returns_empty_dataframe(engine):
    result = engine.get_recommendations(
        "This Movie Definitely Does Not Exist",
        n=10
    )

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_recommendation_count(engine):
    for n in [1, 5, 10]:
        result = engine.get_recommendations("Avatar", n=n)
        assert len(result) == n


def test_recommendations_are_sorted(engine):
    result = engine.get_recommendations("Avatar", n=10)

    scores = result["similarity_score"].tolist()

    assert scores == sorted(scores, reverse=True)
from src.recommendation_engine import MovieRecommendationEngine


# Paths to the raw TMDB files
movies_path = "data/raw/tmdb_5000_movies.csv"
credits_path = "data/raw/tmdb_5000_credits.csv"


# Create recommendation engine
engine = MovieRecommendationEngine(
    movies_path=movies_path,
    credits_path=credits_path
)

# Test 1: Avatar
print("\n" + "=" * 60)
print("Recommendations for Avatar")
print("=" * 60)

avatar_recommendations = engine.get_recommendations(
    "Avatar",
    n=10
)

print(
    avatar_recommendations[
        [
            "id",
            "title",
            "vote_average",
            "popularity",
            "similarity_score"
        ]
    ].to_string(index=False)
)


# Test 2: Interstellar
print("\n" + "=" * 60)
print("Recommendations for Interstellar")
print("=" * 60)

interstellar_recommendations = engine.get_recommendations(
    "Interstellar",
    n=10
)

print(
    interstellar_recommendations[
        [
            "id",
            "title",
            "vote_average",
            "popularity",
            "similarity_score"
        ]
    ].to_string(index=False)
)
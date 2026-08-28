import ast
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class MovieRecommendationEngine:

    def __init__(self, movies_path, credits_path):

        self.movies_path = movies_path
        self.credits_path = credits_path

        self.movies = None
        self.credits = None
        self.df = None

        self.tfidf = None
        self.tfidf_matrix = None
        self.cosine_sim = None
        self.indices = None

        self._load_data()
        self._prepare_data()
        self._build_model()

    # ==================================================
    # 1. LOAD DATA
    # ==================================================

    def _load_data(self):

        self.movies = pd.read_csv(self.movies_path)
        self.credits = pd.read_csv(self.credits_path)

    # ==================================================
    # 2. PARSE JSON-LIKE COLUMNS
    # ==================================================

    @staticmethod
    def _parse_json_column(value):

        if pd.isna(value):
            return []

        try:
            return ast.literal_eval(value)

        except (ValueError, SyntaxError, TypeError):
            return []

    # ==================================================
    # 3. EXTRACT NAMES
    # ==================================================

    @classmethod
    def _extract_names(cls, value):

        data = cls._parse_json_column(value)

        return [
            item["name"]
            for item in data
            if isinstance(item, dict) and "name" in item
        ]

    # ==================================================
    # 4. EXTRACT TOP CAST
    # ==================================================

    @classmethod
    def _extract_cast(cls, value, limit=5):

        data = cls._parse_json_column(value)

        return [
            item["name"]
            for item in data[:limit]
            if isinstance(item, dict) and "name" in item
        ]

    # ==================================================
    # 5. EXTRACT DIRECTOR
    # ==================================================

    @classmethod
    def _extract_director(cls, value):

        data = cls._parse_json_column(value)

        for item in data:

            if (
                isinstance(item, dict)
                and item.get("job") == "Director"
            ):
                return item.get("name")

        return None

    # ==================================================
    # 6. PREPARE DATA
    # ==================================================

    def _prepare_data(self):

        # ------------------------------
        # Movie features
        # ------------------------------

        self.movies["genres_list"] = (
            self.movies["genres"]
            .apply(self._extract_names)
        )

        self.movies["keywords_list"] = (
            self.movies["keywords"]
            .apply(self._extract_names)
        )

        # ------------------------------
        # Credit features
        # ------------------------------

        self.credits["cast_list"] = (
            self.credits["cast"]
            .apply(self._extract_cast)
        )

        self.credits["director"] = (
            self.credits["crew"]
            .apply(self._extract_director)
        )

        # ------------------------------
        # Merge datasets
        # ------------------------------

        self.df = self.movies.merge(
            self.credits[
                ["movie_id", "cast_list", "director"]
            ],
            left_on="id",
            right_on="movie_id",
            how="inner"
        )

        # ------------------------------
        # Create weighted feature text
        # ------------------------------

        self.df["soup"] = self.df.apply(
            self._create_soup,
            axis=1
        )

        # ------------------------------
        # Movie title → dataframe index
        # ------------------------------

        self.indices = pd.Series(
            self.df.index,
            index=self.df["title"]
        ).drop_duplicates()

    # ==================================================
    # 7. CREATE WEIGHTED FEATURE "SOUP"
    # ==================================================

    @staticmethod
    def _create_soup(row):

        # ------------------------------
        # Genres
        # ------------------------------

        genres = [
            g.replace(" ", "_")
            for g in row["genres_list"]
        ]

        # ------------------------------
        # Keywords
        # ------------------------------

        keywords = [
            k.replace(" ", "_")
            for k in row["keywords_list"]
        ]

        # ------------------------------
        # Cast
        # ------------------------------

        cast = [
            c.replace(" ", "_")
            for c in row["cast_list"]
        ]

        # ------------------------------
        # Director
        # ------------------------------

        director = row["director"]

        if pd.isna(director):
            director = ""
        else:
            director = str(
                director
            ).replace(" ", "_")

        # ------------------------------
        # Overview
        # ------------------------------

        overview = row["overview"]

        if pd.isna(overview):
            overview = ""
        else:
            overview = str(overview)

        # ------------------------------
        # Combine weighted features
        # ------------------------------

        return " ".join(
            genres * 3
            + keywords * 2
            + cast * 2
            + ([director] * 3 if director else [])
            + [overview]
        ).lower()

    # ==================================================
    # 8. BUILD TF-IDF MODEL
    # ==================================================

    def _build_model(self):

        self.tfidf = TfidfVectorizer(
            stop_words="english",
            max_features=10000,
            ngram_range=(1, 2)
        )

        self.tfidf_matrix = self.tfidf.fit_transform(
            self.df["soup"]
        )

        self.cosine_sim = cosine_similarity(
            self.tfidf_matrix
        )

    # ==================================================
    # 9. GET RECOMMENDATIONS
    # ==================================================

        # ==================================================
    # 9. GET RECOMMENDATIONS
    # ==================================================

    def get_recommendations(self, title, n=10):

        if title not in self.indices:
            return pd.DataFrame()

        idx = self.indices[title]

        # Handle duplicate titles
        if isinstance(idx, (pd.Series, list)):
            idx = idx[0]

        similarity_scores = list(
            enumerate(self.cosine_sim[idx])
        )

        similarity_scores = sorted(
            similarity_scores,
            key=lambda x: x[1],
            reverse=True
        )

        # Remove the movie itself
        similarity_scores = similarity_scores[1:n + 1]

        movie_indices = [
            item[0]
            for item in similarity_scores
        ]

        result = self.df.iloc[
            movie_indices
        ][
            [
                "id",
                "title",
                "vote_average",
                "popularity"
            ]
        ].copy()

        result["similarity_score"] = [
            item[1]
            for item in similarity_scores
        ]

        return result.reset_index(drop=True)
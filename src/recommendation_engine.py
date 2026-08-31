import ast
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


class MovieRecommendationEngine:

    def __init__(self, movies_path, credits_path):
        movies = pd.read_csv(movies_path)
        credits = pd.read_csv(credits_path)

        movies["genres_list"] = movies["genres"].apply(self._names)
        movies["keywords_list"] = movies["keywords"].apply(self._names)

        credits["cast_list"] = credits["cast"].apply(
            lambda x: self._names(x)[:5]
        )
        credits["director"] = credits["crew"].apply(self._director)

        self.df = movies.merge(
            credits[["movie_id", "cast_list", "director"]],
            left_on="id",
            right_on="movie_id",
            how="inner"
        ).reset_index(drop=True)

        self.df["vote_average"] = pd.to_numeric(
            self.df["vote_average"], errors="coerce"
        ).fillna(0)

        self.df["popularity"] = pd.to_numeric(
            self.df["popularity"], errors="coerce"
        ).fillna(0)

        self._build()

    @staticmethod
    def _parse(value):
        if pd.isna(value):
            return []
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError, TypeError):
            return []

    @classmethod
    def _names(cls, value):
        return [
            x["name"]
            for x in cls._parse(value)
            if isinstance(x, dict) and x.get("name")
        ]

    @classmethod
    def _director(cls, value):
        for x in cls._parse(value):
            if isinstance(x, dict) and x.get("job") == "Director":
                return x.get("name", "")
        return ""

    @staticmethod
    def _text(value):
        if not isinstance(value, list):
            return ""
        return " ".join(
            str(x).lower().replace(" ", "_")
            for x in value
            if x
        )

    def _build(self):

        genres = self.df["genres_list"].apply(self._text)
        keywords = self.df["keywords_list"].apply(self._text)
        cast = self.df["cast_list"].apply(self._text)

        director = (
            self.df["director"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.replace(" ", "_", regex=False)
        )

        overview = (
            self.df["overview"]
            .fillna("")
            .astype(str)
            .str.lower()
        )

        self.genre_matrix = TfidfVectorizer().fit_transform(genres)

        self.keyword_matrix = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=15000
        ).fit_transform(keywords)

        self.cast_matrix = TfidfVectorizer().fit_transform(cast)

        self.director_matrix = TfidfVectorizer().fit_transform(director)

        self.overview_matrix = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=20000
        ).fit_transform(overview)

        self.rating = self.df["vote_average"].to_numpy() / 10

        popularity = np.log1p(
            np.maximum(self.df["popularity"].to_numpy(), 0)
        )

        self.popularity = (
            (popularity / popularity.max())
            if popularity.max() > 0
            else popularity
        )

        self.title_lookup = {
            str(title).strip().lower(): i
            for i, title in enumerate(self.df["title"])
        }

    def get_recommendations(self, title, n=10):

        idx = self.title_lookup.get(
            str(title).strip().lower()
        )

        if idx is None:
            return pd.DataFrame()

        try:
            n = max(1, min(int(n), 50))
        except (ValueError, TypeError):
            n = 10

        # ---------------------------------
        # Calculate individual similarities
        # ---------------------------------

        genre = linear_kernel(
            self.genre_matrix[idx],
            self.genre_matrix
        ).ravel()

        keyword = linear_kernel(
            self.keyword_matrix[idx],
            self.keyword_matrix
        ).ravel()

        cast = linear_kernel(
            self.cast_matrix[idx],
            self.cast_matrix
        ).ravel()

        director = linear_kernel(
            self.director_matrix[idx],
            self.director_matrix
        ).ravel()

        overview = linear_kernel(
            self.overview_matrix[idx],
            self.overview_matrix
        ).ravel()

        # ---------------------------------
        # Content similarity
        # ---------------------------------

        content_scores = (
            genre * 0.30
            + keyword * 0.30
            + overview * 0.25
            + cast * 0.10
            + director * 0.05
        )

        # ---------------------------------
        # Quality adjustment
        #
        # Small adjustment only.
        # Content similarity remains dominant.
        # ---------------------------------

        quality_boost = (
            1.0
            + self.rating * 0.15
            + self.popularity * 0.05
        )

        scores = content_scores * quality_boost

        # Never recommend the selected movie itself
        scores[idx] = -np.inf

        # ---------------------------------
        # Get top N
        # ---------------------------------

        count = min(n, len(scores) - 1)

        candidates = np.argpartition(
            scores,
            -count
        )[-count:]

        candidates = candidates[
            np.argsort(scores[candidates])[::-1]
        ]

        # ---------------------------------
        # Build result
        # ---------------------------------

        result = self.df.iloc[candidates][
            [
                "id",
                "title",
                "vote_average",
                "popularity"
            ]
        ].copy()

        result["similarity_score"] = np.round(
            scores[candidates],
            6
        )
        return result.reset_index(drop=True)

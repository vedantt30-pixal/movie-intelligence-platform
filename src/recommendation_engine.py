import ast
import re

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

        # Precompute title tokens once, at build time, instead of
        # re-tokenizing candidate titles on every query.
        self.title_tokens = [
            self._title_tokens(t) for t in self.df["title"]
        ]

        # Document frequency of each title word across the whole corpus.
        # Used to tell "distinctive" franchise words (thor, hulk: DF 2)
        # apart from generic words (up, man, war: DF 16+) so the family
        # check doesn't fire on incidental shared vocabulary.
        title_word_df = {}
        for tokens in self.title_tokens:
            for word in tokens:
                title_word_df[word] = title_word_df.get(word, 0) + 1
        self.title_word_df = title_word_df

    # ==================================================
    # Franchise / title-family diversity
    # ==================================================
    #
    # Without this, "similar movies" for a superhero film tend to
    # be dominated by its own sequels/reboots (Superman, Superman
    # II, Superman Returns, Man of Steel all sharing near-identical
    # genre/cast/keyword vectors). This reduces recommendations being
    # dominated by closely related sequel, reboot, or title-family
    # entries — it detects shared, distinctive title vocabulary, not
    # franchises as a concept.
    # ==================================================

    _IGNORED_TITLE_WORDS = {
        "the", "a", "an", "of", "and", "to", "in", "on",
        "for", "part", "chapter",
    }

    @classmethod
    def _title_tokens(cls, title):
        if not title:
            return frozenset()
        words = re.findall(r"[a-z0-9]+", str(title).lower())
        return frozenset(w for w in words if w not in cls._IGNORED_TITLE_WORDS)

    # A word appearing in more than this many titles is treated as
    # generic (e.g. "up", "man", "war") rather than a franchise marker
    # (e.g. "thor", "hulk", "smurfs" — almost always DF <= 4).
    _GENERIC_WORD_MAX_DF = 10

    def _is_same_family(self, tokens_a, tokens_b):
        if not tokens_a or not tokens_b:
            return False

        shared = tokens_a.intersection(tokens_b)
        if not shared:
            return False

        # Require at least one shared word that's actually distinctive.
        # This is what lets "Thor" match "Thor: The Dark World" (DF=2)
        # while stopping "Up" from matching "Knocked Up" (DF=20) —
        # without a blanket ban on single-token titles, which would
        # have also broken "Thor" and "Hulk" style franchise matches.
        if not any(self.title_word_df.get(w, 0) <= self._GENERIC_WORD_MAX_DF for w in shared):
            return False

        smaller = min(len(tokens_a), len(tokens_b))
        overlap = len(shared)
        return (overlap / smaller) >= 0.6

    def get_recommendations(self, title, n=10, diversify=True):

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
        # Rank all candidates once (descending)
        # ---------------------------------
        #
        # We rank everything rather than just top-N because
        # diversity filtering may skip some high-scoring
        # franchise-mates, so we need a deeper candidate pool
        # to fill back in from.
        # ---------------------------------

        ranked = np.argsort(scores)[::-1]

        if not diversify:
            selected = [
                i for i in ranked[:n]
                if scores[i] > -np.inf
            ]

        else:
            selected = []
            selected_tokens = []
            skipped = []

            target_tokens = self.title_tokens[idx]

            for candidate_idx in ranked:
                if scores[candidate_idx] <= -np.inf:
                    break

                candidate_tokens = self.title_tokens[candidate_idx]

                # Allow a sequel/reboot of the movie being queried.
                # Example:
                #   Toy Story -> Toy Story 2
                #   Dark Knight -> Dark Knight Rises
                #
                # But once one member of a title family has been
                # selected, don't add another member of that family.
                same_as_selected = any(
                    self._is_same_family(
                        candidate_tokens,
                        selected_title_tokens
                    )
                    for selected_title_tokens in selected_tokens
                )

                if same_as_selected:
                    skipped.append(candidate_idx)
                    continue

                selected.append(candidate_idx)
                selected_tokens.append(candidate_tokens)

                if len(selected) >= n:
                    break

            # If there aren't enough diverse candidates, fill the
            # remaining slots with the highest-ranked skipped movies.
            if len(selected) < n:
                for candidate_idx in skipped:
                    selected.append(candidate_idx)

                    if len(selected) >= n:
                        break

        result = self.df.iloc[selected][
            [
                "id",
                "title",
                "vote_average",
                "popularity"
            ]
        ].copy()

        result["similarity_score"] = np.round(
            scores[selected],
            6
        )
        return result.reset_index(drop=True)
import { useState } from "react";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

const QUICK_SEARCHES = [
  "Avatar",
  "Inception",
  "Interstellar",
  "The Dark Knight",
];

function App() {
  const [movie, setMovie] = useState("");
  const [searchedMovie, setSearchedMovie] = useState("");
  const [recommendations, setRecommendations] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [diversify, setDiversify] = useState(true);

  const getRecommendations = async (searchTitle = movie) => {
    const title = searchTitle.trim();

    if (!title) {
      setError("Please enter a movie title.");
      setRecommendations([]);
      return;
    }

    setError("");
    setLoading(true);

    try {
      const params = new URLSearchParams({
        n: "10",
        diversify: String(diversify),
      });

      const response = await fetch(
        `${API_BASE_URL}/recommendations/${encodeURIComponent(title)}?${params}`
      );

      let data = {};

      try {
        data = await response.json();
      } catch {
        throw new Error("The server returned an invalid response.");
      }

      if (!response.ok) {
        throw new Error(data.detail || "Movie not found.");
      }

      setRecommendations(data.recommendations || []);
      setSearchedMovie(data.movie || title);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to connect to the recommendation service."
      );
      setRecommendations([]);
      setSearchedMovie("");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      getRecommendations();
    }
  };

  const handleQuickSearch = (title) => {
    setMovie(title);
    getRecommendations(title);
  };

  const handleDiversityChange = (event) => {
    const enabled = event.target.checked;
    setDiversify(enabled);

    if (searchedMovie) {
      setTimeout(() => {
        getRecommendations(searchedMovie);
      }, 0);
    }
  };

  return (
    <div className="app">
      <header className="hero">
        <div className="hero-glow hero-glow-one" />
        <div className="hero-glow hero-glow-two" />

        <div className="hero-content">
          <div className="brand-mark" aria-hidden="true">
            <span>MI</span>
          </div>

          <div className="eyebrow">AI-POWERED DISCOVERY</div>

          <h1>
            Find your next
            <span> great movie.</span>
          </h1>

          <p className="hero-description">
            Tell us what you love. Our machine-learning recommendation engine
            finds movies with similar stories, genres, keywords, cast, and
            directors.
          </p>

          <div className="search-box">
            <span className="search-icon" aria-hidden="true">
              ⌕
            </span>

            <input
              type="text"
              placeholder="Search for a movie..."
              value={movie}
              onChange={(event) => {
                setMovie(event.target.value);
                if (error) {
                  setError("");
                }
              }}
              onKeyDown={handleKeyDown}
              disabled={loading}
              aria-label="Movie title"
            />

            {movie && !loading && (
              <button
                className="clear-button"
                onClick={() => {
                  setMovie("");
                  setError("");
                }}
                aria-label="Clear search"
              >
                ×
              </button>
            )}

            <button
              className="recommend-button"
              onClick={() => getRecommendations()}
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="button-spinner" />
                  Analyzing
                </>
              ) : (
                <>
                  Recommend
                  <span aria-hidden="true">→</span>
                </>
              )}
            </button>
          </div>

          <div className="quick-searches">
            <span>Try</span>

            {QUICK_SEARCHES.map((title) => (
              <button
                key={title}
                onClick={() => handleQuickSearch(title)}
                disabled={loading}
              >
                {title}
              </button>
            ))}
          </div>

          <div className="controls">
            <label className="toggle">
              <input
                type="checkbox"
                checked={diversify}
                onChange={handleDiversityChange}
                disabled={loading}
              />

              <span className="toggle-track">
                <span className="toggle-thumb" />
              </span>

              <span className="toggle-copy">
                <strong>Smart diversity</strong>
                <small>Reduce repetitive franchise results</small>
              </span>
            </label>
          </div>

          {error && (
            <div className="error" role="alert">
              <span aria-hidden="true">!</span>
              <div>
                <strong>Something went wrong</strong>
                <p>{error}</p>
              </div>
            </div>
          )}
        </div>
      </header>

      {loading && (
        <main className="content">
          <section className="loading-state">
            <div className="loading-orbit">
              <span />
              <span />
              <span />
            </div>

            <div className="loading-copy">
              <span className="results-label">ANALYZING</span>
              <h2>Finding your recommendations...</h2>
              <p>
                Comparing genres, keywords, cast, directors, and story
                information.
              </p>
            </div>

            <div className="skeleton-grid">
              {Array.from({ length: 5 }).map((_, index) => (
                <div className="skeleton-card" key={index}>
                  <div className="skeleton-poster" />
                  <div className="skeleton-line skeleton-title" />
                  <div className="skeleton-line skeleton-small" />
                </div>
              ))}
            </div>
          </section>
        </main>
      )}

      {!loading && recommendations.length > 0 && (
        <main className="content results-content">
          <div className="results-header">
            <div>
              <span className="results-label">YOUR RESULTS</span>

              <h2>
                Because you liked{" "}
                <span>&ldquo;{searchedMovie}&rdquo;</span>
              </h2>

              <p className="results-description">
                Ranked by content similarity and lightly adjusted for movie
                quality and popularity.
              </p>
            </div>

            <div className="results-meta">
              <div className="result-count">
                <strong>{recommendations.length}</strong>
                <span>recommendations</span>
              </div>

              <div className="mode-pill">
                <span className="mode-dot" />
                {diversify ? "Diversity ON" : "Pure similarity"}
              </div>
            </div>
          </div>

          <div className="movie-grid">
            {recommendations.map((recommendation, index) => (
              <MovieCard
                key={recommendation.id}
                recommendation={recommendation}
                rank={index + 1}
              />
            ))}
          </div>
        </main>
      )}

      {!loading && !error && recommendations.length === 0 && (
        <main className="content">
          <section className="empty-state">
            <div className="empty-visual">
              <div className="empty-film">▦</div>
              <div className="empty-spark">✦</div>
            </div>

            <span className="results-label">READY WHEN YOU ARE</span>

            <h2>What are you in the mood for?</h2>

            <p>
              Search for a movie and we'll build a personalized-looking
              recommendation list from our 4,803-movie catalog.
            </p>

            <div className="empty-features">
              <div>
                <span>01</span>
                <strong>Search</strong>
                <small>Choose a movie you love</small>
              </div>

              <div>
                <span>02</span>
                <strong>Analyze</strong>
                <small>Compare movie attributes</small>
              </div>

              <div>
                <span>03</span>
                <strong>Discover</strong>
                <small>Get your recommendations</small>
              </div>
            </div>
          </section>
        </main>
      )}

      <footer>
        <div>
          <strong>Movie Intelligence</strong>
          <span>React · FastAPI · TF-IDF</span>
        </div>

        <p>Recommendations are generated from movie content and metadata.</p>
      </footer>
    </div>
  );
}

function MovieCard({ recommendation, rank }) {
  const score = Number(recommendation.similarity_score) || 0;
  const rating = Number(recommendation.vote_average) || 0;
  const popularity = Number(recommendation.popularity) || 0;

  const matchPercentage = Math.min(score * 100, 99.9);
  const barPercentage = Math.min(score * 100 * 1.6, 100);

  return (
    <article className={`movie-card ${rank === 1 ? "top-card" : ""}`}>
      <div className="poster-wrapper">
        <div className="rank">
          <span>#</span>
          {rank}
        </div>

        {rank === 1 && <div className="top-pick">TOP PICK</div>}

        <img
          src={recommendation.poster_url || "/movie-placeholder.svg"}
          alt={`${recommendation.title} poster`}
          className="movie-poster"
          loading="lazy"
          onError={(event) => {
            event.currentTarget.onerror = null;
            event.currentTarget.src = "/movie-placeholder.svg";
          }}
        />

        <div className="poster-gradient" />

        <div className="similarity-badge">
          <strong>{matchPercentage.toFixed(1)}%</strong>
          <span>match</span>
        </div>
      </div>

      <div className="movie-info">
        <h3 title={recommendation.title}>{recommendation.title}</h3>

        <div className="movie-stats">
          <div className="stat">
            <span className="stat-label">Rating</span>
            <span className="stat-value">
              <span className="star">★</span>
              {rating.toFixed(1)}
            </span>
          </div>

          <div className="stat">
            <span className="stat-label">Popularity</span>
            <span className="stat-value">{popularity.toFixed(1)}</span>
          </div>
        </div>

        <div className="match-section">
          <div className="match-header">
            <span>Similarity</span>
            <strong>{score.toFixed(3)}</strong>
          </div>

          <div className="match-bar">
            <div
              className="match-fill"
              style={{ width: `${barPercentage}%` }}
            />
          </div>
        </div>
      </div>
    </article>
  );
}

export default App;
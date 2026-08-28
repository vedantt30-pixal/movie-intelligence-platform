import { useState } from "react";
import "./App.css";

function App() {
  const [movie, setMovie] = useState("");
  const [recommendations, setRecommendations] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const getRecommendations = async () => {
    if (!movie.trim()) {
      setError("Please enter a movie title.");
      setRecommendations([]);
      return;
    }

    setError("");
    setLoading(true);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/recommendations/${encodeURIComponent(
          movie.trim()
        )}?n=10`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Movie not found.");
      }

      setRecommendations(data.recommendations);
    } catch (err) {
      setError(err.message);
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      getRecommendations();
    }
  };

  return (
    <div className="app">
      {/* ================= HERO ================= */}
      <header className="hero">
        <div className="hero-content">
          <div className="logo">🎬</div>

          <h1>Movie Intelligence</h1>

          <p>
            Discover movies you'll love using machine learning.
          </p>

          <div className="search-box">
            <input
              type="text"
              placeholder="Search for a movie..."
              value={movie}
              onChange={(e) => setMovie(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />

            <button
              onClick={getRecommendations}
              disabled={loading}
            >
              {loading ? "Analyzing..." : "Recommend"}
            </button>
          </div>

          <p className="search-hint">
            Try searching for <strong>Avatar</strong>,{" "}
            <strong>Inception</strong>, or <strong>Interstellar</strong>
          </p>

          {error && (
            <div className="error">
              ⚠️ {error}
            </div>
          )}
        </div>
      </header>

      {/* ================= RESULTS ================= */}
      {recommendations.length > 0 && (
        <main className="content">
          <div className="results-header">
            <div>
              <span className="results-label">
                RECOMMENDATIONS
              </span>

              <h2>
                Movies similar to{" "}
                <span>"{movie}"</span>
              </h2>
            </div>

            <div className="results-count">
              {recommendations.length} movies
            </div>
          </div>

          <div className="movie-grid">
            {recommendations.map((recommendation, index) => (
              <div
                className="movie-card"
                key={recommendation.id}
              >
                {/* Ranking */}
                <div className="rank">
                  #{index + 1}
                </div>

                {/* Poster */}
                <div className="poster-wrapper">
                  {recommendation.poster_url ? (
                    <img
                      src={recommendation.poster_url}
                      alt={recommendation.title}
                      className="movie-poster"
                    />
                  ) : (
                    <div className="poster-placeholder">
                      <span>🎬</span>
                      <p>No Poster</p>
                    </div>
                  )}

                  <div className="similarity-badge">
                    {(recommendation.similarity_score * 100).toFixed(
                      1
                    )}
                    % Match
                  </div>
                </div>

                {/* Movie info */}
                <div className="movie-info">
                  <h3>{recommendation.title}</h3>

                  <div className="movie-stats">
                    <div>
                      <span className="stat-label">
                        Rating
                      </span>

                      <span className="stat-value">
                        ⭐{" "}
                        {Number(
                          recommendation.vote_average
                        ).toFixed(1)}
                      </span>
                    </div>

                    <div>
                      <span className="stat-label">
                        Popularity
                      </span>

                      <span className="stat-value">
                        {Number(
                          recommendation.popularity
                        ).toFixed(1)}
                      </span>
                    </div>
                  </div>

                  <div className="match-bar">
                    <div
                      className="match-fill"
                      style={{
                        width: `${Math.min(
                          recommendation.similarity_score * 100 * 5,
                          100
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </main>
      )}

      {/* ================= EMPTY STATE ================= */}
      {!loading &&
        !error &&
        recommendations.length === 0 && (
          <section className="empty-state">
            <div className="empty-icon">🧠</div>

            <h2>Ready to discover something new?</h2>

            <p>
              Enter a movie above and our recommendation engine
              will find similar movies for you.
            </p>
          </section>
        )}

      {/* ================= LOADING ================= */}
      {loading && (
        <section className="loading-state">
          <div className="spinner"></div>

          <h2>Finding your recommendations...</h2>

          <p>
            Our recommendation engine is analyzing movie
            similarities.
          </p>
        </section>
      )}

      {/* ================= FOOTER ================= */}
      <footer>
        <p>
          Movie Intelligence · Built with React, FastAPI &
          Machine Learning
        </p>
      </footer>
    </div>
  );
}

export default App;
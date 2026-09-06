# 🎬 Movie Intelligence

A content-based movie recommendation system that uses machine learning to recommend movies similar to a user's search.

The project combines a **Python recommendation engine**, **FastAPI backend**, and **React frontend** to provide an interactive movie recommendation experience.

---

## 🚀 Live Demo

👉 **[Try Movie Intelligence](https://movie-intelligence-platform-1.onrender.com)**

### 🔗 Services

- **Frontend:** https://movie-intelligence-platform-1.onrender.com
- **Backend API:** https://movie-intelligence-platform.onrender.com
- **API Documentation:** https://movie-intelligence-platform.onrender.com/docs
- **Health Check:** https://movie-intelligence-platform.onrender.com/health

---

## ✨ Features

- 🎬 Search for a movie and receive recommendations
- 🤖 Content-based machine learning recommendation engine
- 🎭 Uses genres, keywords, cast, director, and movie overview
- ⭐ Displays movie ratings
- 📈 Displays movie popularity
- 🎯 Shows similarity/match scores
- 🖼️ Displays movie posters
- ⚡ FastAPI REST API
- ⚛️ React + Vite frontend
- ⌨️ Supports pressing Enter to search
- 🛡️ Handles unknown and partial movie titles
- 🔄 Recommendation diversification
- ✅ Automated tests with pytest

---

## 🧠 How the Recommendation System Works

The recommendation engine uses **TF-IDF vectorization** and **cosine similarity** to compare movies.

For each movie, the system extracts:

- Genres
- Keywords
- Top cast members
- Director
- Overview

Each feature is converted into a TF-IDF representation.

The final content similarity score is calculated using weighted similarities:

| Feature | Weight |
|---|---:|
| Genres | 30% |
| Keywords | 30% |
| Overview | 25% |
| Cast | 10% |
| Director | 5% |

A small quality adjustment is then applied using movie rating and popularity.

The selected movie itself is always excluded from the recommendations.

---

## 🏗️ Architecture

```text
                    ┌──────────────────┐
                    │   React Frontend │
                    │    Vite + CSS    │
                    └────────┬─────────┘
                             │
                             │ HTTP Request
                             ▼
                    ┌──────────────────┐
                    │  FastAPI Backend │
                    │     REST API     │
                    └────────┬─────────┘
                             │
                             ▼
                 ┌────────────────────────┐
                 │  Recommendation Engine │
                 │                        │
                 │ TF-IDF + Cosine       │
                 │ Similarity             │
                 └───────────┬────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   TMDB Dataset   │
                    │ Movies + Credits │
                    └──────────────────┘
```

---

## 🛠️ Tech Stack

- **Frontend:** React, Vite, CSS
- **Backend:** FastAPI, Python
- **Machine Learning:** TF-IDF, Cosine Similarity
- **Data:** TMDB 5000 Movies Dataset
- **Movie Metadata:** TMDB API
- **Testing:** pytest
- **Deployment:** Render

---

## 🔌 API Example

### Get Recommendations

```http
GET /recommendations/Avatar?n=10&diversify=true
```

Example response:

```json
{
  "movie": "Avatar",
  "recommendations": [
    {
      "title": "Star Trek Into Darkness",
      "vote_average": 7.4,
      "similarity_score": 0.384488
    }
  ]
}
```

### Health Check

```http
GET /health
```

---

## 📁 Project Structure

```text
movie-intelligence-platform/
├── backend/
│   └── main.py
├── frontend/
│   ├── src/
│   └── package.json
├── src/
│   └── recommendation_engine.py
├── data/
│   └── raw/
├── tests/
├── requirements.txt
└── README.md
```

---



## 📌 Project Status

**Live and deployed** 🚀

The application is currently available through the live demo above.

---

## 👨‍💻 Author

**Vedant Mhaskar**

GitHub: [@vedantt30-pixal](https://github.com/vedantt30-pixal)
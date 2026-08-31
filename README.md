# 🎬 Movie Intelligence

A content-based movie recommendation system that uses machine learning to recommend movies similar to a user's search.

The project combines a **Python recommendation engine**, **FastAPI backend**, and **React frontend** to provide an interactive movie recommendation experience.

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
                 │ Recommendation Engine  │
                 │                        │
                 │ TF-IDF + Cosine        │
                 │ Similarity              │
                 └───────────┬────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   TMDB Dataset   │
                    │ Movies + Credits │
                    └──────────────────┘
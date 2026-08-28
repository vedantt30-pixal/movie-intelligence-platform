# Movie Intelligence Platform — Project Memory

## Project Goal

Build a resume-worthy Movie Intelligence Platform using the TMDB 5000 dataset.

The system will provide movie recommendations and eventually include:
- Content-based recommendations
- Movie search
- Movie details
- Recommendation explanations
- Evaluation metrics
- Frontend UI
- Backend API
- Eventually deployment

---

## Current Status

### Backend
Status: Working

### Frontend
Status: Working

### Recommendation Engine
Status: Content-based TF-IDF recommendation engine implemented.

### Dataset
TMDB 5000 Movies + Credits

Movies shape:
4803 rows × 20 columns

Credits shape:
4803 rows × 4 columns

---

## Recommendation Engine

File:
`[ADD FILE PATH HERE]`

Current approach:
- Parse JSON-like TMDB columns using `ast.literal_eval`
- Extract genres
- Extract keywords
- Extract top 5 cast members
- Extract director
- Merge movies and credits
- Create weighted feature "soup"
- TF-IDF vectorization
- Cosine similarity
- Return top-N recommendations

TF-IDF configuration:

- stop_words = "english"
- max_features = 10000
- ngram_range = (1, 2)

Similarity matrix:
4803 × 4803

---

## Current Features

- [x] Dataset loading
- [x] JSON-like column parsing
- [x] Genre extraction
- [x] Keyword extraction
- [x] Cast extraction
- [x] Director extraction
- [x] Dataset merging
- [x] Feature engineering
- [x] TF-IDF
- [x] Cosine similarity
- [x] Movie recommendations
- [ ] Backend API integration
- [ ] Frontend recommendation UI
- [ ] Movie search
- [ ] Recommendation explanations
- [ ] Evaluation
- [ ] Advanced recommendation strategy
- [ ] Deployment

---

## Important Technical Decisions

### Backend
Working backend exists.

### Frontend
Working frontend exists.

### ML
Currently using:
`scikit-learn`

Main model:
`TfidfVectorizer + cosine_similarity`

---

## Development Log

### 2026-08-28

- Backend confirmed working.
- Frontend confirmed working.
- Decided to build a persistent project memory system.
- Created the concept of `PROJECT_MEMORY.md`.
- Goal of memory system: allow the project to be continued across different ChatGPT conversations/accounts without repeatedly explaining the entire project.

---

## Next Task

DO NOT START YET.

The next development step will be decided in the next conversation.

---

## File Change Log

| Date | File | Change | Reason |
|------|------|--------|--------|
| 2026-08-28 | PROJECT_MEMORY.md | Created | Persistent project context |

---

## Rules for Continuing This Project

1. Read this file before making major changes.
2. Do not assume previous conversation context exists.
3. Record important architectural decisions.
4. Record significant file changes.
5. Record bugs and their solutions.
6. Record completed features.
7. Record the next planned task.
8. Keep this file updated as the project evolves.
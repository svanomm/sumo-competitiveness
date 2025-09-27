git clone <https://github.com/svanomm/sumo-competitiveness/>
# Sumo Competitiveness: Data Acquisition, Cleaning, and Modeling

This repository contains an end‑to‑end pipeline for assembling a research dataset on professional sumo wrestling from the public SumoDB website (sumodb.sumogames.de). It covers: (1) automated collection of bout‐level results (2000–2025) and wrestler profile attributes, (2) structured storage/export as CSV, (3) basic cleaning and feature construction, and (4) preliminary statistical modeling (logistic regression of bout outcomes) and exploratory distributions.

## 1. Scope and Objectives
Research question: How competitive are professional sumo bouts and which observable pre‑bout characteristics most strongly relate to victory probability?

Core tasks implemented:

- Bout data scraping (≈ 76k bouts, 2000.01 onward) with controlled pagination (1,000 bouts/page).
- Wrestler profile scraping (biographical + physical measures + rank history segments).
- Batch and resumable scraping modes with progress logging for reliability.
- Clean CSV outputs stamped with retrieval metadata (timestamp, source offset) for reproducibility.
- Feature engineering and exploratory analysis (win rate distributions, variability, logistic model, ROC curve).

## 2. Data Sources and Outputs
 
### 2.1 Bout Dataset (`data/*bouts*.csv`)

Columns (principal):

- basho: YYYY.MM tournament identifier.
- day: Tournament day number.
- wrestler1 / wrestler2: Shikona (ring names).
- wrestler1_rank / wrestler2_rank: Rank strings as listed (e.g., J13w, M5e).
- wrestler1_result / wrestler2_result: Per-bout outcome plus running record at that point.
- kimarite: Winning technique (string; may be empty when not reported).
- scraped_at: ISO timestamp of retrieval.
- source_offset: Integer offset (multiples of 1000) used in pagination.

### 2.2 Wrestler Profile Dataset (`data/*wrestlers*.csv`)

Selected columns:

- rikishi: Shikona/name.
- heya: Stable (sumo training residence).
- shusshin: Birthplace (as listed in SumoDB).
- birth_date, hatsu (debut), intai (retirement) as raw strings (no locale normalization yet).
- height, weight: in cm, kg.
- highest_rank, career_high: Rank summaries.
- date_info, rank_info, age_info, record_info: Additional career snapshot columns captured verbatim.
- scraped_at, source_offset: Retrieval metadata.

### 3 Analysis

Located in `output/`:

- `overall_win_rate_distribution.pdf`, `annual_win_rate_distribution.pdf`: Empirical distributions for competitiveness assessment.
- `overall_rank_sd_distribution.pdf`: Variation in rank outcomes.
- `logit_model_summary.txt`: Statsmodels logistic regression results for bout win probability using engineered covariates (differences in historical win rate, age, rank, physique proxies, division flags, etc.).
- `roc_curve_bout_level_model.pdf`: Discriminative performance visualization.

## 4 Pipeline Overview

1. Configuration: Environment and rate limits defined in `config/settings.py` (default delay ~1–3s; adjustable via env variables). Directories ensured on import.
2. Scraping Abstraction: `src/scrapers/base_scraper.py` provides an asynchronous pattern (aiohttp + semaphore + delay, graceful timeout handling, structured parsing hook).
3. Bout Scraper: `src/scrapers/sumodb_scraper.py` iteratively builds paginated query URLs, parses HTML table rows into normalized dictionaries, and concatenates page DataFrames.
4. Name/Profile Scraper: `src/scrapers/sumo_name_scraper.py` targets wrestler metadata across an offset range, similarly batched.
5. Batch Execution: `scripts/run_batch_scrape.py` and `scripts/run_name_scraper.py` implement resumable chunking (progress persisted in `progress.txt` plus per‑batch CSVs for fault tolerance).
6. Main Entry Point: `main.py` offers interactive selection (test subset vs full scrape vs N pages) for bout data.
7. Cleaning / Utilities: `src/utils.py` includes text normalization placeholders and (future) database export utilities (an async SQLite schema is referenced for potential extension; model file not yet included in this repository snapshot).
8. Analysis: Jupyter notebooks under `scripts/` and produced PDF outputs illustrate exploratory summaries and predictive modeling.

# Pracuj.pl Job Scraper

A Python scraper for **[pracuj.pl](https://pracuj.pl)** — the largest Polish job board. Collects job listings, normalises the data, and filters for IT roles.

## What it does

1. Scrapes job listing URLs from search result pages
2. Visits each listing and stores structured data in SQLite (parallel scraping supported)
3. Cleans and normalises the raw data (salary, region, languages, …)
4. Exports a filtered database of IT-related roles
5. Tracks historical trends via CSV snapshots
6. Visualises everything in an interactive Streamlit dashboard

## Pipeline

Run the full pipeline with a single command:

```bash
python main_trigger.py
```

Or skip scraping and re-run cleanup/filter/snapshot only:

```bash
python main_trigger.py --skip-scrape
```

Custom worker count:

```bash
python main_trigger.py --workers 64
```

### Individual steps (manual)

```bash
# 1. Collect listing URLs
python url_list_search2.0.py

# 2. Scrape each listing → job_database.db (parallel, 32 workers by default)
python detail_scraper2.0.py
python detail_scraper2.0.py --workers 4    # custom worker count
python detail_scraper2.0.py --no-fresh     # keep existing data

# 3. Clean & normalise data
python db_cleaner/database_cleaner.py

# 4. Filter IT roles → nerd_jobs.db
python nerds_db_filter.py

# 5. Append monthly CSV snapshots
python snapshot_history.py
```

> **Note:** Each cleaning step prompts for confirmation before writing to the database.
> `snapshot_history.py` runs automatically after each scrape (idempotent per month).

## Output

| File | Description |
|------|-------------|
| `job_urls_complete.json` | Raw list of scraped listing URLs |
| `job_database.db` | All job offers (~230 MB after full scrape) |
| `nerd_jobs.db` | Filtered IT roles only |
| `dashboard/data/history_roles.csv` | Monthly job count per IT role (trend data) |
| `dashboard/data/history_industries.csv` | Monthly job count per industry (trend data) |

## Database schema

Table: `job_offers`

| Column group | Columns |
|-------------|---------|
| Identity | `partition_id` (PK), `url`, `title` |
| Company | `company` |
| Salary | `salary_min`, `salary_max`, `salary_currency` |
| Location | `region`, `city`, `postal_code` |
| Work conditions | `work_modes`, `work_schedules`, `employment_type`, `position_levels` |
| Content | `industry`, `description`, `technologies_os`, `technologies_optional`, `requirements_expected`, `we_offer`, `benefits` |
| Dates | `date_posted`, `valid_through` |
| Added by cleaner | `monthly_max_salary`, `mapped_industry`, `kw_industry`, `mapped_languages` |

Salary values below 1 000 PLN are treated as hourly rates and converted to monthly equivalents (× 160).

## Dashboard

Interactive Streamlit dashboard deployed on [Streamlit Community Cloud](https://streamlit.io/cloud). Visualises IT job market data from `nerd_jobs.db`.

**Pages:**
- **Top Skills** — most demanded skills across IT roles (bar chart + full table)
- **Salary by Job Role** — median/mean monthly salary per role category
- **Salary by Skill** — median/mean salary per technology/skill (min 5 postings)
- **Salary by Seniority Level** — salary breakdown by junior/mid/senior/lead
- **Job Postings by Region** — geographic distribution of IT jobs
- **Historical Trends** — line chart tracking job counts over time (IT roles / all industries)

All pages include a Job Role filter. Salary pages have a Median/Mean/Both toggle.

## Project structure

```
Pracuj/
├── url_list_search2.0.py       # Step 1 — collect listing URLs
├── main_trigger.py             # Pipeline orchestrator (runs all steps, --skip-scrape, --workers)
├── detail_scraper2.0.py        # Step 2 — parallel scraper (--workers 32, fresh mode)
├── nerds_db_filter.py          # Step 4 — IT role filter
├── snapshot_history.py         # Step 5 — append monthly snapshots to CSV
├── Nerd_mapped.csv             # Keyword → mapped title mapping for IT roles
├── db_cleaner/
│   ├── database_cleaner.py     # Step 3 — orchestrates all mappers
│   ├── base_mapper.py          # Abstract base class (Template Method pattern)
│   └── mappers/
│       ├── salary_mapper.py
│       ├── region_mapper.py
│       ├── work_modes_mapper.py
│       ├── work_schedules_mapper.py
│       ├── employment_type_mapper.py
│       ├── position_levels_mapper.py
│       ├── industry_mapper.py
│       └── language_mapper.py
├── dashboard/
│   ├── TOP_Skills.py           # Main page — Top Skills Overview
│   ├── .streamlit/config.toml  # Streamlit theme config
│   ├── components/charts.py    # Plotly chart functions
│   ├── data/
│   │   ├── loader.py              # DB queries & data transforms
│   │   ├── history_roles.csv      # Monthly IT role trend data
│   │   └── history_industries.csv # Monthly industry trend data
│   └── pages/
│       ├── 2_Salary_Per_Role.py
│       ├── 3_Salary_Per_Skill.py
│       ├── 4_Salary_Per_Level.py
│       ├── 5_Jobs_Per_Region.py
│       └── 6_Trends.py            # Historical trend line charts
└── job_database.db             # Full database (~230 MB, git-ignored)
```

## Installation

```bash
# Scraping pipeline
pip install cloudscraper

# Dashboard
pip install -r dashboard/requirements.txt
```

## Requirements

- Python 3.10+
- `cloudscraper` (handles Cloudflare protection on pracuj.pl)
- Dashboard: `streamlit`, `pandas`, `plotly`, `sqlalchemy`

## Notes

- Old scripts (`detail_scraper.py`, `nerds_database.py`, `url_scraper.py`) are archived in `ARCH/`.

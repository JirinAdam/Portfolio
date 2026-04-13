# Pracuj.pl Job Scraper

A Python scraper for **[pracuj.pl](https://pracuj.pl)** — the largest Polish job board. Collects job listings, normalises the data, and filters for IT roles.

## What it does

1. Scrapes job listing URLs from search result pages
2. Visits each listing and stores structured data in SQLite
3. Cleans and normalises the raw data (salary, region, languages, …)
4. Exports a filtered database of IT-related roles

## Pipeline

Run the steps in order:

```bash
# 1. Collect listing URLs
python url_scraper.py

# 2. Scrape each listing → job_database.db
python detail_scraper.py

# 3. Clean & normalise data (run from db_cleaner directory)
cd db_cleaner
python database_cleaner.py

# 4. Filter IT roles → nerd_jobs.db
cd ..
python nerds_db_filter.py
```

> **Note:** `database_cleaner.py` must be run from the `db_cleaner/` directory due to relative imports.
> Each cleaning step prompts for confirmation before writing to the database.

## Output

| File | Description |
|------|-------------|
| `job_urls_complete.json` | Raw list of scraped listing URLs |
| `job_database.db` | All job offers (~230 MB after full scrape) |
| `nerd_jobs.db` | Filtered IT roles only |

## Database schema

Table: `job_offers`

| Column group | Columns |
|-------------|---------|
| Identity | `id`, `url`, `title` |
| Company | `company_name`, `company_size` |
| Salary | `salary_raw`, `salary_min`, `salary_max`, `salary_currency`, `salary_period`, `monthly_min_salary`, `monthly_max_salary` |
| Location | `region`, `city`, `mapped_region` |
| Work conditions | `work_modes`, `schedules`, `employment_type`, `position_levels` |
| Content | `technologies`, `description` |
| Added by cleaner | `mapped_industry`, `kw_industry`, `mapped_languages` |

Salary values below 1 000 PLN are treated as hourly rates and converted to monthly equivalents (× 160).

## Dashboard

Interactive Streamlit dashboard deployed on [Streamlit Community Cloud](https://streamlit.io/cloud). Visualises IT job market data from `nerd_jobs.db`.

**Pages:**
- **Top Skills** — most demanded skills across IT roles (bar chart + full table)
- **Salary by Job Role** — median/mean monthly salary per role category
- **Salary by Skill** — median/mean salary per technology/skill (min 5 postings)
- **Salary by Seniority Level** — salary breakdown by junior/mid/senior/lead
- **Job Postings by Region** — geographic distribution of IT jobs

All pages include a Job Role filter. Salary pages have a Median/Mean/Both toggle.

## Project structure

```
Pracuj/
├── url_scraper.py              # Step 1 — collect listing URLs
├── detail_scraper.py           # Step 2 — scrape listing details
├── nerds_db_filter.py          # Step 4 — IT role filter (current version)
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
│   ├── data/loader.py          # DB queries & data transforms
│   ├── components/charts.py    # Plotly chart functions
│   └── pages/
│       ├── 2_Salary_Per_Role.py
│       ├── 3_Salary_Per_Skill.py
│       ├── 4_Salary_Per_Level.py
│       └── 5_Jobs_Per_Region.py
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

- `nerds_database.py` is an **older** version of the IT filter — use `nerds_db_filter.py` instead.
- `url_list_search2.0.py` is a duplicate of `url_scraper.py` — use `url_scraper.py`.
- A backup of the original raw database is kept as `job_database_original_backup.db`.

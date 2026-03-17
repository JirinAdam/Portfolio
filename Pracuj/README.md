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
│       ├── salary.py
│       ├── region.py
│       ├── work_modes.py
│       ├── schedules.py
│       ├── employment_type.py
│       ├── position_levels.py
│       ├── industry.py
│       └── language.py
└── job_database.db             # Output database (git-ignored)
```

## Installation

```bash
pip install cloudscraper
```

All other dependencies are Python standard library (`sqlite3`, `json`, `re`, `csv`, `pathlib`, `abc`).

## Requirements

- Python 3.8+
- `cloudscraper` (handles Cloudflare protection on pracuj.pl)

## Notes

- `nerds_database.py` is an **older** version of the IT filter — use `nerds_db_filter.py` instead.
- `url_list_search2.0.py` is a duplicate of `url_scraper.py` — use `url_scraper.py`.
- A backup of the original raw database is kept as `job_database_original_backup.db`.

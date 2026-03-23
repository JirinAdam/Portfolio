# CLAUDE.md — Pracuj Scraper & Dashboard Project

## Project Overview
Web scraper pro **pracuj.pl** (polský job board). Stahuje pracovní nabídky, čistí data, filtruje IT role a vizualizuje výsledky v Streamlit dashboardu.

- **Vstup:** pracuj.pl search pages
- **Výstup:** `job_database.db` (všechny nabídky), `nerd_jobs.db` (IT role), Streamlit dashboard

---

## Pipeline (pořadí spuštění)

```
1. url_scraper.py                    →  job_urls_complete.json   (scrape URL z výsledků vyhledávání)
2. detail_scraper.py                 →  job_database.db           (scrape detailů každé nabídky)
3. db_cleaner/database_cleaner.py    →  job_database.db           (čištění a normalizace dat, in-place)
4. nerds_db_filter.py                →  nerd_jobs.db              (filtrování IT rolí)
5. dashboard/app.py                  →  Streamlit Cloud            (vizualizace nerd_jobs.db)
```

---

## Klíčové soubory

### Scraping pipeline

| Soubor | Role |
|--------|------|
| `url_scraper.py` | Scrape URL stránek s paginací, výstup JSON |
| `detail_scraper.py` | Scrape detailů každé nabídky → SQLite DB |
| `db_cleaner/database_cleaner.py` | Orchestrátor 8 mapperů (čištění DB) |
| `db_cleaner/base_mapper.py` | Abstraktní base class — Template Method pattern |
| `db_cleaner/mappers/*.py` | 8 mapperů: salary, region, work_modes, schedules, employment_type, position_levels, industry, language |
| `nerds_db_filter.py` | Filtrovací skript (kw_title + monthly_max_salary) |
| `Nerd_mapped.csv` | Keyword mapping: title → mapped_title pro IT role |

### Dashboard

| Soubor | Role |
|--------|------|
| `dashboard/app.py` | Hlavní stránka — Top Skills Overview |
| `dashboard/data/loader.py` | DB připojení, dotazy, datové transformace (`@st.cache_data`) |
| `dashboard/components/charts.py` | 3 Plotly chart funkce (skills_bar, salary_bar, jobs_bar) |
| `dashboard/pages/2_salary_per_role.py` | Salary by Job Role (Median/Mean toggle) |
| `dashboard/pages/3_salary_per_skill.py` | Salary by Skill (filtr kw_title, min 5 záznamů) |
| `dashboard/pages/4_salary_per_level.py` | Salary by Seniority Level |
| `dashboard/pages/5_jobs_per_region.py` | Job Postings by Region |

---

## DB schéma — tabulka `job_offers` (job_database.db)

Sloupce po průchodu celou pipeline:

| Skupina | Sloupce |
|---------|---------|
| Identifikace | `id`, `url`, `title` |
| Firma | `company_name`, `company_size` |
| Plat | `salary_raw`, `salary_min`, `salary_max`, `salary_currency`, `salary_period`, `monthly_min_salary`, `monthly_max_salary` |
| Lokalita | `region`, `city`, `mapped_region` |
| Pracovní podmínky | `work_modes`, `schedules`, `employment_type`, `position_levels` |
| Obsah nabídky | `technologies`, `description` |
| Doplněno db_cleaner | `mapped_industry`, `kw_industry`, `mapped_languages` |

## DB schéma — tabulka `nerd_jobs` (nerd_jobs.db)

Klíčové:
- `kw_title` — mapovaná kategorie role (filtr v dashboardu)
- `monthly_max_salary` — primární salary sloupec (REAL)
- `technologies_os`, `technologies_optional` — JSON arrays v TEXT
- `position_levels` — JSON array v TEXT

---

## GitHub

- **Repo:** `JirinAdam/Portfolio` → složka `Pracuj/`
- **Tracked:** vše kromě velkých DB a lokálních souborů
- **`nerd_jobs.db` (6.6 MB)** — tracked (potřebuje Streamlit Cloud)
- **`job_database.db` (~230 MB)** — .gitignore (přes GitHub limit)
- **`Support/`, `csvCollection/`** — lokální, nejsou na GitHubu

---

## Upozornění / Gotchas

- **`db_cleaner` musí být spouštěn ze své složky** kvůli relativním importům mapperů
- Každý mapper před zápisem volá interaktivní `confirm_update()` — pipeline není plně automatická
- `nerds_db_filter.py` má v docstringu špatný název souboru (kosmetická chyba, funkčně OK)
- `job_database.db` je ~230 MB — velký soubor, existuje `job_database_original_backup.db`
- JSON sloupce v nerd_jobs musí být parsovány přes `parse_json_list()` (ošetřuje None, "", nevalidní JSON)
- Salary hodnoty < 1 000 PLN jsou interpretovány jako hodinová sazba × 160 = monthly

---

## Závislosti

```
# Scraping pipeline
cloudscraper                    # obcházení Cloudflare (pip install cloudscraper)
sqlite3, json, re, csv, pathlib, typing, abc, time, random  # stdlib

# Dashboard
streamlit>=1.35
pandas>=2.0
plotly>=5.20
sqlalchemy>=2.0
```

---

## Konvence kódu

- Type hints všude
- Template Method pattern v `base_mapper.py` → `mappers/*.py`
- Interaktivní `confirm_update()` před každým DB update v mapperech
- Dashboard: `@st.cache_data(ttl=3600)` pro DB dotazy
- Dashboard: Plotly chart funkce vracejí `go.Figure`

---

## Aktuální práce: TASK 9 — Visual Customization

Customization points:

| Co | Kde |
|----|-----|
| Barvy grafů (Plotly) | `components/charts.py` — `#636EFA`, `#EF553B` |
| Fonty grafů | `components/charts.py` — Plotly default |
| Globální téma | `.streamlit/config.toml` `[theme]` — prázdné |
| Názvy stránek v sidebar | názvy souborů v `pages/` |
| Titul v záložce | `st.set_page_config(page_title=...)` per stránka |
| Hlavní nadpis | `st.title(...)` per stránka |
| Custom CSS | neexistuje |

Postup: `config.toml [theme]` → `charts.py` barvy/fonty → stránky názvy/texty

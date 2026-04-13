# CLAUDE.md — Pracuj Scraper & Dashboard Project

## Project Overview
Web scraper pro **pracuj.pl** (polský job board). Stahuje pracovní nabídky, čistí data, filtruje IT role a vizualizuje výsledky v Streamlit dashboardu.

- **Vstup:** pracuj.pl search pages
- **Výstup:** `job_database.db` (všechny nabídky), `nerd_jobs.db` (IT role), Streamlit dashboard

---

## Pipeline (pořadí spuštění)

```
1. url_list_search2.0.py             →  job_urls_complete.json   (scrape URL z výsledků vyhledávání)
2. detail_scraper.py                 →  job_database.db           (scrape detailů každé nabídky)
3. db_cleaner/database_cleaner.py    →  job_database.db           (čištění a normalizace dat, in-place)
4. nerds_db_filter.py                →  nerd_jobs.db              (filtrování IT rolí)
5. dashboard/TOP_Skills.py           →  Streamlit Cloud            (vizualizace nerd_jobs.db)
```

---

## Klíčové soubory

### Scraping pipeline

| Soubor | Role |
|--------|------|
| `url_list_search2.0.py` | Scrape URL stránek s paginací, výstup JSON |
| `detail_scraper.py` | Scrape detailů každé nabídky → SQLite DB |
| `db_cleaner/database_cleaner.py` | Orchestrátor 9 mapperů (čištění DB) |
| `db_cleaner/base_mapper.py` | Abstraktní base class — Template Method pattern |
| `db_cleaner/mappers/*.py` | 9 mapperů: salary, monthly_salary, region, work_modes, work_schedules, employment_type, position_levels, industry, language |
| `nerds_db_filter.py` | Filtrovací skript (kw_title + monthly_max_salary) |
| `Nerd_mapped.csv` | Keyword mapping: title → mapped_title pro IT role |

### Archiv

| Soubor | Role |
|--------|------|
| `ARCH/` | Staré verze skriptů (`url_scraper.py`, `nerds_database.py`, `url_list_search2.0.py`) |
| `ARCH/csvCollection/` | Starší CSV exporty |
| `ARCH/Support/` | Pomocné soubory |

### Dashboard

| Soubor | Role |
|--------|------|
| `dashboard/TOP_Skills.py` | Hlavní stránka — Top Skills Overview |
| `dashboard/data/loader.py` | DB připojení, dotazy, datové transformace (`@st.cache_data`) |
| `dashboard/components/charts.py` | 3 Plotly chart funkce (skills_bar, salary_bar, jobs_bar) |
| `dashboard/pages/2_Salary_Per_Role.py` | Salary by Job Role (Median/Mean toggle) |
| `dashboard/pages/3_Salary_Per_Skill.py` | Salary by Skill (filtr kw_title, min 5 záznamů) |
| `dashboard/pages/4_Salary_Per_Level.py` | Salary by Seniority Level |
| `dashboard/pages/5_Jobs_Per_Region.py` | Job Postings by Region |

---

## DB schéma — tabulka `job_offers` (job_database.db)

Sloupce vytvořené v `detail_scraper.py`:

| Skupina | Sloupce |
|---------|---------|
| Identifikace | `partition_id` (PK), `url`, `title` |
| Firma | `company` |
| Plat | `salary_min`, `salary_max`, `salary_currency` |
| Lokalita | `region`, `city`, `postal_code` |
| Pracovní podmínky | `work_modes`, `work_schedules`, `employment_type`, `position_levels` |
| Obsah nabídky | `industry`, `description`, `technologies_os`, `technologies_optional`, `requirements_expected`, `we_offer`, `benefits` |
| Časové | `date_posted`, `valid_through` |

Sloupce přidané `db_cleaner` mappery (ALTER TABLE):

| Mapper | Přidané sloupce |
|--------|-----------------|
| `monthly_salary_mapper` | `monthly_max_salary` (REAL) |
| `industry_mapper` | `mapped_industry`, `kw_industry` |
| `language_mapper` | `mapped_languages` |

Pozn.: `salary_mapper` nepřidává sloupce — doplňuje hodnoty do existujících `salary_min`, `salary_max`, `salary_currency` z textu `we_offer`. `region_mapper` překládá anglické názvy regionů na polské in-place v sloupci `region`.

Detailní popis logiky industry mapperu viz [`db_cleaner/INDUSTRY_MAPPING.md`](db_cleaner/INDUSTRY_MAPPING.md).

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
- **`Support/`, `csvCollection/`** — lokální, nejsou na GitHubu (přesunuty do `ARCH/`)

---

## Upozornění / Gotchas

- **`db_cleaner`**: `database_cleaner.py` automaticky hledá DB v `Path(__file__).parent.parent`, ale mappery importují `base_mapper` relativně — spouštět z `db_cleaner/` složky nebo jako `python db_cleaner/database_cleaner.py` s nastaveným PYTHONPATH
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

## Next Steps

Viz [`NEXT_STEPS.md`](NEXT_STEPS.md) — plánované vylepšení:

1. **Paralelizace detail_scraper.py** — ThreadPoolExecutor, konfigurovatelný `--workers N`, z 40-78h na ~10h
2. **Historická data + trendové grafy** — CSV append logy, `snapshot_history.py`, nová Streamlit stránka `6_Trends.py`

---

## Visual Customization (TASK 9 — dokončeno)

| Co | Kde |
|----|-----|
| Barvy grafů (Plotly) | `components/charts.py` — `#22D3EE` (Median/skills), `#F43F5E` (Mean) |
| Fonty grafů + celá app | Space Grotesk (`components/charts.py` + CSS na všech stránkách) |
| Globální téma | `.streamlit/config.toml` `[theme]` |
| Názvy stránek v sidebar | názvy souborů v `pages/` (PascalCase) |
| Titul v záložce | `st.set_page_config(page_title=...)` per stránka |
| Hlavní nadpis | `st.title(...)` per stránka |
| Projekt titulek (sidebar) | CSS `::before` pseudo-element na `[data-testid='stSidebarNav']` |
| Custom CSS | inline `<style>` na každé stránce (font, sidebar nav 130%, h1 36px, h3 60px) |

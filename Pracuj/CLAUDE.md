# CLAUDE.md — Pracuj Scraper Project

## Project Overview
Web scraper pro **pracuj.pl** (polský job board). Stahuje pracovní nabídky, čistí data a filtruje IT role.

- **Vstup:** pracuj.pl search pages
- **Výstup:** `job_database.db` (všechny nabídky), `nerd_jobs.db` (IT role)

---

## Pipeline (pořadí spuštění)

```
1. url_scraper.py          →  job_urls_complete.json   (scrape URL z výsledků vyhledávání)
2. detail_scraper.py       →  job_database.db           (scrape detailů každé nabídky)
3. db_cleaner/database_cleaner.py  →  job_database.db  (čištění a normalizace dat, in-place)
4. nerds_db_filter.py      →  nerd_jobs.db              (filtrování IT rolí)
```

---

## Klíčové soubory

| Soubor | Role |
|--------|------|
| `url_scraper.py` | Scrape URL stránek s paginací, výstup JSON |
| `detail_scraper.py` | Scrape detailů každé nabídky → SQLite DB |
| `db_cleaner/database_cleaner.py` | Orchestrátor 8 mapperů (čištění DB) |
| `db_cleaner/base_mapper.py` | Abstraktní base class — Template Method pattern |
| `db_cleaner/mappers/*.py` | 8 mapperů: salary, region, work_modes, schedules, employment_type, position_levels, industry, language |
| `nerds_db_filter.py` | **AKTUÁLNÍ** filtrovací skript (kw_title + monthly_max_salary) |
| `nerds_database.py` | **STARŠÍ** verze filtru (jen kw_title, bez salary normalizace) — nepoužívat |
| `Nerd_mapped.csv` | Keyword mapping: title → mapped_title pro IT role |

---

## DB schéma — tabulka `job_offers`

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

---

## Upozornění / Gotchas

- **`url_scraper.py` a `url_list_search2.0.py` jsou IDENTICKÉ** — duplikát, používat `url_scraper.py`
- **`nerds_db_filter.py` je NOVĚJŠÍ než `nerds_database.py`** navzdory názvům — vždy používat `nerds_db_filter.py`
- `nerds_db_filter.py` má v docstringu špatný název souboru (kosmetická chyba, funkčně OK)
- **`db_cleaner` musí být spouštěn ze své složky** kvůli relativním importům mapperů
- `job_database.db` je ~230 MB — velký soubor, existuje `job_database_original_backup.db`
- Každý mapper před zápisem volá interaktivní `confirm_update()` — pipeline není plně automatická

---

## Salary logika

Hodnoty `salary_min`/`salary_max` < 1 000 PLN jsou interpretovány jako **hodinová sazba** a převedeny: `× 160 = monthly`.

---

## Závislosti

```
cloudscraper      # jediná externí závislost (instalace: pip install cloudscraper)
sqlite3, json, re, csv, pathlib, typing, abc, time, random  # stdlib
```

---

## Konvence kódu

- Type hints všude
- Template Method pattern v `base_mapper.py` → `mappers/*.py`
- Interaktivní `confirm_update()` před každým DB update v mapperech

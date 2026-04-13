# Next Steps — Pracuj Scraper

Plánované vylepšení projektu, seřazené podle priority.

---

## 1. Paralelizace detail_scraper.py

**Problém:** Scraper běží sekvenčně — 1 URL za ~3.5s, celkem ~80k URL = 40-78 hodin.

**Cíl:** Paralelní scraping pomocí `ThreadPoolExecutor`, konfigurovatelný počet workerů přes CLI.

**Soubor:** `detail_scraper.py`

### Architektura

```
                    ┌── Worker 1 (vlastní cloudscraper session)
URL list ──split──► ├── Worker 2 (vlastní cloudscraper session)  ──► SQLite (WAL + Lock)
                    ├── Worker 3 (vlastní cloudscraper session)
                    └── Worker N ...
```

### Klíčové změny

| Komponenta | Aktuální stav | Nový stav |
|---|---|---|
| Zpracování URL | Sekvenční `for` loop | `ThreadPoolExecutor(max_workers=N)` |
| cloudscraper session | 1 sdílená | Per-worker (thread-local) |
| SQLite zápis | Bez zámku | `threading.Lock` + WAL mode |
| Rate-limit backoff | Per-scraper counter | Globální `threading.Event`, všichni pausnou |
| Spuštění | `python detail_scraper.py` | `python detail_scraper.py --workers 6` |

### Thread-safety

| Sdílený resource | Řešení |
|---|---|
| `cloudscraper` session | Thread-local — každý worker vytvoří vlastní |
| SQLite writes | `threading.Lock` kolem `save_to_database()` + WAL journal mode |
| `successful`/`failed` countery | `threading.Lock` |
| `consecutive_fails` / backoff | `threading.Lock` + `threading.Event` — při 5× fail všichni čekají 120s |
| `self.failed_urls` list | `threading.Lock` kolem append |

### Delay/backoff logika (zachována per worker)

- Delay po requestu: `random.uniform(1.5, 2.2)s` — **stejný jako teď**, ale paralelně
- Batch break: progress report každých 100 dokončených URL
- Rate-limit: 5× consecutive fail → globální pauza 120s pro všechny workery
- Retry: 3 pokusy per URL, exponential backoff (`2 × retry_count`)

### Zpětná kompatibilita

- `scrape_all_urls()` (stará sekvenční metoda) zůstane beze změny
- Nová `scrape_all_urls_parallel()` jako default v `__main__`
- `--workers 1` = efektivně sekvenční běh

### Očekávaný výkon

| Workery | Odhad (80k URL) |
|---|---|
| 1 | ~40-78h (jako teď) |
| 4 | ~10-20h |
| 6 | ~7-13h |
| 8 | ~5-10h |

### Verifikace

1. `--workers 1` → ověřit, že funguje jako předtím
2. `--workers 4` → sledovat progress, ověřit paralelní běh
3. Po runu: `SELECT COUNT(*) FROM job_offers` — žádné chybějící/zduplikované záznamy
4. Sledovat consecutive fails — pokud příliš failů, snížit počet workerů

---

## 2. Historická data — trendové grafy

**Problém:** Žádná historická data o vývoji trhu. Každý scrape run přepisuje předchozí stav.

**Cíl:** Sledovat vývoj počtu nabídek per role (IT) a per industry (celý trh) v čase. Nová Streamlit stránka s line chartem.

### Řešení: CSV append logy

| Soubor | Zdroj DB | Formát |
|--------|----------|--------|
| `dashboard/data/history_roles.csv` | `nerd_jobs.db` | `date, kw_title, job_count` |
| `dashboard/data/history_industries.csv` | `job_database.db` | `date, mapped_industry, job_count` |

**Proč CSV:** Git-friendly (textový diff), žádný binární merge conflict, triviální načtení přes `pd.read_csv()`, malá velikost (~KB i po roce).

### Nový skript: `snapshot_history.py`

Spouští se jako krok 5 v pipeline po `nerds_db_filter.py`:

```
1. url_list_search2.0.py  →  job_urls_complete.json
2. detail_scraper.py      →  job_database.db
3. db_cleaner/            →  job_database.db (čištění)
4. nerds_db_filter.py     →  nerd_jobs.db
5. snapshot_history.py    →  history_roles.csv + history_industries.csv  ← NOVÉ
6. dashboard/             →  Streamlit Cloud
```

Logika:
- Přečte obě DB, spočítá `COUNT(*) GROUP BY kw_title` / `GROUP BY mapped_industry`
- Appendne řádky s aktuálním datem do CSV souborů
- Pokud CSV neexistuje, vytvoří ho s headerem

### Nová dashboard stránka: `dashboard/pages/6_Trends.py`

- Plotly line chart
- Filtr per role / industry
- Osa X = datum, osa Y = počet nabídek
- Reuse `dashboard/components/charts.py` pro styling

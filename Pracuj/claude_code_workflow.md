# Claude Code Workflow — nerd_jobs Streamlit Dashboard

## Kontext projektu

Cílem je postavit interaktivní webový dashboard v Streamlit nad SQLite databází `nerd_jobs.db`, tabulka `nerd_jobs`. Dashboard vizualizuje data-driven job market (EDA) a bude nasazen na Streamlit Community Cloud. Vývoj probíhá ve VSCode se zapnutým Claude Code v terminálu.

**Nepište žádný kód dříve, než je daný task explicitně zadán.**

---

## Tech stack

| Vrstva | Nástroj |
|---|---|
| Databáze | SQLite — `nerd_jobs.db` |
| Backend / data | Python 3.11+, Pandas, SQLAlchemy |
| Vizualizace | Plotly Express |
| Web framework | Streamlit |
| Deployment | Streamlit Community Cloud |

---

## Struktura projektu (vytvořit)

Všechny nové soubory patří do složky `dashboard/` uvnitř stávajícího projektu `Pracuj/`:

```
Pracuj/
├── [stávající scraping soubory — nesahat]
├── job_database.db
├── nerd_jobs.db
│
└── dashboard/
    ├── app.py                        ← Hlavní stránka (Skills overview)
    ├── pages/
    │   ├── 2_salary_per_role.py
    │   ├── 3_salary_per_skill.py
    │   ├── 4_salary_per_level.py
    │   └── 5_jobs_per_region.py
    ├── data/
    │   └── loader.py                 ← Veškeré DB dotazy a parsing
    ├── components/
    │   └── charts.py                 ← Znovupoužitelné Plotly funkce
    └── requirements.txt
```

---

## Schéma tabulky `nerd_jobs`

```
Databáze:  nerd_jobs.db
Tabulka:   nerd_jobs
Počet sloupců: 28
```

| cid | name | type | Poznámka |
|---|---|---|---|
| 0 | partition_id | TEXT | |
| 1 | url | TEXT | Unikátní identifikátor záznamu |
| 2 | industry | TEXT | |
| 3 | company | TEXT | |
| 4 | title | TEXT | Surový titulek |
| 5 | kw_title | TEXT | Mapovaná kategorie role — použít pro filtry |
| 6 | description | TEXT | |
| 7 | employment_type | TEXT | |
| 8 | salary_min | INTEGER | |
| 9 | salary_max | INTEGER | |
| 10 | salary_currency | TEXT | |
| 11 | monthly_max_salary | REAL | **Primární salary sloupec pro všechny vizualizace** |
| 12 | city | TEXT | |
| 13 | region | TEXT | |
| 14 | postal_code | TEXT | |
| 15 | position_levels | TEXT | JSON array, např. `["specialist"]` |
| 16 | work_schedules | TEXT | |
| 17 | work_modes | TEXT | |
| 18 | technologies_os | TEXT | JSON array, např. `["Python", "SQL"]` |
| 19 | technologies_optional | TEXT | JSON array nebo prázdný string `""` |
| 20 | requirements_expected | TEXT | |
| 21 | we_offer | TEXT | |
| 22 | benefits | TEXT | |
| 23 | date_posted | DATE | |
| 24 | valid_through | DATE | |
| 25 | mapped_industry | TEXT | |
| 26 | kw_industry | TEXT | |
| 27 | mapped_languages | TEXT | |

---

## Kritické technické poznámky

### JSON sloupce — povinné ošetření

Sloupce `technologies_os`, `technologies_optional` a `position_levels` jsou uloženy jako JSON arrays v TEXT poli.

**Vzorová data:**
```
technologies_os:       ["BPMN", "SQL", "Azure OpenAI", "ML Studio"]
technologies_optional: ""           ← může být prázdný string místo "[]"
position_levels:       ["specialist"]
```

**Pravidlo pro loader:** Každý JSON sloupec musí být parsován funkcí, která ošetří oba případy:
```python
import json

def parse_json_list(value):
    if not value or value.strip() == "":
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []
```

### Skills — kombinace dvou sloupců

Všude kde se pracuje se skills, je nutné **sloučit** `technologies_os` a `technologies_optional` do jednoho seznamu na úrovni každého záznamu. Duplicity v rámci jednoho záznamu odstraňovat, ale skill který se vyskytuje u více různých záznamů se počítá vícekrát.

### Salary — výhradně `monthly_max_salary`

Veškeré salary výpočty (Median, Mean) pracují **pouze** se sloupcem `monthly_max_salary` (REAL). Záznamy kde je `monthly_max_salary` NULL nebo 0 se ze salary výpočtů vylučují. Na count vizualizace (stránka 5) toto omezení neplatí.

---

## TASK 0 — Inicializace projektu

**Pořadí: první**

1. Vytvořit složkovou strukturu `dashboard/` dle schématu výše
2. Vytvořit `requirements.txt` s těmito závislostmi:
   ```
   streamlit>=1.35
   pandas>=2.0
   plotly>=5.20
   sqlalchemy>=2.0
   ```
3. Vytvořit `.streamlit/config.toml` uvnitř `dashboard/` s nastavením:
   - layout: wide
   - sidebar defaultně rozbalený
4. Ověřit, že `nerd_jobs.db` je dostupná relativní cestou z `dashboard/`

**Výstup tasku:** Prázdná funkční struktura, spustitelná příkazem `streamlit run app.py` bez chyb.

---

## TASK 1 — `data/loader.py`

**Pořadí: druhý — vše ostatní závisí na tomto modulu**

Vytvořit centrální datový modul se dvěma typy funkcí:

### 1A — Připojení k databázi

Funkce `get_connection()` která vrací SQLAlchemy engine nebo sqlite3 connection na `nerd_jobs.db`. Cesta k DB musí být dynamická (relativní vůči umístění `loader.py`), aby fungovala i po nasazení.

Výsledky dotazů cachovat pomocí `@st.cache_data` s TTL 1 hodina.

### 1B — Datové funkce (načíst celou tabulku jednou, filtrovat v Pandas)

```
load_all_jobs()
    → pd.DataFrame, všechny záznamy z nerd_jobs
    → JSON sloupce (technologies_os, technologies_optional, position_levels)
      jsou ihned parsovány do Python lists pomocí parse_json_list()
    → cachovat @st.cache_data

get_kw_title_options(df)
    → sorted list unikátních hodnot kw_title (bez NULL)
    → přidat možnost "All" jako první položku

get_region_options(df)
    → sorted list unikátních hodnot region (bez NULL)
    → přidat možnost "All" jako první položku

get_skills_counts(df, kw_title_filter=None)
    → sloučí technologies_os + technologies_optional per záznam
    → aplikuje kw_title_filter pokud není "All"
    → vrátí pd.Series: skill → count, seřazeno sestupně

get_salary_per_kw_title(df)
    → filtrovat: monthly_max_salary IS NOT NULL AND > 0
    → groupby kw_title → Median, Mean monthly_max_salary
    → vrátit DataFrame: [kw_title, median_salary, mean_salary]
    → seřadit podle median_salary sestupně

get_salary_per_skill(df, kw_title_filter=None)
    → rozbalit skills (technologies_os + technologies_optional) do řádků
    → filtrovat: monthly_max_salary IS NOT NULL AND > 0
    → aplikovat kw_title_filter pokud není "All"
    → groupby skill → Median, Mean monthly_max_salary
    → vrátit DataFrame: [skill, median_salary, mean_salary, count]
    → seřadit podle median_salary sestupně

get_salary_per_level(df, kw_title_filter=None)
    → rozbalit position_levels do řádků (jeden záznam může mít více levels)
    → filtrovat: monthly_max_salary IS NOT NULL AND > 0
    → aplikovat kw_title_filter pokud není "All"
    → groupby position_levels → Median, Mean monthly_max_salary
    → vrátit DataFrame: [level, median_salary, mean_salary, count]
    → seřadit podle median_salary sestupně

get_jobs_per_region(df, kw_title_filter=None)
    → aplikovat kw_title_filter pokud není "All"
    → groupby region → count(url)
    → vrátit DataFrame: [region, job_count]
    → seřadit podle job_count sestupně
```

**Výstup tasku:** `loader.py` s všemi funkcemi, otestovaný samostatně (rychlý print test v `__main__` bloku).

---

## TASK 2 — `components/charts.py`

**Pořadí: třetí**

Znovupoužitelné Plotly Express funkce. Každá funkce vrací `plotly.graph_objects.Figure`.

```
make_skills_bar(skills_series, top_n=20, title="")
    → horizontální bar chart
    → osa X: count, osa Y: skill název
    → zobrazit Top N (default 20), seřazeno vzestupně (největší nahoře)
    → barvy: jednotná barva celého grafu (ne gradient)

make_salary_bar(df, x_col, title="", show_median=True, show_mean=True)
    → horizontální bar chart
    → podporuje zobrazení Median, Mean nebo obou jako grouped bars
    → osa X: monthly_max_salary (CZK), osa Y: kategorie (role/skill/level)
    → formát čísel na ose X: tisíce s mezerou (např. "50 000")
    → tooltip: přesná hodnota + count záznamů

make_jobs_bar(df, x_col="job_count", y_col="region", title="")
    → horizontální bar chart
    → osa X: počet jobů, osa Y: region
    → seřazeno sestupně (nejvíce nahoře)
    → tooltip: přesný count
```

**Výstup tasku:** `charts.py` se třemi funkcemi.

---

## TASK 3 — `app.py` (Hlavní stránka — Skills Overview)

**Vizualizace:** Top 20 skills bar chart
**Filtr:** `kw_title` (selectbox, default "All")
**Salary:** není

**Specifikace stránky:**
1. Načíst data přes `loader.load_all_jobs()`
2. Sidebar: selectbox `kw_title` s opcemi z `get_kw_title_options()`
3. Hlavní oblast: horizontální bar chart Top 20 skills z `get_skills_counts()` → `make_skills_bar()`
4. Pod grafem: malá tabulka (st.dataframe) s kompletním skill rankinkem (všechny skills, ne jen top 20) — skrytá za `st.expander("Zobrazit kompletní tabulku")`
5. Nadpis stránky: "Top Skills in Data Jobs"
6. Popisek pod nadpisem: počet analyzovaných záznamů (dynamický, reaguje na filtr)

---

## TASK 4 — `pages/2_salary_per_role.py`

**Vizualizace:** Median + Mean `monthly_max_salary` per `kw_title`
**Filtr:** žádný
**Salary sloupec:** `monthly_max_salary`

**Specifikace stránky:**
1. Načíst data přes `loader.load_all_jobs()`
2. Žádný sidebar filtr na této stránce
3. Toggle (st.radio nebo st.toggle) pro přepínání: "Median" / "Mean" / "Oba"
4. Horizontální bar chart z `get_salary_per_kw_title()` → `make_salary_bar()`
5. Pod grafem: počet záznamů se salary daty (monthly_max_salary NOT NULL > 0)
6. Nadpis: "Salary by Job Role"

---

## TASK 5 — `pages/3_salary_per_skill.py`

**Vizualizace:** Median + Mean `monthly_max_salary` per skill
**Filtr:** `kw_title` (sidebar selectbox)
**Salary sloupec:** `monthly_max_salary`

**Specifikace stránky:**
1. Načíst data přes `loader.load_all_jobs()`
2. Sidebar: selectbox `kw_title` (default "All")
3. Toggle: "Median" / "Mean" / "Oba"
4. Horizontální bar chart z `get_salary_per_skill()` → `make_salary_bar()`
5. Zobrazit pouze skills s alespoň 5 záznamy (zabránit zkreslení na vzorcích)
6. Nadpis: "Salary by Skill"

---

## TASK 6 — `pages/4_salary_per_level.py`

**Vizualizace:** Median + Mean `monthly_max_salary` per `position_levels`
**Filtr:** `kw_title` (sidebar selectbox)
**Salary sloupec:** `monthly_max_salary`

**Specifikace stránky:**
1. Načíst data přes `loader.load_all_jobs()`
2. Sidebar: selectbox `kw_title` (default "All")
3. Toggle: "Median" / "Mean" / "Oba"
4. Horizontální bar chart z `get_salary_per_level()` → `make_salary_bar()`
5. Nadpis: "Salary by Seniority Level"

---

## TASK 7 — `pages/5_jobs_per_region.py`

**Vizualizace:** Count(`url`) per `region` — bar chart
**Filtr:** `kw_title` (sidebar selectbox, optional)
**Salary:** není

**Specifikace stránky:**
1. Načíst data přes `loader.load_all_jobs()`
2. Sidebar: selectbox `kw_title` (default "All" = zobrazit všechny regiony bez filtru)
3. Horizontální bar chart z `get_jobs_per_region()` → `make_jobs_bar()`
4. Nad grafem: celkový počet zobrazených záznamů (dynamický)
5. Nadpis: "Job Postings by Region"

---

## TASK 8 — Deployment na Streamlit Community Cloud

**Pořadí: poslední — až jsou všechny stránky funkční lokálně**

1. Přidat `dashboard/` do GitHub repozitáře (nebo vytvořit nový)
2. Vytvořit `.streamlit/secrets.toml` pro lokální vývoj (prázdný nebo DB cesta)
3. Na Streamlit Community Cloud:
   - Main file path: `dashboard/app.py`
   - `nerd_jobs.db` musí být součástí repozitáře (pokud není příliš velká — limit 100MB)
   - Pokud DB > 100MB: konzultovat alternativu (SQLite → DuckDB nebo hosted DB)
4. Ověřit, že `requirements.txt` je v `dashboard/` složce

---

## Pořadí tasků (pro Claude Code)

```
TASK 0 → TASK 1 → TASK 2 → TASK 3 → TASK 4 → TASK 5 → TASK 6 → TASK 7 → TASK 8
```

Každý task testovat samostatně před zahájením dalšího. TASK 1 (`loader.py`) je kritická závislost — bez ní nelze spustit žádnou stránku.

---

## Otevřené otázky (rozhodnout v průběhu produkce)

- Stránka 3 (Salary per skill): zobrazovat absolutní počty nebo procenta zastoupení skills?
- Stránka 5 (Jobs per region): přidat možnost přepnutí na `kw_title` jako primární osu?
- Vizuální téma dashboardu: default Streamlit nebo custom CSS?
- Minimální počet záznamů pro salary výpočet (aktuálně navrženo: 5) — potvrdit po prvním spuštění

---

*Dokument verze 1.0 — připraven jako podklad pro Claude Code tasky*

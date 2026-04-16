# Project brief: Pracuj_all_viz — Poland Labour Market EDA

> Tento dokument je most mezi Cowork (plánování) a Code (implementace).
> Vyplněno v Cowork fázi — Claude Code ho automaticky načte jako kontext.

---

## 1. Cíl projektu

**Co stavíme?**
Explorativní datová analýza (EDA) polského trhu práce — série publikovatelných statických PNG vizualizací (bar charty, geo choropleth mapa, heatmapy) doplněných textovým narativem na webu.

**Proč to stavíme?**
Odhalit klíčové trendy a vztahy v datech pracovních nabídek z polského trhu (počty, regiony, mzdy, odvětví, typy úvazku). Výstup slouží jako web článek — analytická studie s vlastním narativem.

**Jak poznáme, že je to hotové?**
- Všechny skripty běží bez chyb z rootu projektu
- PNG grafy exportovány do `outputs/figures/`
- Geo mapa vojvodství vygenerována a čitelná

---

## 2. Kontext a rozhodnutí

### Klíčová rozhodnutí

| Rozhodnutí | Zvolená varianta | Důvod |
|---|---|---|
| Tech stack | Python (pandas, matplotlib, seaborn, geopandas) | Standardní DA stack, bez interaktivity |
| Databáze | SQLite (`data/job_database.db`) | Lokální, bez externích závislostí |
| Vizualizace | Pouze statické PNG — matplotlib/seaborn + geopandas | Web článek nevyžaduje interaktivitu |
| Geo data | GeoJSON vojvodství (`data/geo/`) | Volně dostupný, napojení přes `region` sloupec |
| IDE | VSCode + Jupyter notebooky | Experiment v notebooku, produkce v skriptech |

### Omezení a hranice

- **Musí mít:** Statické PNG grafy, geo mapa vojvodství, skripty spustitelné samostatně
- **Nesmí mít:** Interaktivní dashboard, cloudové závislosti, externí API (Plotly se používá výhradně pro statický PNG export treemap přes kaleido)
- **Prostředí:** Lokální Python 3.11+, Windows

### Cílový uživatel

Čtenáři datového blogu na vlastní doméně (sekce `domena.com/data-analyst/`). Výstup je web článek s textovým narativem a vloženými statickými PNG grafy — žádná interaktivita.

### Publikační platforma

WordPress Multisite na Hostingeru — sekce `domena.com/data-analyst/`. PNG grafy se nahrají jako obrázky přímo do příspěvku.

---

## 3. Specifikace pro implementaci

### Struktura projektu

```
Pracuj_all_viz/
├── brief.md                        ← Tento soubor
├── CLAUDE.md                       ← Project-level instrukce pro Code
├── requirements.txt                ← Python závislosti
├── data/
│   ├── job_database.db             ← SQLite databáze (65 401 řádků)
│   ├── fonts/                      ← Inter TTF fonty (Light, Regular, SemiBold, ExtraBold)
│   └── geo/
│       └── poland_voivodeships.geojson  ← stáhnout před spuštěním 03_geo_map.py
├── scripts/
│   ├── db_connection.py            ← Helper — připojení k DB
│   ├── download_fonts.py           ← Stažení Inter fontů do data/fonts/
│   ├── 01_eda_summary.py           ← EDA overview + CSV profily
│   ├── 02_visualizations.py        ← Bar charty, heatmapy, ridge ploty → PNG
│   ├── 03_geo_map.py               ← Choropleth mapy vojvodství → PNG
│   └── 04_treemap_sankey.py        ← Nested treemapy + Sankey → PNG
├── notebooks/                      ← Jupyter experimenty
└── outputs/
    ├── figures/                    ← Všechny PNG výstupy
    └── reports/                    ← CSV profily, souhrny
```

### Seznam vizualizací

| # | Typ | Obsah | Knihovna | Poznámka |
|---|---|---|---|---|
| 1 | Geo choropleth | Počet nabídek / vojvodství + % z celku | geopandas | |
| 2 | Bar chart | Počet nabídek podle mapped_industry | seaborn | |
| 3 | Sankey diagram | Top 10 Industries → 16 Voivodeships | pySankey | industry → region |
| 4 | Tabulková heatmapa | Vojvodství × mapped_industry, absolutní čísla | seaborn | pivot tabulka |
| 5 | Bar chart | position_level (>1000 nabídek), s % | seaborn | |
| 7 | Bar chart | work_modes | seaborn | |
| 8 | Nested Treemap | Top 20 Cities → work_modes (% nabídek) | plotly + kaleido | export jako PNG |
| 9a | Geo choropleth | Mediánový plat (střed min–max) / vojvodství | geopandas | mako_r |
| 9b | Ridge Plot | monthly_max_salary podle vojvodství | seaborn FacetGrid | overlapping, mako styl |
| 10 | Ridge Plot | monthly_max_salary podle work_modes | seaborn FacetGrid | overlapping, mako styl |
| 11 | Ridge Plot | monthly_max_salary podle position_level | seaborn FacetGrid | overlapping, mako styl |
| 12 | Ridge Plot | monthly_max_salary podle mapped_industry | seaborn FacetGrid | overlapping, mako styl |
| 13 | Nested Treemap | Top 20 Cities → top 5 mapped_industry (% nabídek) | plotly + kaleido | export jako PNG |
| 14 | Tabulková heatmapa | Language × mapped_industry, absolutní čísla | seaborn | center=1800 |
| 15 | Sankey diagram | Top 10 Languages → Top 10 Industries | pySankey | language → industry |

### Fáze implementace

1. **Setup & DB** — ověřit připojení, prozkoumat schéma
2. **EDA přehled** — statistiky, null hodnoty, distribuce klíčových sloupců
3. **Bar charty** (č. 2, 5, 7) — seaborn → PNG
4. **Heatmapy** (č. 4) — seaborn pivot → PNG
5. **Ridge Ploty** (č. 9–12) — seaborn FacetGrid overlapping → PNG
6. **Geo mapa** (č. 1) — GeoJSON stáhnout, geopandas → PNG
7. **Treemapy** (č. 8, 13) — plotly nested → PNG přes kaleido
8. **Sankey** (č. 3) — pySankey → PNG

### Klíčové skripty

| Skript | Popis |
|---|---|
| `scripts/db_connection.py` | Helper modul — připojení k SQLite |
| `scripts/01_eda_summary.py` | EDA overview + CSV profily do `outputs/reports/` |
| `scripts/02_visualizations.py` | Bar charty, heatmapy, ridge ploty → `outputs/figures/` |
| `scripts/03_geo_map.py` | Choropleth mapy Polska → `outputs/figures/` |
| `scripts/04_treemap_sankey.py` | Nested treemapy + Sankey → `outputs/figures/` |

---

## 4. Handoff checklist

- [x] Cíl je jasný a měřitelný
- [x] Tech stack zvolený s odůvodněním
- [x] Databáze umístěna v `data/`
- [x] Struktura projektu definována
- [x] GeoJSON stažen do `data/geo/` — napojení 16/16 regionů ověřeno
- [x] EDA skripty otestovány na reálných datech
- [x] Geo mapa vojvodství funkční
- [x] Všech 15 PNG grafů vygenerováno do `outputs/figures/`

---

## 5. Poznámky z Cowork sessions

### Session 1 — 2026-03-24

- Projekt nastaven pomocí `da-project` skill
- `job_database.db` přesunut do `data/` podle workspace konvencí
- Chybějící dokumenty (brief.md, CLAUDE.md) doplněny

### Session 2 — 2026-03-25

- Rozhodnutí: flat struktura — `Pracuj_all_viz/` je root projektu, jeden projekt = jedna DB
- Zrušena zbytečná podsložka `poland-labour-market-eda/`
- Odstraněn 221 MB duplikát `labour_market.db` (identická s `job_database.db`)
- Skripty, notebooks, requirements.txt přesunuty do rootu projektu
- Path v `db_connection.py` aktualizován na `job_database.db`
- Rozhodnutí: výstup jsou statické PNG pro web článek — žádný interaktivní dashboard
- `03_dashboard.py` (Plotly) nahrazen `03_geo_map.py` (geopandas choropleth)
- `plotly` odstraněn z `requirements.txt`, přidány `geopandas` + `mapclassify`
- brief.md a CLAUDE.md aktualizovány dle finálního stacku a struktury

### Session 3 — 2026-03-26

**Color scales — finální stav:**
- Bar charty (č. 2, 5, 7): `sns.color_palette("mako_r", as_cmap=True)`
- Heatmapa (č. 4): `sns.color_palette("mako_r", as_cmap=True)`
- Treemapy (č. 8, 13): Plotly `"inferno"` / `"inferno_r"`
- Geo mapa (č. 1): `sns.color_palette("mako_r", as_cmap=True)`

**Grafy č. 6 odstraněny** (set 11 choropleth map position_level → redundantní). Celkový počet grafů: 12.

**Sankey (č. 3):**
- pySankey nainstalován a funkční (import fix: `from pySankey.sankey import sankey`)
- TOP 16 regionů × TOP 10 odvětví
- Color scale: `plt.cm.inferno` přes colorDict

**Bar charty — orientace:** všechny převedeny na horizontální `barh`, největší nahoře, bez filtru >1000 (č. 5).

**Typografie — Inter font:**
- Staženo do `data/fonts/`: Inter-Light, Regular, SemiBold, ExtraBold (TTF z Inter v3.19)
- Skript pro stažení: `scripts/download_fonts.py`
- Globální setup v `02_visualizations.py`: `_setup_inter_fonts()` + rcParams
- Tituly: Inter Light 300 | Osy/hodnoty: Inter Regular 400
- Bar charty Y labels + value annotations: Inter ExtraBold 800
- Heatmapa Y labels: Inter SemiBold 600
- **Zítra:** doladit fonty v jednotlivých grafech (ridge ploty, heatmapa, geo)

### Session 4 — 2026-04-09

**Typografie Inter — aplikována do všech skriptů:**
- `_setup_inter_fonts()` + `plt.rcParams.update()` přidáno do `03_geo_map.py` a `04_treemap_sankey.py`
- Plotly treemapy: `font=dict(family="Inter")` v `update_layout()` (vyžaduje systémový font)
- Sankey: explicitní `fontfamily="Inter"` v `plt.title()`
- Tituly sjednoceny na `fontweight=600` (Inter SemiBold) napříč všemi grafy

**Treemap č. 8 — změna hierarchie:**
- Z region → work_modes na **city → work_modes** (top 20 měst dle počtu nabídek)
- Funkce přejmenována: `plot_treemap_region_work_modes` → `plot_treemap_city_work_modes`

**Treemapy — vizuální sjednocení:**
- Fixní sdílený `color_continuous_midpoint=18` (obě treemapy)
- `title_font=dict(size=36, weight=600)` + `title_x=0.15`
- Buňky: `textfont=dict(size=20, family="Inter", weight=400)`
- `explode_col` opraveno: `.str.strip("[]\"'")` — odstranění závorek z JSON-encoded hodnot

**Geo mapy — kompletní přepracování:**
- `FONT_FAMILY` změněn z `"DejaVu Sans"` na `"Inter"`
- `CMAP_SALARY` změněn z `"Blues"` na `mako_r` (sjednocení s č. 1)
- Tituly: `fontsize=22, fontweight=600` (sjednocení s bar charty)
- Anotace: `fontweight=800` + dynamická barva textu (bílá/tmavá dle luminance pozadí)
- `fig.suptitle` místo `ax.set_title` pro lepší kontrolu pozice
- Přidán `midpoint` parametr (TwoSlopeNorm) pro fixní střed colorbar
- Přidán `show_pct` parametr — č. 1 zobrazuje `count\n(pct %)`
- Tituly přeloženy do angličtiny

**Geo č. 9 — nová salary mapa:**
- Metrika změněna z mean na **medián** (skewness 3.02, jen 33 % dat má plat)
- `aggregate()` rozšířena o výpočet mediánu (`salary_mid_median`)
- Soubor: `09_geo_salary_median.png`

### Session 5 — 2026-04-10

**Reverzní Sankey (č. 3):**
- Směr obrácen: **Industry → Region** (Top 10 Industries → 16 Voivodeships)
- Industries řazeny ascending (IT nahoře), voivodeships descending (Mazowieckie dole)
- pySankey bug workaround: ordering přes DataFrame row sort (`leftLabels`/`rightLabels` nelze použít — bug v `check_data_matches_labels`: `len(labels > 0)` místo `len(labels) > 0`)
- Inter SemiBold 600 na všechny text labels přes `fig.findobj(plt.Text)`

**Title format Voivodeship:**
- `.str.title()` aplikován v: heatmapě (č. 4), ridge by region (č. 9), Sankey (č. 3)
- Geo mapy nezobrazují region names v textu → není potřeba

**Bar chart č. 2:**
- Přidán `(pct %)` formát shodný s č. 5 a č. 7

**Heatmapa č. 4:**
- `center=1800` (midpoint barevné škály)

**Ridge ploty — kompletní reforma:**
- Paleta: `coolwarm` → `mako` (tmavé nahoře = vyšší medián platu)
- `sharey=False` — individuální Y-osa per facet (řešení neviditelných distribucí)
- `common_norm=False` — individuální normalizace KDE
- Filled KDE `linewidth=0` — odstranění shadow artefaktu v chvostu
- Bílá ohraničovací linka zachována (`lw=2`)
- Baseline (`axhline`) odstraněn — způsoboval viditelné čáry přes celou šířku
- Label pozice: `y=0.05` (blíž k baseline distribuce)
- `hspace=0.5` (oddělené, bez překrytí)
- Titulek: `fontweight=600` (Inter SemiBold)

### Session 6 — 2026-04-10

**Titulky přeloženy do angličtiny:**
- Všechny české titulky ve skriptech 02, 04 přepsány do EN
- Geo mapy (03) a Sankey (04) už měly anglické titulky

**Heatmapa č. 4 — labely smazány:**
- `ax.set_xlabel("")`, `ax.set_ylabel("")` — odstranění auto-generated labelů z pivot sloupců
- Colorbar label vyprázdněn

**Code cleanup (-73 řádků):**
- `02`: smazána nepoužívaná `load_data()`, 3× zakomentovaný `ax.set_xlabel`
- `03`: smazán unused `import mpatches`, sloučeny `CMAP_COUNT`/`CMAP_SALARY` → `CMAP`, vyčištěn `aggregate()` (smazány unused `salary_min_mean`, `salary_max_mean`, `salary_mid_mean`)
- `04`: smazán unused `import mticker`, unused SQL sloupec `position_levels`, unused `agg["label"]`, 48 řádků zakomentovaného fallback kódu
- `db_connection.py`: smazán zbytečný `row_factory = sqlite3.Row`

**Dokumentace opravena:**
- brief.md: handoff checklist zaškrtnut, struktura projektu aktualizována, duplicitní č. 9 přečíslován na 9a/9b, omezení Plotly upřesněno
- CLAUDE.md: aktuální stav doplněn

**Nové vizualizace — mapped_languages:**
- č. 14 Heatmapa: language × industry (center=1800, formát shodný s č. 4)
- č. 15 Sankey: Top 10 Languages → Top 10 Industries (formát shodný s č. 3)
- `_sankey_pysankey()` refaktorován na obecný `_render_sankey()` — sdílený pro č. 3 i č. 15
- `mapped_languages`: 29 % non-null, 10 jazyků, English 82 %, German 12 %

**GitHub push:**
- Projekt přidán do `JirinAdam/Portfolio` jako složka `DataViz_PracujPL/`
- DB (221 MB) vyloučena přes existující `.gitignore` (`*.db`)
- README.md vytvořen v angličtině

---

*Vytvořeno z šablony `templates/project-brief.md`*
*Poslední update: 2026-04-10*

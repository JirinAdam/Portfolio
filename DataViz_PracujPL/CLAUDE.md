# Projekt: Pracuj_all_viz — Poland Labour Market EDA

## Kontext
Explorativní analýza dat polského pracovního trhu. Výstupem jsou statické PNG vizualizace pro web článek — žádná interaktivita, žádný dashboard, žádný deployment.

## Cíl
12 publikovatelných PNG grafů (bar charty, geo choropleth, heatmapy, ridge ploty, treemapy, sankey) doplněných textovým narativem na webu (`domena.com/data-analyst/`).
Graf č. 6 (position_level choropleth sety) byl odstraněn jako redundantní.

## Data
- Zdroj: SQLite databáze s nabídkami práce z polského trhu
- Umístění: `data/job_database.db`
- Rozsah: 65 401 řádků, tabulka `job_offers`, 27 sloupců
- Klíčové sloupce: `salary_min`, `salary_max`, `monthly_max_salary`, `city`, `region`, `mapped_industry`, `employment_type`, `work_modes`, `position_levels`, `date_posted`
- `monthly_max_salary` má 66 % null hodnot — používat jen pro ridge ploty (distribuce), ne pro průměry
- Regiony: 16 vojvodství (`mazowieckie`, `śląskie`…) + `zagranica` — filtrovat při geo vizualizacích

## Stack
| Knihovna | Účel | Vizuály |
|---|---|---|
| `pandas`, `sqlite3` | Data | — |
| `matplotlib`, `seaborn` | Bar charty, heatmapy, ridge ploty | č. 2, 4, 5, 7, 9–12 |
| `geopandas`, `mapclassify` | Choropleth mapa Polska | č. 1 |
| `plotly` + `kaleido` | Nested treemapy → export PNG | č. 8, 13 |
| `pySankey` | Sankey diagram → PNG | č. 3 |

## Struktura projektu
```
Pracuj_all_viz/
├── CLAUDE.md
├── brief.md
├── requirements.txt
├── data/
│   ├── job_database.db
│   └── geo/
│       └── poland_voivodeships.geojson   ← stáhnout před spuštěním 03_geo_map.py
├── scripts/
│   ├── db_connection.py       ← helper: připojení k DB
│   ├── 01_eda_summary.py      ← EDA overview + CSV profily
│   ├── 02_visualizations.py   ← bar charty, heatmapy, ridge ploty → outputs/figures/
│   ├── 03_geo_map.py          ← choropleth mapy → outputs/figures/
│   └── 04_treemap_sankey.py   ← nested treemapy + sankey → outputs/figures/
├── notebooks/
└── outputs/
    ├── figures/               ← všechny PNG výstupy
    └── reports/               ← CSV profily, souhrny
```

## Aktuální stav
- [x] DB připojení ověřeno
- [x] GeoJSON stažen do `data/geo/`
- [x] EDA summary hotové
- [x] Bar charty + heatmapy hotové (č. 2, 4, 5, 7) — horizontální, mako_r, s pct
- [x] Ridge ploty hotové (č. 9–12) — mako, sharey=False, individuální KDE normalizace
- [x] Geo mapy hotové (č. 1, 9) — mako_r, dynamická barva textu, fixní midpoint
- [x] Treemapy + Sankey hotové (č. 3, 8, 13) — inferno / inferno_r, fixní midpoint=18
- [x] Typografie Inter — aplikována ve všech 3 skriptech (02, 03, 04)
- [x] Geo č. 9: salary metrika změněna z mean na **medián** (skewness 3.02, jen 33 % dat má plat)
- [x] Treemap č. 8: hierarchie změněna z region → **city** (top 20 měst → work_modes)
- [x] Reverzní Sankey: Top 10 Industries → 16 Voivodeships (industry → region)
- [x] Sankey fonty — Inter SemiBold 600 na všechny labels
- [x] č. 4 Heatmapa: midpoint `center=1800`
- [x] Title format "Voivodeship" — `.str.title()` ve všech figures (č. 3, 4, 9 ridge)
- [x] č. 2 Bar chart: přidán pct (jako č. 5, 7)
- [x] Kompletní reforma Ridge plotů (mako, sharey=False, linewidth=0, hspace=0.0)

## Klíčové proměnné
| Název | Typ | Popis |
|---|---|---|
| `df` | DataFrame | Surová data z DB |
| `conn` | sqlite3.Connection | Připojení k DB |
| `gdf` | GeoDataFrame | Spojená geo + analytická data |

## Typografie
- Font: **Inter** (TTF v `data/fonts/`, registrace v `_setup_inter_fonts()` — všechny 3 skripty)
- Plotly: `font=dict(family="Inter")` v `update_layout()` (vyžaduje Inter jako systémový font)
- Tituly (matplotlib): Inter SemiBold 600 (`fontweight=600`)
- Tituly (Plotly): `title_font=dict(size=36, weight=600)`
- Osy, hodnoty, labels: Inter Regular 400 (výchozí rcParams)
- Bar Y labels + value annotations: Inter ExtraBold 800
- Heatmapa Y labels: Inter SemiBold 600
- Geo anotace: Inter ExtraBold 800, dynamická barva (bílá/tmavá dle luminance pozadí)
- Treemap buňky: Inter Regular 400, size=20
- Sankey: Inter SemiBold 600 na všechny labels (`fig.findobj(plt.Text)`), titulek explicitní `fontfamily="Inter"`
- Ridge ploty: Inter SemiBold 600 labels (barva = barva výplně skupiny), titulek fontweight=600

## Konvence
- Kód anglicky, komentáře česky
- Názvy souborů: `RRRR-MM-DD_nazev-grafu.png`
- DPI grafů: 150 (web)
- Skripty jsou idempotentní — lze spouštět opakovaně
- `zagranica` filtrovat z geo vizualizací, lze zachovat v ostatních grafech
- Ridge ploty: seaborn FacetGrid overlapping styl (viz seaborn docs `kde_ridgeplot`)
- Treemapy: plotly `px.treemap` s hierarchií, export přes `fig.write_image()` (kaleido)
- Sankey: pySankey, emergency fallback = stacked bar chart (zdokumentováno v brief.md)

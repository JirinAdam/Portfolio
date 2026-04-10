# Poland Labour Market — Data Visualization

Exploratory data analysis of the Polish job market based on 65,000+ job listings scraped from Pracuj.pl. The project produces 15 publication-ready static PNG visualizations for a web article.

## Visualizations

| # | Type | Description |
|---|---|---|
| 1 | Geo choropleth | Job offers by voivodeship (count + %) |
| 2 | Bar chart | Job offers by industry |
| 3 | Sankey diagram | Top 10 industries &rarr; 16 voivodeships |
| 4 | Heatmap | Voivodeship &times; industry |
| 5 | Bar chart | Job offers by position level |
| 7 | Bar chart | Job offers by work mode |
| 8 | Treemap | Top 20 cities &rarr; work modes |
| 9a | Geo choropleth | Median salary by voivodeship |
| 9b | Ridge plot | Salary distribution by voivodeship |
| 10 | Ridge plot | Salary distribution by work mode |
| 11 | Ridge plot | Salary distribution by position level |
| 12 | Ridge plot | Salary distribution by industry |
| 13 | Treemap | Top 20 cities &rarr; top 5 industries |
| 14 | Heatmap | Language &times; industry |
| 15 | Sankey diagram | Top 10 languages &rarr; top 10 industries |

## Tech Stack

- **Data:** Python, pandas, SQLite
- **Visualizations:** matplotlib, seaborn, geopandas, Plotly (static PNG export via kaleido), pySankey
- **Typography:** Inter font family (Light, Regular, SemiBold, ExtraBold)

## Project Structure

```
DataViz_PracujPL/
├── scripts/
│   ├── db_connection.py          # DB connection helper
│   ├── 01_eda_summary.py         # EDA overview + CSV profiles
│   ├── 02_visualizations.py      # Bar charts, heatmaps, ridge plots
│   ├── 03_geo_map.py             # Choropleth maps
│   └── 04_treemap_sankey.py      # Treemaps + Sankey diagram
├── data/
│   ├── fonts/                    # Inter TTF fonts
│   └── geo/                      # Poland voivodeships GeoJSON
├── outputs/
│   └── figures/                  # All PNG outputs
└── requirements.txt
```

## How to Run

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Place the SQLite database as `data/job_database.db`, then run scripts in order:

```bash
python scripts/01_eda_summary.py
python scripts/02_visualizations.py
python scripts/03_geo_map.py
python scripts/04_treemap_sankey.py
```

All outputs are saved to `outputs/figures/`.

## Data Source

Job listings scraped from [Pracuj.pl](https://www.pracuj.pl/) — 65,401 rows, 27 columns. The SQLite database is not included in the repository due to size (221 MB).

"""
03_geo_map.py
-------------
Choropleth mapy polského trhu práce podle vojvodství (województw).
Výstup: PNG soubory do outputs/figures/

Generuje:
    č. 1  — Geo choropleth: počet nabídek / vojvodství + % z celku
    č. 9  — Geo choropleth: mediánový plat (střed min–max) / vojvodství

Font: Inter (registrace přes _setup_inter_fonts(), stejná jako 02/04)
Color palette: mako_r (obě mapy)
Dynamická barva textu: bílá na tmavém pozadí, tmavá na světlém (luminance threshold)

Předpoklady:
    GeoJSON s hranicemi vojvodství musí být uložen v:
    data/geo/poland_voivodeships.geojson

    Stažení:
    https://github.com/ppatrzyk/polska-geojson/raw/master/wojewodztwa/wojewodztwa-medium.geojson

Run from project root:
    python scripts/03_geo_map.py
"""

import sys
import sqlite3
import pandas as pd
import seaborn as sns
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.db_connection import get_connection


def _setup_inter_fonts():
    """Zaregistruje Inter fonty z lokálního data/fonts/. Fallback: DejaVu Sans."""
    fonts_dir = Path(__file__).parent.parent / "data" / "fonts"
    for ttf in ["Inter-Light.ttf", "Inter-Regular.ttf", "Inter-SemiBold.ttf", "Inter-ExtraBold.ttf"]:
        path = fonts_dir / ttf
        if path.exists():
            fm.fontManager.addfont(str(path))

_setup_inter_fonts()

plt.rcParams.update({
    "figure.dpi": 150,
    "font.family": "Inter",
    "font.weight": 400,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

# --- Cesty ---
GEO_PATH = Path(__file__).parent.parent / "data" / "geo" / "poland_voivodeships.geojson"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TODAY = date.today().isoformat()

# --- Styl ---
CMAP_COUNT   = sns.color_palette("mako_r", as_cmap=True)   # počet nabídek
CMAP_SALARY  = sns.color_palette("mako_r", as_cmap=True)   # průměrný plat
FIG_DPI      = 150
BORDER_COLOR = "white"
BORDER_WIDTH = 0.6
FONT_FAMILY  = "Inter"


def load_geo() -> gpd.GeoDataFrame:
    """Načte GeoJSON vojvodství. Normalizuje názvy na lowercase bez mezer."""
    if not GEO_PATH.exists():
        raise FileNotFoundError(
            f"\nGeoJSON nenalezen: {GEO_PATH}\n"
            "Stáhni ho příkazem:\n"
            "  mkdir -p data/geo && curl -L -o data/geo/poland_voivodeships.geojson \\\n"
            "  https://github.com/ppatrzyk/polska-geojson/raw/master/wojewodztwa/wojewodztwa-medium.geojson\n"
        )
    gdf = gpd.read_file(GEO_PATH)

    # Zjistí název sloupce s názvem regionu (liší se podle zdroje GeoJSONu)
    name_candidates = ["name", "nazwa", "JPT_NAZWA_", "NAME_1", "Nazwa"]
    name_col = next((c for c in name_candidates if c in gdf.columns), None)
    if name_col is None:
        raise ValueError(f"GeoJSON neobsahuje očekávaný sloupec s názvy. Sloupce: {gdf.columns.tolist()}")

    gdf = gdf.rename(columns={name_col: "region_geo"})
    # Normalizace: lowercase, bez mezer na krajích
    gdf["region_key"] = gdf["region_geo"].str.lower().str.strip()
    return gdf


def load_data(conn: sqlite3.Connection) -> pd.DataFrame:
    """Načte a připraví data z DB. Filtruje zahraniční nabídky a NULL regiony."""
    df = pd.read_sql_query(
        """
        SELECT region, salary_min, salary_max
        FROM job_offers
        WHERE region IS NOT NULL
          AND region != ''
          AND region != 'zagranica'
        """,
        conn,
    )
    # Normalizace klíče pro join s GeoJSON
    df["region_key"] = df["region"].str.lower().str.strip()
    return df


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """Agreguje data na úrovni vojvodství."""
    agg = df.groupby("region_key").agg(
        job_count=("region", "count"),
        salary_min_mean=("salary_min", "mean"),
        salary_max_mean=("salary_max", "mean"),
    ).reset_index()
    # Průměrný plat jako střed rozsahu (salary_min + salary_max) / 2
    # Pouze řádky kde jsou obě hodnoty nenulové
    salary_df = df[(df["salary_min"] > 0) & (df["salary_max"] > 0)].copy()
    salary_df["salary_mid"] = (salary_df["salary_min"] + salary_df["salary_max"]) / 2
    salary_agg = salary_df.groupby("region_key")["salary_mid"].agg(["mean", "median"]).reset_index()
    salary_agg.columns = ["region_key", "salary_mid_mean", "salary_mid_median"]
    agg = agg.merge(salary_agg, on="region_key", how="left")
    return agg


def save_fig(fig: plt.Figure, name: str):
    path = OUTPUT_DIR / f"{TODAY}_{name}.png"
    fig.savefig(path, dpi=FIG_DPI, bbox_inches="tight", pad_inches=0.25, facecolor="white")
    plt.close(fig)
    print(f"  Uloženo: {path.name}")


def plot_choropleth(
    merged: gpd.GeoDataFrame,
    column: str,
    title: str,
    legend_label: str,
    cmap,
    filename: str,
    fmt: str = "{:.0f}",
    midpoint: float | None = None,
    show_pct: bool = False,
):
    """Vykreslí a uloží choropleth mapu. midpoint fixuje střed colorbar škály."""
    import matplotlib.colors as mcolors

    fig, ax = plt.subplots(1, 1, figsize=(10, 9))

    # Volitelný midpoint — vytvoří TwoSlopeNorm
    plot_kwargs = {}
    if midpoint is not None:
        vmin = merged[column].min()
        vmax = merged[column].max()
        if vmin < midpoint < vmax:
            plot_kwargs["norm"] = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=midpoint, vmax=vmax)

    merged.plot(
        column=column,
        ax=ax,
        cmap=cmap,
        legend=True,
        legend_kwds={
            "label": legend_label,
            "orientation": "horizontal",
            "shrink": 0.6,
            "pad": 0.02,
        },
        edgecolor=BORDER_COLOR,
        linewidth=BORDER_WIDTH,
        missing_kwds={"color": "#eeeeee", "label": "Bez dat"},
        **plot_kwargs,
    )

    # Popisky vojvodství s hodnotou
    # Dynamická barva textu: bílá na tmavém pozadí, tmavá na světlém
    vmin = merged[column].min()
    vmax = merged[column].max()
    norm = plot_kwargs.get("norm", mcolors.Normalize(vmin=vmin, vmax=vmax))

    total = merged[column].sum(min_count=1)
    for _, row in merged.iterrows():
        if pd.isna(row[column]):
            continue
        centroid = row.geometry.centroid
        label = fmt.format(row[column])
        if show_pct and total > 0:
            pct = row[column] / total * 100
            label += f"\n({pct:.0f} %)"

        # Zjistit jas pozadí z colormap
        rgba = cmap(norm(row[column]))
        luminance = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
        text_color = "white" if luminance < 0.45 else "#2c3e50"

        ax.annotate(
            label,
            xy=(centroid.x, centroid.y),
            ha="center",
            va="center",
            fontsize=12,
            fontweight=800,
            fontfamily=FONT_FAMILY,
            color=text_color,
        )

    ax.axis("off")
    fig.suptitle(title, fontsize=22, fontweight=600, fontfamily=FONT_FAMILY, y=0.90)

    save_fig(fig, filename)
    


def run():
    print("Načítám GeoJSON...")
    gdf = load_geo()

    print("Připojuji k DB...")
    conn = get_connection()
    df = load_data(conn)
    conn.close()

    print(f"Načteno {len(df):,} nabídek z {df['region_key'].nunique()} vojvodství.")

    # Agregace
    agg = aggregate(df)

    # Kontrola napojení
    geo_keys  = set(gdf["region_key"])
    data_keys = set(agg["region_key"])
    unmatched = data_keys - geo_keys
    if unmatched:
        print(f"  VAROVÁNÍ — regiony bez shody v GeoJSON: {unmatched}")

    # Merge GeoJSON + data
    merged = gdf.merge(agg, on="region_key", how="left")

    # --- Mapa č. 1: Počet nabídek ---
    print("\nGeneruji mapu č. 1: počet nabídek...")
    plot_choropleth(
        merged,
        column="job_count",
        title="Job Offers by Voivodeship\n",
        legend_label=" ",
        cmap=CMAP_COUNT,
        filename="01_geo_job_count",
        fmt="{:.0f}",
        midpoint=700,
        show_pct=True,
    )

    # --- Mapa č. 6 (A): Průměrný plat (střed rozsahu) ---
    print("Generuji mapu: medianovy  plat...")
    plot_choropleth(
        merged,
        column="salary_mid_median",
        title="Median Salary by Voivodeship",
        legend_label="",
        cmap=CMAP_SALARY,
        filename="09_geo_salary_median",
        fmt="{:,.0f}",
        midpoint=6700,
    )

    print(f"\nHotovo. Výstupy uloženy do: {OUTPUT_DIR}")


if __name__ == "__main__":
    run()

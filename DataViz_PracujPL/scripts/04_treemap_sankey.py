"""
04_treemap_sankey.py
--------------------
Nested treemapy a Sankey diagram pro polský trh práce.
Výstup: PNG soubory do outputs/figures/

Generuje:
    č. 3  — Sankey diagram: Top 10 Industries → 16 Voivodeships (industry → region)
    č. 8  — Nested Treemap: Top 20 Cities → work_modes (% nabídek)
    č. 13 — Nested Treemap: Top 20 Cities → top 5 mapped_industry (% nabídek)

Font: Inter (matplotlib: _setup_inter_fonts() + rcParams; Plotly: font=dict(family="Inter"))
    Tituly: Inter SemiBold 600 (title_font)
    Buňky/labely: Inter Regular 400 (textfont)
    Sankey titulek: fontfamily="Inter" explicitně (pySankey vytváří figure interně)
Color palette: inferno_r (treemapy), inferno (Sankey colorDict)
Midpoint: fixní sdílený midpoint=18 (obě treemapy)

Závislosti:
    plotly >= 5.18, kaleido >= 0.2    (treemapy → PNG)
    pySankey >= 1.0                   (Sankey)

Run from project root:
    python scripts/04_treemap_sankey.py
"""

import sys
import warnings
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.font_manager as fm
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.db_connection import get_connection

OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TODAY = date.today().isoformat()


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
TOP_CITIES = 20              # počet měst pro treemap č. 13
TOP_INDUSTRIES = 5           # top N odvětví per město / region (treemapy)
TOP_REGIONS = 16             # top N regionů pro Sankey (méně = čitelnější)
SANKEY_TOP_INDUSTRIES = 10   # top N odvětví pro Sankey č. 3


def save_png(path: Path):
    print(f"  Uloženo: {path.name}")


# ─────────────────────────────────────────────────────────────────────────────
# Pomocné funkce
# ─────────────────────────────────────────────────────────────────────────────

def explode_col(df: pd.DataFrame, col: str, id_cols: list[str]) -> pd.DataFrame:
    """Exploduje comma-separated sloupec, zachová id_cols."""
    result = df[id_cols + [col]].copy()
    result = result[result[col].notna()]
    result = result.assign(**{col: result[col].str.split(",")}).explode(col)
    result[col] = result[col].str.strip().str.strip("[]\"'")
    return result[result[col] != ""]


def load_data(conn) -> pd.DataFrame:
    return pd.read_sql_query(
        """
        SELECT region, city, mapped_industry, work_modes, position_levels
        FROM job_offers
        WHERE region IS NOT NULL AND region != ''
        """,
        conn,
    )


# ─────────────────────────────────────────────────────────────────────────────
# č. 8 — Nested Treemap: Top 20 Cities → work_modes
# ─────────────────────────────────────────────────────────────────────────────

def plot_treemap_city_work_modes(df: pd.DataFrame):
    """č. 8 — Top 20 měst → work_modes, % nabídek. Export přes kaleido."""
    import plotly.express as px

    df_valid = df[df["city"].notna() & df["work_modes"].notna()].copy()

    # Top 20 měst dle počtu nabídek
    top_cities = (
        df_valid["city"].value_counts()
        .head(TOP_CITIES)
        .index.tolist()
    )
    df_top = df_valid[df_valid["city"].isin(top_cities)].copy()

    # Explodovat work_modes
    df_exp = explode_col(df_top, "work_modes", ["city"])

    # Agregace
    agg = df_exp.groupby(["city", "work_modes"]).size().reset_index(name="count")

    # Přidat % v rámci města
    city_totals = agg.groupby("city")["count"].sum().reset_index(name="total")
    agg = agg.merge(city_totals, on="city")
    agg["pct"] = (agg["count"] / agg["total"] * 100).round(1)
    agg["label"] = agg["work_modes"] + "<br>" + agg["pct"].astype(str) + " %"

    fig = px.treemap(
        agg,
        path=[px.Constant("Top Cities"), "city", "work_modes"],
        values="count",
        color="pct",
        color_continuous_scale="inferno_r",
        color_continuous_midpoint=18,
        title="Job Offers: Top 20 Cities → Work Modes",
        hover_data={"pct": ":.1f"},
    )
    fig.update_traces(
        textinfo="label+percent parent",
        textfont=dict(size=20, family="Inter", weight=400),
    )
    fig.update_layout(
        margin=dict(t=100, l=10, r=10, b=10),
        width=1600,
        height=1000,
        font=dict(family="Inter"),
        title_font=dict(size=36,weight=600),
        title_x=0.15,
        coloraxis_colorbar=dict(title="% per City"),
    )

    path = OUTPUT_DIR / f"{TODAY}_08_treemap_city_work_modes.png"
    fig.write_image(str(path), scale=1.5)
    save_png(path)


# ─────────────────────────────────────────────────────────────────────────────
# č. 13 — Nested Treemap: City → top 5 mapped_industry
# ─────────────────────────────────────────────────────────────────────────────

def plot_treemap_city_industry(df: pd.DataFrame):
    """č. 13 — City → top 5 mapped_industry, top 20 měst dle počtu nabídek."""
    import plotly.express as px

    df_valid = df[df["city"].notna() & df["mapped_industry"].notna()].copy()

    # Top N měst dle celkového počtu nabídek
    top_cities = (
        df_valid["city"].value_counts()
        .head(TOP_CITIES)
        .index.tolist()
    )
    df_top = df_valid[df_valid["city"].isin(top_cities)].copy()

    # Agregace city × industry
    agg = df_top.groupby(["city", "mapped_industry"]).size().reset_index(name="count")

    # Pro každé město zachovat jen top N odvětví
    agg_top = (
        agg.sort_values("count", ascending=False)
        .groupby("city")
        .head(TOP_INDUSTRIES)
        .reset_index(drop=True)
    )

    # Přidat % v rámci města
    city_totals = agg_top.groupby("city")["count"].sum().reset_index(name="total")
    agg_top = agg_top.merge(city_totals, on="city")
    agg_top["pct"] = (agg_top["count"] / agg_top["total"] * 100).round(1)

    fig = px.treemap(
        agg_top,
        path=[px.Constant("Top Cities"), "city", "mapped_industry"],
        values="count",
        color="pct",
        color_continuous_scale="inferno_r",
        color_continuous_midpoint=18,
        title=f"Job Offers: Top {TOP_CITIES} Cities → Top {TOP_INDUSTRIES} Industries",
        hover_data={"pct": ":.1f"},
    )
    fig.update_traces(
        textinfo="label+percent parent",
        textfont=dict(size=20, family="Inter", weight=400),
    )
    fig.update_layout(
        margin=dict(t=100, l=10, r=10, b=10),
        width=1600,
        height=1000,
        font=dict(family="Inter"),
        title_font=dict(size=36,weight=600),
        title_x=0.15,
        coloraxis_colorbar=dict(title="% per City"),
    )

    path = OUTPUT_DIR / f"{TODAY}_13_treemap_city_industry.png"
    fig.write_image(str(path), scale=1.5)
    save_png(path)


# ─────────────────────────────────────────────────────────────────────────────
# č. 3 — Sankey: Top 10 Industries → 16 Voivodeships
# ─────────────────────────────────────────────────────────────────────────────

def _sankey_pysankey(flow_df: pd.DataFrame, left_order: list, right_order: list):
    """Sankey přes pySankey. flow_df má sloupce: industry, region, count.
    Směr: industry (left) → region (right).
    left_order/right_order: řazení uzlů shora dolů (od největšího)."""
    from pySankey.sankey import sankey

    # Barvy všech uzlů z inferno colormap — rovnoměrně rozložené po škále
    cmap = plt.cm.inferno
    all_labels = left_order + right_order
    n = len(all_labels)
    color_dict = {
        label: "#{:02x}{:02x}{:02x}".format(
            *[int(c * 255) for c in cmap(i / (n - 1))[:3]]
        )
        for i, label in enumerate(all_labels)
    }

    # Seřadit DataFrame — pySankey bere pořadí z first appearance (df.left/right.unique())
    # leftLabels/rightLabels nepředáváme kvůli bugu v pySankey (check_data_matches_labels)
    left_rank = {l: i for i, l in enumerate(left_order)}
    right_rank = {r: i for i, r in enumerate(right_order)}
    flow_df = flow_df.copy()
    flow_df["_lr"] = flow_df["industry"].map(left_rank)
    flow_df["_rr"] = flow_df["region"].map(right_rank)
    flow_df = flow_df.sort_values(["_lr", "_rr"]).drop(columns=["_lr", "_rr"]).reset_index(drop=True)

    # pySankey vytváří vlastní figure interně — nepřijímá ax parametr
    sankey(
        left=flow_df["industry"],
        right=flow_df["region"],
        leftWeight=flow_df["count"],
        rightWeight=flow_df["count"],
        colorDict=color_dict,
        aspect=20,
        fontsize=14,
    )
    fig = plt.gcf()
    fig.set_size_inches(16, 12)

    # Titulek — Inter SemiBold 600
    plt.title(
        f"Top {SANKEY_TOP_INDUSTRIES} Industries → {TOP_REGIONS} Voivodeships",
        fontsize=22, fontweight=600, fontfamily="Inter", pad=15,
    )

    # Fonty pro labels uzlů (pySankey generuje Text objekty)
    for text_obj in fig.findobj(plt.Text):
        if text_obj.get_text() and text_obj != fig._suptitle if hasattr(fig, '_suptitle') else True:
            text_obj.set_fontfamily("Inter")
            text_obj.set_fontweight(600)

    path = OUTPUT_DIR / f"{TODAY}_03_sankey_industry_to_region.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    save_png(path)

"""
def _sankey_fallback_stacked_bar(flow_df: pd.DataFrame):
    
    #Fallback pro č. 3: stacked bar chart (region × top 10 odvětví).
    #Použije se pokud pySankey není nainstalován nebo selže.
    
    pivot = flow_df.pivot_table(
        index="region", columns="industry", values="count", fill_value=0
    )
    # Seřadit regiony dle celkového počtu
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(12, 7))
    colors = plt.cm.Set2.colors
    bottom = pd.Series([0] * len(pivot), index=pivot.index)

    for i, col in enumerate(pivot.columns):
        ax.bar(
            pivot.index, pivot[col],
            bottom=bottom,
            label=col,
            color=colors[i % len(colors)],
            width=0.7,
        )
        bottom += pivot[col]

    ax.set_xlabel("Vojvodství", fontsize=18)
    ax.set_ylabel("Počet nabídek", fontsize=18)
    ax.set_title(
        f"Top {TOP_INDUSTRIES} odvětví v top {TOP_REGIONS} vojvodstvích\n(stacked bar fallback za Sankey)",
        fontsize=22, fontweight=600, pad=12,
    )
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.legend(title="Odvětví", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=9)
    ax.tick_params(axis="x", rotation=45, labelsize=9)

    plt.rcParams["axes.spines.top"] = False
    plt.rcParams["axes.spines.right"] = False
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    path = OUTPUT_DIR / f"{TODAY}_03_sankey_fallback_stacked_bar.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    save_png(path)
    print("  (Fallback: stacked bar chart — pySankey nedostupný nebo selhal)")

"""
def plot_sankey_industry_to_region(df: pd.DataFrame):
    """č. 3 — Reverzní Sankey: Top 10 industries → 16 voivodeships."""
    df_pl = df[
        df["region"].notna() &
        (df["region"] != "zagranica") &
        df["mapped_industry"].notna()
    ].copy()

    # Top 10 odvětví globálně dle počtu nabídek
    top_industries = (
        df_pl["mapped_industry"].value_counts()
        .head(SANKEY_TOP_INDUSTRIES)
        .index.tolist()
    )
    df_top = df_pl[df_pl["mapped_industry"].isin(top_industries)].copy()

    # Agregace industry × region
    agg = df_top.groupby(["mapped_industry", "region"]).size().reset_index(name="count")
    agg.columns = ["industry", "region", "count"]

    # Title case pro vojvodství ("śląskie" → "Śląskie")
    agg["region"] = agg["region"].str.title()

    # Řazení: od největšího k nejmenšímu (shora dolů)
    left_order = agg.groupby("industry")["count"].sum().sort_values(ascending=True).index.tolist()
    right_order = agg.groupby("region")["count"].sum().sort_values(ascending=False).index.tolist()

    # Zkusit pySankey, fallback na stacked bar
    try:
        import pySankey  # noqa: F401
        _sankey_pysankey(agg, left_order, right_order)
    except ImportError:
        warnings.warn("pySankey není nainstalován. Používám stacked bar fallback.")
    except Exception as e:
        warnings.warn(f"pySankey selhal ({e}).")

# ─────────────────────────────────────────────────────────────────────────────
# Hlavní funkce
# ─────────────────────────────────────────────────────────────────────────────

def run():
    conn = get_connection()
    print("Načítám data z DB...")
    df = load_data(conn)
    conn.close()
    print(f"  Načteno {len(df):,} řádků.\n")

    print("[3] Sankey: top 10 industries → 16 voivodeships")
    plot_sankey_industry_to_region(df)

    print("\n[8] Treemap: top 20 měst → work_modes")
    plot_treemap_city_work_modes(df)

    print("\n[13] Treemap: top 20 měst → top 5 odvětví")
    plot_treemap_city_industry(df)

    print(f"\nVšechny výstupy uloženy do: {OUTPUT_DIR}")


if __name__ == "__main__":
    run()

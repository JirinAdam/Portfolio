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
SANKEY_TOP_LANGUAGES = 10    # top N jazyků pro Sankey č. 15


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
        SELECT region, city, mapped_industry, work_modes, mapped_languages
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

def _render_sankey(flow_df: pd.DataFrame, left_col: str, right_col: str,
                   left_order: list, right_order: list, title: str, filename: str):
    """Obecný Sankey renderer přes pySankey.
    flow_df musí mít sloupce: left_col, right_col, count."""
    from pySankey.sankey import sankey

    # Barvy všech uzlů z inferno colormap
    cmap = plt.cm.inferno
    all_labels = left_order + right_order
    n = len(all_labels)
    color_dict = {
        label: "#{:02x}{:02x}{:02x}".format(
            *[int(c * 255) for c in cmap(i / (n - 1))[:3]]
        )
        for i, label in enumerate(all_labels)
    }

    # Seřadit DataFrame — pySankey bere pořadí z first appearance
    left_rank = {l: i for i, l in enumerate(left_order)}
    right_rank = {r: i for i, r in enumerate(right_order)}
    flow_df = flow_df.copy()
    flow_df["_lr"] = flow_df[left_col].map(left_rank)
    flow_df["_rr"] = flow_df[right_col].map(right_rank)
    flow_df = flow_df.sort_values(["_lr", "_rr"]).drop(columns=["_lr", "_rr"]).reset_index(drop=True)

    sankey(
        left=flow_df[left_col],
        right=flow_df[right_col],
        leftWeight=flow_df["count"],
        rightWeight=flow_df["count"],
        colorDict=color_dict,
        aspect=20,
        fontsize=14,
    )
    fig = plt.gcf()
    fig.set_size_inches(16, 12)

    plt.title(title, fontsize=22, fontweight=600, fontfamily="Inter", pad=15)

    for text_obj in fig.findobj(plt.Text):
        if text_obj.get_text() and text_obj != fig._suptitle if hasattr(fig, '_suptitle') else True:
            text_obj.set_fontfamily("Inter")
            text_obj.set_fontweight(600)

    path = OUTPUT_DIR / f"{TODAY}_{filename}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    save_png(path)

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

    try:
        import pySankey  # noqa: F401
        _render_sankey(
            agg, "industry", "region", left_order, right_order,
            f"Top {SANKEY_TOP_INDUSTRIES} Industries → {TOP_REGIONS} Voivodeships",
            "03_sankey_industry_to_region",
        )
    except ImportError:
        warnings.warn("pySankey not installed.")
    except Exception as e:
        warnings.warn(f"pySankey failed ({e}).")


# ─────────────────────────────────────────────────────────────────────────────
# č. 15 — Sankey: Languages → Industries
# ─────────────────────────────────────────────────────────────────────────────

def plot_sankey_language_to_industry(df: pd.DataFrame):
    """č. 15 — Sankey: Top languages → Top industries."""
    df_valid = df[
        df["mapped_languages"].notna() &
        df["mapped_industry"].notna()
    ].copy()

    # Explodovat jazyky
    df_exp = explode_col(df_valid, "mapped_languages", ["mapped_industry"])

    # Top N jazyků dle počtu nabídek
    top_langs = (
        df_exp["mapped_languages"].value_counts()
        .head(SANKEY_TOP_LANGUAGES)
        .index.tolist()
    )
    df_top = df_exp[df_exp["mapped_languages"].isin(top_langs)].copy()

    # Top N odvětví dle počtu nabídek (v rámci filtrovaných dat)
    top_industries = (
        df_top["mapped_industry"].value_counts()
        .head(SANKEY_TOP_INDUSTRIES)
        .index.tolist()
    )
    df_top = df_top[df_top["mapped_industry"].isin(top_industries)].copy()

    # Agregace
    agg = df_top.groupby(["mapped_languages", "mapped_industry"]).size().reset_index(name="count")
    agg.columns = ["language", "industry", "count"]

    left_order = agg.groupby("language")["count"].sum().sort_values(ascending=True).index.tolist()
    right_order = agg.groupby("industry")["count"].sum().sort_values(ascending=False).index.tolist()

    try:
        import pySankey  # noqa: F401
        _render_sankey(
            agg, "language", "industry", left_order, right_order,
            f"Top {SANKEY_TOP_LANGUAGES} Languages → Top {SANKEY_TOP_INDUSTRIES} Industries",
            "15_sankey_language_to_industry",
        )
    except ImportError:
        warnings.warn("pySankey not installed.")
    except Exception as e:
        warnings.warn(f"pySankey failed ({e}).")


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

    print("\n[15] Sankey: languages → industries")
    plot_sankey_language_to_industry(df)

    print(f"\nVšechny výstupy uloženy do: {OUTPUT_DIR}")


if __name__ == "__main__":
    run()

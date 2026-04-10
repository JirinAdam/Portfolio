"""
02_visualizations.py
--------------------
Statické vizualizace polského trhu práce.
Výstup: PNG soubory do outputs/figures/

Generuje:
    č. 2  — Bar chart: počet nabídek podle mapped_industry + %
    č. 4  — Heatmapa: vojvodství × mapped_industry (absolutní čísla, center=1800)
    č. 5  — Bar chart: position_levels + %
    č. 7  — Bar chart: work_modes + %
    č. 9  — Ridge Plot: monthly_max_salary podle vojvodství (mako, sharey=False)
    č. 10 — Ridge Plot: monthly_max_salary podle work_modes
    č. 11 — Ridge Plot: monthly_max_salary podle position_level
    č. 12 — Ridge Plot: monthly_max_salary podle mapped_industry

Font: Inter (registrace přes _setup_inter_fonts() + rcParams)
    Tituly: Inter SemiBold 600
    Bar Y labels + value annotations: Inter ExtraBold 800
    Heatmapa Y labels: Inter SemiBold 600
    Ridge labels: Inter SemiBold 600, barva = barva výplně skupiny
Color palette: mako_r (bar charty, heatmapa), mako (ridge ploty)
Voivodeships: Title format (.str.title()) v heatmapě i ridge by region

Run from project root:
    python scripts/02_visualizations.py
"""

import ast
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.font_manager as fm
import seaborn as sns
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.db_connection import get_connection

OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TODAY = date.today().isoformat()


def _setup_inter_fonts():
    """Zaregistruje Inter fonty z lokálního data/fonts/. Fallback: DejaVu Sans.
    Poznámka: nevolat fm._load_fontmanager() — resetuje ručně přidané fonty.
    """
    fonts_dir = Path(__file__).parent.parent / "data" / "fonts"
    for ttf in ["Inter-Light.ttf", "Inter-Regular.ttf", "Inter-SemiBold.ttf", "Inter-ExtraBold.ttf"]:
        path = fonts_dir / ttf
        if path.exists():
            fm.fontManager.addfont(str(path))

_setup_inter_fonts()

# Globální styl
sns.set_theme(style="white", palette="muted")
plt.rcParams.update({
    "figure.dpi": 150,
    "font.family": "Inter",
    "font.weight": 400,          # Regular jako výchozí
    "axes.spines.top": False,
    "axes.spines.right": False,
})

# Konstanty pro ridge ploty
SALARY_CAP = 50_000       # PLN/měsíc — horní cap pro odstranění outlierů
MIN_RIDGE_COUNT = 30      # minimální počet hodnot pro vykreslení skupiny


def _bar_colors(values: pd.Series):
    """Mapuje hodnoty na mako_r colormap (seaborn, as_cmap=True). Tmavší = větší hodnota."""
    cmap = sns.color_palette("mako_r", as_cmap=True)
    norm = plt.Normalize(values.min(), values.max())
    return [cmap(norm(v)) for v in values]


def save_fig(fig: plt.Figure, name: str):
    path = OUTPUT_DIR / f"{TODAY}_{name}.png"
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Uloženo: {path.name}")


def load_data(conn) -> pd.DataFrame:
    """Načte celou tabulku job_offers."""
    return pd.read_sql_query("SELECT * FROM job_offers", conn)


def explode_col(df: pd.DataFrame, col: str) -> pd.Series:
    """
    Exploduje sloupec obsahující JSON-encoded listy (např. '["hybrid work", "full office"]')
    nebo prosté comma-separated stringy (fallback).
    Každý prvek listu = jeden řádek. Vrací Series bez NaN.

    Poznámka: výsledný total > počet originálních řádků —
    jedna nabídka je počítána 1× za každý mode, který obsahuje.
    Vhodné pro vizuály distribuce (kolik nabídek zahrnuje daný mode).
    Platí pro: work_modes, employment_type, work_schedules, mapped_languages.
    """
    def parse_cell(val):
        if pd.isna(val):
            return []
        try:
            # Parsovat JSON-encoded list: ["hybrid work", "full office work"]
            parsed = ast.literal_eval(str(val))
            return parsed if isinstance(parsed, list) else [parsed]
        except (ValueError, SyntaxError):
            # Fallback: prosté comma-separated hodnoty
            return [v.strip() for v in str(val).split(",") if v.strip()]

    return (
        df[col]
        .apply(parse_cell)
        .explode()
        .str.strip()
        .loc[lambda s: s.notna() & (s != "")]
    )


# ─────────────────────────────────────────────────────────────────────────────
# č. 2 — Bar chart: mapped_industry
# ─────────────────────────────────────────────────────────────────────────────

def plot_industry_bar(df: pd.DataFrame):
    """č. 2 — Počet nabídek podle mapped_industry, seřazeno sestupně, s % z celku."""
    counts = df["mapped_industry"].dropna().value_counts().reset_index()
    counts.columns = ["industry", "count"]
    total = counts["count"].sum()
    counts["pct"] = (counts["count"] / total * 100).round(1)
    counts = counts.sort_values("count", ascending=True)

    fig, ax = plt.subplots(figsize=(10, max(6, len(counts) * 0.45)))
    bars = ax.barh(counts["industry"], counts["count"], color=_bar_colors(counts["count"]), height=0.7)

    # Hodnoty vpravo od sloupce
    x_offset = counts["count"].max() * 0.01
    for bar, row in zip(bars, counts.itertuples()):
        ax.text(
            bar.get_width() + x_offset,
            bar.get_y() + bar.get_height() / 2,
            f"{row.count:,} ({row.pct} %)",
            va="center", ha="left", fontsize=15, fontweight=800,
        )

    plt.setp(ax.get_yticklabels(), fontweight=800)
    #ax.set_xlabel("Počet nabídek", fontsize=15)
    ax.set_title(
        "Job Offers by Industry",
        fontsize=28, fontweight=600, pad=12,
    )
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_xlim(right=counts["count"].max() * 1.12)
    fig.tight_layout()
    save_fig(fig, "02_bar_industry")


# ─────────────────────────────────────────────────────────────────────────────
# č. 4 — Heatmapa: vojvodství × mapped_industry
# ─────────────────────────────────────────────────────────────────────────────

def plot_region_industry_heatmap(df: pd.DataFrame):
    """č. 4 — Heatmapa vojvodství × mapped_industry, absolutní čísla."""
    # Filtrovat zahraniční nabídky
    df_pl = df[
        df["region"].notna() &
        (df["region"].str.strip() != "") &
        (df["region"] != "zagranica")
    ].copy()
    df_pl["region"] = df_pl["region"].str.title()

    pivot = (
        df_pl.groupby(["region", "mapped_industry"])
        .size()
        .unstack(fill_value=0)
    )
    # Seřadit: regiony sestupně dle součtu, odvětví sestupně dle součtu
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
    pivot = pivot[pivot.sum(axis=0).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(max(14, len(pivot.columns)), max(8, len(pivot.index) * 0.55)))
    sns.heatmap(
        pivot,
        ax=ax,
        cmap=sns.color_palette("mako_r", as_cmap=True),
        center=1800,
        annot=True,
        fmt="d",
        linewidths=0.3,
        cbar_kws={"label": "", "shrink": 0.6},
        annot_kws={"fontsize": 15},
    )
    ax.set_title(
        "Job Offers: Voivodeship × Industry",
        fontsize=28, fontweight=600, pad=12,
    )
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", rotation=45, labelsize=15)
    ax.tick_params(axis="y", rotation=0, labelsize=15)
    plt.setp(ax.get_yticklabels(), fontweight=600)
    fig.tight_layout()
    save_fig(fig, "04_heatmap_region_industry")


# ─────────────────────────────────────────────────────────────────────────────
# č. 5 — Bar chart: position_levels (>1 000 nabídek) + %
# ─────────────────────────────────────────────────────────────────────────────

def plot_position_level_bar(df: pd.DataFrame):
    """č. 5 — position_levels, všechny kategorie, s % z celku."""
    levels = explode_col(df, "position_levels")
    counts = levels.value_counts().reset_index()
    counts.columns = ["level", "count"]
    total = counts["count"].sum()
    counts["pct"] = (counts["count"] / total * 100).round(1)
    counts = counts.sort_values("count", ascending=True)   # ascending=True → největší nahoře v barh

    fig, ax = plt.subplots(figsize=(9, max(5, len(counts) * 0.55)))
    bars = ax.barh(counts["level"], counts["count"], color=_bar_colors(counts["count"]), height=0.6)

    x_offset = counts["count"].max() * 0.01
    for bar, row in zip(bars, counts.itertuples()):
        ax.text(
            bar.get_width() + x_offset,
            bar.get_y() + bar.get_height() / 2,
            f"{row.count:,} ({row.pct} %)",
            va="center", ha="left", fontsize=15, fontweight=800,
        )

    plt.setp(ax.get_yticklabels(), fontweight=800)
    #ax.set_xlabel("Počet nabídek", fontsize=15)
    ax.set_title(
        "Job Offers by Position Level",
        fontsize=28, fontweight=600, pad=12,
    )
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_xlim(right=counts["count"].max() * 1.2)
    fig.tight_layout()
    save_fig(fig, "05_bar_position_level")


# ─────────────────────────────────────────────────────────────────────────────
# č. 7 — Bar chart: work_modes + %
# ─────────────────────────────────────────────────────────────────────────────

def plot_work_modes_bar(df: pd.DataFrame):
    """č. 7 — Počet nabídek podle work_modes s % z celku."""
    modes = explode_col(df, "work_modes")
    counts = modes.value_counts().reset_index()
    counts.columns = ["mode", "count"]
    total = counts["count"].sum()
    counts["pct"] = (counts["count"] / total * 100).round(1)
    counts = counts.sort_values("count", ascending=True)   # ascending=True → největší nahoře v barh

    fig, ax = plt.subplots(figsize=(9, max(5, len(counts) * 0.55)))
    bars = ax.barh(counts["mode"], counts["count"], color=_bar_colors(counts["count"]), height=0.6)

    x_offset = counts["count"].max() * 0.01
    for bar, row in zip(bars, counts.itertuples()):
        ax.text(
            bar.get_width() + x_offset,
            bar.get_y() + bar.get_height() / 2,
            f"{row.count:,} ({row.pct} %)",
            va="center", ha="left", fontsize=15, fontweight=800,
        )

    plt.setp(ax.get_yticklabels(), fontweight=800)
    #ax.set_xlabel("Počet nabídek", fontsize=15)
    ax.set_title(
        "Job Offers by Work Mode",
        fontsize=28, fontweight=600, pad=12,
    )
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_xlim(right=counts["count"].max() * 1.2)
    fig.tight_layout()
    save_fig(fig, "07_bar_work_modes")


# ─────────────────────────────────────────────────────────────────────────────
# č. 9–12 — Ridge Ploty (seaborn FacetGrid overlapping, Alt C styl)
# ─────────────────────────────────────────────────────────────────────────────

def _ridge_plot(
    df_ridge: pd.DataFrame,
    group_col: str,
    value_col: str,
    title: str,
    filename: str,
):
    """
    Seaborn FacetGrid overlapping ridge plot (Alt C styl).
    Skupiny seřazeny sestupně dle mediánu, skupiny s <MIN_RIDGE_COUNT hodnotami vynechány.
    """
    # Seřadit skupiny dle mediánu
    order = (
        df_ridge.groupby(group_col)[value_col]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )
    # Odebrat skupiny s malým vzorkem
    valid = [g for g in order if (df_ridge[group_col] == g).sum() >= MIN_RIDGE_COUNT]
    if not valid:
        print(f"  Přeskakuji {filename}: žádná skupina s dostatkem dat.")
        return

    df_ridge = df_ridge[df_ridge[group_col].isin(valid)].copy()
    df_ridge[group_col] = pd.Categorical(df_ridge[group_col], categories=valid, ordered=True)

    n = len(valid)
    palette = sns.color_palette("mako", n)

    g = sns.FacetGrid(
        df_ridge,
        row=group_col,
        hue=group_col,
        aspect=7,
        height=0.75,
        palette=palette,
        sharey=False,
    )
    # Filled KDE — common_norm=False: každá skupina normalizována individuálně
    g.map(
        sns.kdeplot, value_col,
        bw_adjust=0.6, clip_on=False,
        fill=True, alpha=0.85, linewidth=0,
        common_norm=False,
    )
    # Bílá ohraničovací linka
    g.map(
        sns.kdeplot, value_col,
        bw_adjust=0.6, clip_on=False,
        color="white", lw=2,
        common_norm=False,
    )

    # Popisek skupiny vlevo od grafu (barva = barva výplně)
    def _label(x, color, label):
        ax = plt.gca()
        ax.text(
            -0.01, 0.05, label,
            fontweight=600, color=color,
            ha="right", va="center",
            transform=ax.transAxes,
            fontsize=15,
        )
    g.map(_label, value_col)

    g.figure.subplots_adjust(hspace=0.3)
    g.set_titles("")
    g.set(yticks=[], xlabel="", ylabel="")
    g.despine(bottom=True, left=True)
    g.figure.suptitle(title, fontsize=22, fontweight=600, y=1.02)
    g.figure.set_facecolor("white")

    path = OUTPUT_DIR / f"{TODAY}_{filename}.png"
    g.figure.savefig(path, bbox_inches="tight", dpi=150, facecolor="white")
    plt.close(g.figure)
    print(f"  Uloženo: {path.name}")


def _prep_salary(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Filtruje a cappuje monthly_max_salary pro ridge ploty."""
    return df[
        df["monthly_max_salary"].notna() &
        (df["monthly_max_salary"] > 0) &
        (df["monthly_max_salary"] <= SALARY_CAP) &
        df[group_col].notna()
    ][[group_col, "monthly_max_salary"]].copy()


def plot_ridge_by_region(df: pd.DataFrame):
    """č. 9 — monthly_max_salary podle vojvodství (zagranica vyloučena)."""
    d = _prep_salary(df, "region")
    d = d[d["region"] != "zagranica"]
    d["region"] = d["region"].str.title()
    d.columns = ["region", "salary"]
    _ridge_plot(d, "region", "salary",
                "Salary Distribution by Voivodeship",
                "09_ridge_salary_region")


def plot_ridge_by_work_mode(df: pd.DataFrame):
    """č. 10 — monthly_max_salary podle work_modes."""
    d = _prep_salary(df, "work_modes")
    # Explodovat JSON-encoded work_modes přes sdílený helper
    modes = explode_col(d, "work_modes").rename("work_mode")
    d = d.loc[modes.index].assign(work_mode=modes.values)[["work_mode", "monthly_max_salary"]].copy()
    d.columns = ["work_mode", "salary"]
    _ridge_plot(d, "work_mode", "salary",
                "Salary Distribution by Work Mode",
                "10_ridge_salary_work_mode")


def plot_ridge_by_position_level(df: pd.DataFrame):
    """č. 11 — monthly_max_salary podle position_level."""
    d = _prep_salary(df, "position_levels")
    # Explodovat přes sdílený helper (JSON i comma-sep fallback)
    levels = explode_col(d, "position_levels").rename("level")
    d = d.loc[levels.index].assign(level=levels.values)[["level", "monthly_max_salary"]].copy()
    d.columns = ["level", "salary"]
    _ridge_plot(d, "level", "salary",
                "Salary Distribution by Position Level",
                "11_ridge_salary_position_level")


def plot_ridge_by_industry(df: pd.DataFrame):
    """č. 12 — monthly_max_salary podle mapped_industry."""
    d = _prep_salary(df, "mapped_industry")
    d.columns = ["industry", "salary"]
    _ridge_plot(d, "industry", "salary",
                "Salary Distribution by Industry",
                "12_ridge_salary_industry")


# ─────────────────────────────────────────────────────────────────────────────
# Hlavní funkce
# ─────────────────────────────────────────────────────────────────────────────

def run():
    conn = get_connection()
    print("Načítám data z DB...")
    df = pd.read_sql_query("SELECT * FROM job_offers", conn)
    conn.close()
    print(f"  Načteno {len(df):,} řádků, {df.shape[1]} sloupců.\n")

    print("[2] Bar chart: mapped_industry")
    plot_industry_bar(df)

    print("\n[4] Heatmapa: vojvodství × mapped_industry")
    plot_region_industry_heatmap(df)

    print("\n[5] Bar chart: position_levels")
    plot_position_level_bar(df)

    print("\n[7] Bar chart: work_modes")
    plot_work_modes_bar(df)

    print("\n[9] Ridge Plot: salary × region")
    plot_ridge_by_region(df)

    print("\n[10] Ridge Plot: salary × work_modes")
    plot_ridge_by_work_mode(df)

    print("\n[11] Ridge Plot: salary × position_level")
    plot_ridge_by_position_level(df)

    print("\n[12] Ridge Plot: salary × industry")
    plot_ridge_by_industry(df)

    print(f"\nVšechny výstupy uloženy do: {OUTPUT_DIR}")


if __name__ == "__main__":
    run()

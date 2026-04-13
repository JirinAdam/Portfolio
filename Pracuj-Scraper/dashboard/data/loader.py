"""Centrální datový modul pro PracujPL Data jobs ."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine


DB_PATH = Path(__file__).resolve().parent.parent.parent / "nerd_jobs.db"


def parse_json_list(value) -> list:
    """Bezpečný parser JSON array uloženého v TEXT sloupci."""
    if not value or (isinstance(value, str) and value.strip() == ""):
        return []
    try:
        result = json.loads(value)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def get_connection():
    """Vrátí SQLAlchemy engine na nerd_jobs.db."""
    return create_engine(f"sqlite:///{DB_PATH}")


@st.cache_data(ttl=3600)
def load_all_jobs() -> pd.DataFrame:
    """Načte celou tabulku nerd_jobs a parsuje JSON sloupce."""
    engine = get_connection()
<<<<<<< HEAD
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM nerd_jobs", conn)
=======
    
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM nerd_jobs", conn) 
    
>>>>>>> ca4417bf1751450e2dc58a07ab28e92f1e5d5fab

    for col in ("technologies_os", "technologies_optional", "position_levels"):
        df[col] = df[col].apply(parse_json_list)

    return df


def get_kw_title_options(df: pd.DataFrame) -> list[str]:
    """Vrátí sorted list unikátních kw_title + 'All' na začátku."""
    options = sorted(df["kw_title"].dropna().unique())
    return ["All"] + options


def get_region_options(df: pd.DataFrame) -> list[str]:
    """Vrátí sorted list unikátních region + 'All' na začátku."""
    options = sorted(df["region"].dropna().unique())
    return ["All"] + options


def _filter_by_kw_title(df: pd.DataFrame, kw_title_filter: str | None) -> pd.DataFrame:
    """Pomocný filtr podle kw_title."""
    if kw_title_filter and kw_title_filter != "All":
        return df[df["kw_title"] == kw_title_filter]
    return df


def _salary_mask(df: pd.DataFrame) -> pd.Series:
    """Maska: monthly_max_salary IS NOT NULL AND > 0."""
    return df["monthly_max_salary"].notna() & (df["monthly_max_salary"] > 0)


def get_skills_counts(df: pd.DataFrame, kw_title_filter: str | None = None) -> pd.Series:
    """Sloučí technologies_os + technologies_optional per záznam, vrátí skill → count."""
    filtered = _filter_by_kw_title(df, kw_title_filter)

    all_skills = []
    for _, row in filtered.iterrows():
        combined = set(row["technologies_os"]) | set(row["technologies_optional"])
        all_skills.extend(combined)

    if not all_skills:
        return pd.Series(dtype=int)

    return pd.Series(all_skills).value_counts().sort_values(ascending=False)


def get_salary_per_kw_title(df: pd.DataFrame) -> pd.DataFrame:
    """Groupby kw_title → Median, Mean monthly_max_salary, seřazeno sestupně."""
    valid = df[_salary_mask(df)]
    grouped = valid.groupby("kw_title")["monthly_max_salary"].agg(
        median_salary="median",
        mean_salary="mean",
    ).reset_index()
    return grouped.sort_values("median_salary", ascending=False)


def get_salary_per_skill(
    df: pd.DataFrame, kw_title_filter: str | None = None
) -> pd.DataFrame:
    """Rozbalí skills do řádků, groupby skill → Median, Mean, Count."""
    filtered = _filter_by_kw_title(df, kw_title_filter)
    valid = filtered[_salary_mask(filtered)].copy()

    valid["_skills"] = valid.apply(
        lambda r: list(set(r["technologies_os"]) | set(r["technologies_optional"])),
        axis=1,
    )
    exploded = valid.explode("_skills").rename(columns={"_skills": "skill"})
    exploded = exploded.dropna(subset=["skill"])
    exploded = exploded[exploded["skill"] != ""]

    if exploded.empty:
        return pd.DataFrame(columns=["skill", "median_salary", "mean_salary", "count"])

    grouped = exploded.groupby("skill")["monthly_max_salary"].agg(
        median_salary="median",
        mean_salary="mean",
        count="count",
    ).reset_index()
    return grouped.sort_values("median_salary", ascending=False)


def get_salary_per_level(
    df: pd.DataFrame, kw_title_filter: str | None = None
) -> pd.DataFrame:
    """Rozbalí position_levels do řádků, groupby level → Median, Mean, Count."""
    filtered = _filter_by_kw_title(df, kw_title_filter)
    valid = filtered[_salary_mask(filtered)].copy()

    exploded = valid.explode("position_levels").rename(
        columns={"position_levels": "level"}
    )
    exploded = exploded.dropna(subset=["level"])
    exploded = exploded[exploded["level"] != ""]

    if exploded.empty:
        return pd.DataFrame(columns=["level", "median_salary", "mean_salary", "count"])

    grouped = exploded.groupby("level")["monthly_max_salary"].agg(
        median_salary="median",
        mean_salary="mean",
        count="count",
    ).reset_index()
    return grouped.sort_values("median_salary", ascending=False)


def get_jobs_per_region(
    df: pd.DataFrame, kw_title_filter: str | None = None
) -> pd.DataFrame:
    """Groupby region → count(url), seřazeno sestupně."""
    filtered = _filter_by_kw_title(df, kw_title_filter)

    grouped = (
        filtered.groupby("region")["url"]
        .count()
        .reset_index()
        .rename(columns={"url": "job_count"})
    )
    return grouped.sort_values("job_count", ascending=False)


if __name__ == "__main__":
    # Standalone test — mock streamlit before re-importing
    import sys
    import types

    mock_st = types.ModuleType("streamlit")
    mock_st.cache_data = lambda ttl=None: (lambda fn: fn)
    sys.modules["streamlit"] = mock_st

    # Re-import with mock in place
    from importlib import reload
    mod = reload(sys.modules[__name__])

    print(f"DB path: {mod.DB_PATH} (exists: {mod.DB_PATH.exists()})")

    df = mod.load_all_jobs()
    print(f"Loaded {len(df)} rows")
    print(f"kw_title options: {mod.get_kw_title_options(df)[:5]}...")
    print(f"region options: {mod.get_region_options(df)[:5]}...")

    skills = mod.get_skills_counts(df)
    print(f"\nTop 5 skills:\n{skills.head()}")

    sal_role = mod.get_salary_per_kw_title(df)
    print(f"\nSalary per role (top 3):\n{sal_role.head(3)}")

    sal_skill = mod.get_salary_per_skill(df)
    print(f"\nSalary per skill (top 3):\n{sal_skill.head(3)}")

    sal_level = mod.get_salary_per_level(df)
    print(f"\nSalary per level:\n{sal_level}")

    jobs_region = mod.get_jobs_per_region(df)
    print(f"\nJobs per region (top 3):\n{jobs_region.head(3)}")

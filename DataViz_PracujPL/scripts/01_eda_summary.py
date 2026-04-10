"""
01_eda_summary.py
-----------------
Exploratory Data Analysis — overview of all tables.
Outputs a text summary to the console and saves a CSV profile per table
to outputs/reports/.

Run from project root:
    python scripts/01_eda_summary.py
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import date

# Allow importing from scripts/ as a package
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.db_connection import get_connection, list_tables, table_info

OUTPUT_DIR = Path(__file__).parent.parent / "outputs" / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TODAY = date.today().isoformat()


def profile_table(conn: sqlite3.Connection, table_name: str) -> pd.DataFrame:
    """Load a table into a DataFrame and return basic profile."""
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    return df


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def run_eda():
    conn = get_connection()
    tables = list_tables(conn)

    print_section(f"EDA Summary — Poland Labour Market DB ({TODAY})")
    print(f"Tables found: {len(tables)}")

    for table_name in tables:
        print_section(f"Table: {table_name}")
        df = profile_table(conn, table_name)

        print(f"  Shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
        print(f"\n  Columns & dtypes:")
        for col, dtype in df.dtypes.items():
            null_count = df[col].isna().sum()
            null_pct = null_count / len(df) * 100
            print(f"    {col:<30} {str(dtype):<15} nulls: {null_count} ({null_pct:.1f}%)")

        # Numeric columns — basic stats
        numeric_df = df.select_dtypes(include="number")
        if not numeric_df.empty:
            print(f"\n  Numeric summary:")
            print(numeric_df.describe().round(2).to_string(max_cols=10))

        # Duplicate check
        dupe_count = df.duplicated().sum()
        print(f"\n  Duplicates: {dupe_count}")

        # Save profile CSV
        out_path = OUTPUT_DIR / f"{TODAY}_{table_name}_profile.csv"
        df.describe(include="all").to_csv(out_path)
        print(f"\n  Profile saved: {out_path.name}")

    conn.close()
    print_section("EDA complete.")


if __name__ == "__main__":
    run_eda()

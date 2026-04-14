"""snapshot_history.py — Append daily job-count snapshots to CSV trend files.

Pipeline step 5 (after nerds_db_filter.py):
  nerd_jobs.db   → dashboard/data/history_roles.csv      (kw_title counts)
  job_database.db → dashboard/data/history_industries.csv (mapped_industry counts)
"""

import csv
import sqlite3
from datetime import date
from pathlib import Path

NERD_DB = "nerd_jobs.db"
JOB_DB = "job_database.db"

HISTORY_ROLES_CSV = Path("dashboard/data/history_roles.csv")
HISTORY_INDUSTRIES_CSV = Path("dashboard/data/history_industries.csv")

ROLES_HEADER = ["date", "kw_title", "job_count"]
INDUSTRIES_HEADER = ["date", "mapped_industry", "job_count"]


def _read_existing_dates(csv_path: Path) -> set[str]:
    """Return set of date strings already present in CSV."""
    if not csv_path.exists():
        return set()
    dates: set[str] = set()
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dates.add(row["date"])
    return dates


def _ensure_csv(csv_path: Path, header: list[str]) -> None:
    """Create CSV with header row if file doesn't exist."""
    if csv_path.exists():
        return
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)


def _append_rows(csv_path: Path, rows: list[list]) -> None:
    """Append rows to CSV (no header)."""
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def snapshot_roles(today: str) -> None:
    """Query nerd_jobs.db → COUNT(*) GROUP BY kw_title → append to CSV."""
    _ensure_csv(HISTORY_ROLES_CSV, ROLES_HEADER)

    existing = _read_existing_dates(HISTORY_ROLES_CSV)
    if today in existing:
        print(f"Skipping {HISTORY_ROLES_CSV} — {today} already recorded.")
        return

    conn = sqlite3.connect(NERD_DB)
    cursor = conn.execute(
        "SELECT kw_title, COUNT(*) AS job_count "
        "FROM nerd_jobs "
        "WHERE kw_title IS NOT NULL "
        "GROUP BY kw_title "
        "ORDER BY kw_title"
    )
    rows = [[today, kw_title, count] for kw_title, count in cursor]
    conn.close()

    _append_rows(HISTORY_ROLES_CSV, rows)
    print(f"Appended {len(rows)} role rows for {today} to {HISTORY_ROLES_CSV}")


def snapshot_industries(today: str) -> None:
    """Query job_database.db → COUNT(*) GROUP BY mapped_industry → append to CSV."""
    _ensure_csv(HISTORY_INDUSTRIES_CSV, INDUSTRIES_HEADER)

    existing = _read_existing_dates(HISTORY_INDUSTRIES_CSV)
    if today in existing:
        print(f"Skipping {HISTORY_INDUSTRIES_CSV} — {today} already recorded.")
        return

    conn = sqlite3.connect(JOB_DB)
    cursor = conn.execute(
        "SELECT mapped_industry, COUNT(*) AS job_count "
        "FROM job_offers "
        "WHERE mapped_industry IS NOT NULL "
        "GROUP BY mapped_industry "
        "ORDER BY mapped_industry"
    )
    rows = [[today, industry, count] for industry, count in cursor]
    conn.close()

    _append_rows(HISTORY_INDUSTRIES_CSV, rows)
    print(f"Appended {len(rows)} industry rows for {today} to {HISTORY_INDUSTRIES_CSV}")


def main() -> None:
    today = date.today().strftime("%Y-%m")
    print(f"Snapshot date: {today}")

    snapshot_roles(today)
    snapshot_industries(today)

    print("Done.")


if __name__ == "__main__":
    main()

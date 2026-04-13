"""
nerds_db_filter.py

Creates nerd_jobs.db (table: nerd_jobs) derived from job_database.db (table: job_offers)
by filtering rows whose `title` matches any keyword phrase from Nerd_mapped.csv,
and adding a `kw_title` column.

monthly_max_salary is taken directly from job_database.db (computed by monthly_salary_mapper).

CSV format (required):
- column: title          (keyword phrase; 2-3 words, but script supports >=1)
- column: mapped_title   (value to store into kw_title in output DB)

Matching rules:
- Case-insensitive
- Order of keyword words in job title doesn't matter
- Prefix match for each keyword token:
    keyword token "manag" matches title token "management", "manager", etc.
- Symbols in title are treated as separators (e.g., "Data-Management" works)
- First match wins (keywords evaluated in CSV order)

Output:
- nerd_jobs.db with table nerd_jobs having all columns from job_offers plus:
  - `kw_title`  inserted right after `title`
"""

import os
import re
import csv
import sqlite3
from typing import List, Tuple, Optional

SOURCE_DB    = "job_database.db"
SOURCE_TABLE = "job_offers"

KEYWORD_CSV    = "Nerd_mapped.csv"
CSV_KEYWORD_COL = "title"
CSV_MAPPED_COL  = "mapped_title"

TARGET_DB    = "nerd_jobs.db"
TARGET_TABLE = "nerd_jobs"

TOKEN_SPLIT_RE = re.compile(r"[\s\-/,.(){}\[\]:;|+*?!@#$%^&=<>\"'`~\\]+")


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def tokenize(text: str) -> List[str]:
    """Lowercase + split into tokens; symbols become separators."""
    if not text:
        return []
    text = text.lower().strip()
    return [t for t in TOKEN_SPLIT_RE.split(text) if t]


def load_keywords(csv_path: str) -> List[Tuple[List[str], str, str]]:
    """
    Returns list of (keyword_tokens, mapped_title, original_keyword_phrase).
    Keeps CSV order.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Keyword CSV not found: {csv_path}")

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV has no header row.")

        missing = [c for c in (CSV_KEYWORD_COL, CSV_MAPPED_COL) if c not in reader.fieldnames]
        if missing:
            raise ValueError(
                f"CSV is missing required columns: {missing}. "
                f"Found columns: {reader.fieldnames}"
            )

        out: List[Tuple[List[str], str, str]] = []
        for row in reader:
            kw     = (row.get(CSV_KEYWORD_COL) or "").strip()
            mapped = (row.get(CSV_MAPPED_COL)  or "").strip()
            if not kw:
                continue
            kw_tokens = tokenize(kw)
            if kw_tokens:
                out.append((kw_tokens, mapped, kw))
    return out


def title_matches_keyword(title_tokens: List[str], kw_tokens: List[str]) -> bool:
    """Unordered prefix match: each kw_token must be a prefix of some title token."""
    for kw in kw_tokens:
        if not any(tt.startswith(kw) for tt in title_tokens):
            return False
    return True


def find_kw_title(title: str, keywords: List[Tuple[List[str], str, str]]) -> Optional[str]:
    """Returns mapped_title for the first matching keyword, else None."""
    if not title:
        return None
    title_tokens = tokenize(title)
    if not title_tokens:
        return None
    for kw_tokens, mapped_title, kw_phrase in keywords:
        if title_matches_keyword(title_tokens, kw_tokens):
            return mapped_title if mapped_title else kw_phrase
    return None


def quote_ident(name: str) -> str:
    """Safely quote a SQLite identifier."""
    return '"' + name.replace('"', '""') + '"'


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main() -> None:

    # 1) Load keywords
    keywords = load_keywords(KEYWORD_CSV)
    print(f"✅ Loaded {len(keywords)} keywords from {KEYWORD_CSV}")

    # 2) Open source DB
    if not os.path.exists(SOURCE_DB):
        raise FileNotFoundError(f"Source DB not found: {SOURCE_DB}")

    src_conn = sqlite3.connect(SOURCE_DB)
    src_conn.row_factory = sqlite3.Row
    src_cur = src_conn.cursor()

    # 3) Read source schema + validate required columns
    src_cur.execute(f"PRAGMA table_info({quote_ident(SOURCE_TABLE)})")
    source_cols_info = src_cur.fetchall()
    if not source_cols_info:
        raise ValueError(f"Source table not found or has no columns: {SOURCE_TABLE}")

    src_col_names = [row["name"] for row in source_cols_info]

    for required in ("title", "monthly_max_salary"):
        if required not in src_col_names:
            raise ValueError(
                f'Source table "{SOURCE_TABLE}" is missing required column '
                f'"{required}". Run db_cleaner first. Found: {src_col_names}'
            )

    # 4) Build output column order — add only kw_title (after title)
    out_col_order: List[str] = []
    for c in src_col_names:
        out_col_order.append(c)
        if c == "title":
            out_col_order.append("kw_title")

    # 5) Prepare target DB (overwrite)
    if os.path.exists(TARGET_DB):
        try:
            os.remove(TARGET_DB)
        except PermissionError:
            print(f"⚠️  Cannot delete {TARGET_DB} — file is locked by another process.")
            print("   Close any programs using the file (DBeaver, VS Code SQLite viewer, etc.) and retry.")
            src_conn.close()
            return

    tgt_conn = sqlite3.connect(TARGET_DB)
    tgt_cur  = tgt_conn.cursor()

    # 6) CREATE TABLE — mirror source schema + kw_title
    col_defs: List[str] = []
    for row in source_cols_info:
        name    = row["name"]
        coltype = row["type"] or "TEXT"
        col_defs.append(f"{quote_ident(name)} {coltype}")
        if name == "title":
            col_defs.append(f'{quote_ident("kw_title")} TEXT')

    tgt_cur.execute(
        f"CREATE TABLE {quote_ident(TARGET_TABLE)} ({', '.join(col_defs)})"
    )
    tgt_conn.commit()

    # 7) Prepare SELECT / INSERT statements
    select_sql = (
        f"SELECT {', '.join(quote_ident(c) for c in src_col_names)} "
        f"FROM {quote_ident(SOURCE_TABLE)}"
    )
    insert_sql = (
        f"INSERT INTO {quote_ident(TARGET_TABLE)} "
        f"({', '.join(quote_ident(c) for c in out_col_order)}) "
        f"VALUES ({', '.join(['?'] * len(out_col_order))})"
    )

    # 8) Iterate → filter → insert
    src_cur.execute(select_sql)

    scanned  = 0
    inserted = 0

    while True:
        row = src_cur.fetchone()
        if row is None:
            break
        scanned += 1

        # Title keyword filter
        kw_title = find_kw_title(row["title"], keywords)
        if kw_title is None:
            continue

        # Build values list in out_col_order
        values = []
        for c in src_col_names:
            values.append(row[c])
            if c == "title":
                values.append(kw_title)

        tgt_cur.execute(insert_sql, values)
        inserted += 1

        if inserted % 5000 == 0:
            tgt_conn.commit()
            print(f"   … {inserted} rows inserted (scanned {scanned})")

    tgt_conn.commit()

    # 9) Final log
    print(f"\n✅ Done.")
    print(f"   Scanned  : {scanned} rows")
    print(f"   Inserted : {inserted} rows → {TARGET_DB} : {TARGET_TABLE}")

    src_conn.close()
    tgt_conn.close()


if __name__ == "__main__":
    main()

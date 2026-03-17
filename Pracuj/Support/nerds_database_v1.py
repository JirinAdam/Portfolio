#!/usr/bin/env python3
"""
nerds_database.py

Creates a filtered SQLite database nerd_jobs.db based on job_database.db / table job_offers.

- Loads keywords from Nerd_mapped.csv (column: "Database SME")
- Scans job_offers.title
- Matches a row if ALL keyword tokens (2-3 words) are found in the title
  regardless of order, using prefix matching per token (e.g., "manag" matches "management")
- Title tokenization is symbol-tolerant: punctuation like "-", "/", "()", "," etc. are treated as separators
- On first matching keyword, inserts the full original row into nerd_jobs, plus an extra column kw_title
  inserted right after column "title" and filled with the matched keyword string.

Usage:
  python nerds_database.py
"""

from __future__ import annotations

import sqlite3
import csv
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any


SOURCE_DB = "job_database.db"
SOURCE_TABLE = "job_offers"
KEYWORDS_CSV = "Nerd_mapped.csv"
KEYWORD_COLUMN = "title"

TARGET_DB = "nerd_jobs.db"
TARGET_TABLE = "nerd_jobs"


# ---------------------------
# Text normalization / match
# ---------------------------

_SPLIT_RE = re.compile(r"[^0-9a-zA-Z]+", re.UNICODE)

def _tokenize(text: str) -> List[str]:
    """
    Lowercase + split on any non-alphanumeric char.
    Keeps ASCII letters and digits. (If you later need diacritics, extend the regex.)
    """
    if text is None:
        return []
    text = text.strip().lower()
    if not text:
        return []
    return [t for t in _SPLIT_RE.split(text) if t]


def _keyword_to_tokens(keyword: str) -> List[str]:
    # Use same tokenizer; ensures consistent behavior for hyphens etc.
    return _tokenize(keyword)


def _unordered_prefix_match(title_tokens: List[str], kw_tokens: List[str]) -> bool:
    """
    Returns True if for every keyword token, there exists at least one title token
    that starts with the keyword token (prefix match). Order doesn't matter.
    """
    if not kw_tokens:
        return False
    # Slight micro-optimization: for each kw token, scan title tokens
    for kw in kw_tokens:
        found = False
        for tt in title_tokens:
            if tt.startswith(kw):
                found = True
                break
        if not found:
            return False
    return True


# ---------------------------
# CSV loading
# ---------------------------

def load_keywords(csv_path: Path) -> List[str]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Keywords CSV not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if KEYWORD_COLUMN not in reader.fieldnames:
            raise ValueError(
                f"CSV must contain column '{KEYWORD_COLUMN}'. Found: {reader.fieldnames}"
            )
        keywords = []
        for row in reader:
            kw = (row.get(KEYWORD_COLUMN) or "").strip()
            if kw:
                keywords.append(kw)

    # Keep order as-is (first match wins)
    return keywords


# ---------------------------
# SQLite helpers
# ---------------------------

def get_table_columns(conn: sqlite3.Connection, table_name: str) -> List[Tuple[str, str]]:
    """
    Returns list of (column_name, declared_type) from PRAGMA table_info.
    """
    cur = conn.execute(f"PRAGMA table_info({table_name})")
    rows = cur.fetchall()
    if not rows:
        raise ValueError(f"Table '{table_name}' not found or has no columns.")
    # rows: (cid, name, type, notnull, dflt_value, pk)
    return [(r[1], r[2] or "") for r in rows]


def build_create_table_sql(target_table: str, source_cols: List[Tuple[str, str]]) -> Tuple[str, List[str]]:
    """
    Build CREATE TABLE statement with an inserted kw_title column right after title.
    Returns (create_sql, column_order).
    """
    col_names = [c[0] for c in source_cols]
    col_types = {c[0]: (c[1] or "") for c in source_cols}

    if "title" not in col_names:
        raise ValueError("Source table must contain a 'title' column.")

    out_cols: List[str] = []
    col_defs: List[str] = []

    for name in col_names:
        out_cols.append(name)
        declared_type = col_types.get(name, "")
        if declared_type:
            col_defs.append(f'"{name}" {declared_type}')
        else:
            col_defs.append(f'"{name}"')

        if name == "title":
            out_cols.append("kw_title")
            col_defs.append('"kw_title" TEXT')

    create_sql = f'CREATE TABLE IF NOT EXISTS "{target_table}" (\n  ' + ",\n  ".join(col_defs) + "\n);"
    return create_sql, out_cols


def main() -> None:
    cwd = Path(".").resolve()
    source_db_path = cwd / SOURCE_DB
    keywords_csv_path = cwd / KEYWORDS_CSV
    target_db_path = cwd / TARGET_DB

    if not source_db_path.exists():
        raise FileNotFoundError(f"Source DB not found: {source_db_path}")

    keywords = load_keywords(keywords_csv_path)
    kw_token_lists = [(_keyword_to_tokens(k), k) for k in keywords]

    if not keywords:
        print("No keywords loaded; nothing to do.")
        return

    # Connect source
    src_conn = sqlite3.connect(str(source_db_path))
    src_conn.row_factory = sqlite3.Row
    src_cur = src_conn.cursor()

    # Discover schema
    source_cols = get_table_columns(src_conn, SOURCE_TABLE)
    create_sql, out_col_order = build_create_table_sql(TARGET_TABLE, source_cols)

    # Create / overwrite target DB
    if target_db_path.exists():
        target_db_path.unlink()

    tgt_conn = sqlite3.connect(str(target_db_path))
    tgt_cur = tgt_conn.cursor()
    tgt_cur.execute(create_sql)
    tgt_conn.commit()

    # Build select and insert SQL
    src_col_names = [c[0] for c in source_cols]

    quoted_src_cols = ", ".join([f'"{c}"' for c in src_col_names])
    select_sql = f'SELECT {quoted_src_cols} FROM "{SOURCE_TABLE}"'

    placeholders = ", ".join(["?"] * len(out_col_order))
    quoted_out_cols = ", ".join([f'"{c}"' for c in out_col_order])
    insert_sql = f'INSERT INTO "{TARGET_TABLE}" ({quoted_out_cols}) VALUES ({placeholders})'

    total = 0
    matched = 0

    for row in src_cur.execute(select_sql):
        total += 1
        title = row["title"]
        title_tokens = _tokenize(title or "")

        matched_kw: Optional[str] = None
        if title_tokens:
            for kw_tokens, kw_text in kw_token_lists:
                # Ensure 2-3 word keywords are enforced if you want:
                # if not (2 <= len(kw_tokens) <= 3): continue
                if _unordered_prefix_match(title_tokens, kw_tokens):
                    matched_kw = kw_text
                    break

        if matched_kw is None:
            continue

        matched += 1

        # Prepare output row in the exact column order
        out_values: List[Any] = []
        for col in out_col_order:
            if col == "kw_title":
                out_values.append(matched_kw)
            else:
                out_values.append(row[col])

        tgt_cur.execute(insert_sql, out_values)

        if matched % 1000 == 0:
            tgt_conn.commit()
            print(f"Inserted {matched} matches...")

    tgt_conn.commit()

    print(f"Done.")
    print(f"Total scanned rows: {total}")
    print(f"Matched rows inserted into {TARGET_DB}:{TARGET_TABLE}: {matched}")

    src_conn.close()
    tgt_conn.close()


if __name__ == "__main__":
    main()

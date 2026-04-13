#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nerds_database.py

Creates nerd_jobs.db (table: nerd_jobs) derived from job_database.db (table: job_offers)
by filtering rows whose `title` matches any keyword phrase from Nerd_mapped.csv.

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
- nerd_jobs.db with table nerd_jobs having all columns from job_offers plus `kw_title`
  inserted right after `title`.
"""

import os
import re
import csv
import sqlite3
from typing import List, Tuple, Optional

SOURCE_DB = "job_database.db"
SOURCE_TABLE = "job_offers"

KEYWORD_CSV = "Nerd_mapped.csv"   # user renamed columns inside this CSV
CSV_KEYWORD_COL = "title"
CSV_MAPPED_COL = "mapped_title"

TARGET_DB = "nerd_jobs.db"
TARGET_TABLE = "nerd_jobs"

# Treat these characters as token separators (in addition to whitespace)
TOKEN_SPLIT_RE = re.compile(r"[\s\-/,.(){}\[\]:;|+*?!@#$%^&=<>\"'`~\\]+")


def tokenize(text: str) -> List[str]:
    """Lowercase + split into tokens; symbols become separators."""
    if not text:
        return []
    text = text.lower().strip()
    toks = [t for t in TOKEN_SPLIT_RE.split(text) if t]
    return toks


def load_keywords(csv_path: str) -> List[Tuple[List[str], str, str]]:
    """
    Returns list of (keyword_tokens, mapped_title, original_keyword_phrase)
    Keeps CSV order.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Keyword CSV not found: {csv_path}")

    # utf-8-sig handles BOM if present
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
            kw = (row.get(CSV_KEYWORD_COL) or "").strip()
            mapped = (row.get(CSV_MAPPED_COL) or "").strip()
            if not kw:
                continue
            kw_tokens = tokenize(kw)
            if not kw_tokens:
                continue
            out.append((kw_tokens, mapped, kw))
    return out


def title_matches_keyword(title_tokens: List[str], kw_tokens: List[str]) -> bool:
    """
    Unordered prefix match: each kw_token must be a prefix of some title token.
    """
    for kw in kw_tokens:
        found = False
        for tt in title_tokens:
            if tt.startswith(kw):
                found = True
                break
        if not found:
            return False
    return True


def find_kw_title(title: str, keywords: List[Tuple[List[str], str, str]]) -> Optional[str]:
    """
    Returns mapped_title for the first matching keyword, else None.
    """
    if not title:
        return None
    title_tokens = tokenize(title)
    if not title_tokens:
        return None

    for kw_tokens, mapped_title, _kw_phrase in keywords:
        if title_matches_keyword(title_tokens, kw_tokens):
            return mapped_title if mapped_title != "" else _kw_phrase
    return None


def quote_ident(name: str) -> str:
    """Safely quote SQLite identifier (column/table name)."""
    return '"' + name.replace('"', '""') + '"'


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

    # 3) Read source schema
    src_cur.execute(f'PRAGMA table_info({quote_ident(SOURCE_TABLE)})')
    source_cols_info = src_cur.fetchall()
    if not source_cols_info:
        raise ValueError(f"Source table not found or has no columns: {SOURCE_TABLE}")

    src_col_names = [row["name"] for row in source_cols_info]

    if "title" not in src_col_names:
        raise ValueError(f'Source table "{SOURCE_TABLE}" has no column "title". Columns: {src_col_names}')

    # 4) Prepare output column order: all source cols + kw_title right after title
    out_col_order: List[str] = []
    for c in src_col_names:
        out_col_order.append(c)
        if c == "title":
            out_col_order.append("kw_title")

    # 5) Prepare target DB (overwrite)
    if os.path.exists(TARGET_DB):
        os.remove(TARGET_DB)

    tgt_conn = sqlite3.connect(TARGET_DB)
    tgt_cur = tgt_conn.cursor()

    # 6) Create target table with same schema + kw_title column.
    # We recreate the columns using the PRAGMA info. Types are kept, constraints are simplified.
    col_defs: List[str] = []
    for row in source_cols_info:
        name = row["name"]
        coltype = row["type"] or "TEXT"
        if name == "title":
            col_defs.append(f'{quote_ident(name)} {coltype}')
            col_defs.append(f'{quote_ident("kw_title")} TEXT')
        else:
            col_defs.append(f'{quote_ident(name)} {coltype}')

    create_sql = f'CREATE TABLE {quote_ident(TARGET_TABLE)} ({", ".join(col_defs)})'
    tgt_cur.execute(create_sql)
    tgt_conn.commit()

    # 7) Build SQL for reading and inserting
    quoted_src_cols = ", ".join([quote_ident(c) for c in src_col_names])
    select_sql = f'SELECT {quoted_src_cols} FROM {quote_ident(SOURCE_TABLE)}'

    placeholders = ", ".join(["?"] * len(out_col_order))
    quoted_out_cols = ", ".join([quote_ident(c) for c in out_col_order])
    insert_sql = f'INSERT INTO {quote_ident(TARGET_TABLE)} ({quoted_out_cols}) VALUES ({placeholders})'

    # 8) Iterate, match, insert
    src_cur.execute(select_sql)

    inserted = 0
    scanned = 0

    while True:
        row = src_cur.fetchone()
        if row is None:
            break
        scanned += 1

        title = row["title"]
        kw_title = find_kw_title(title, keywords)
        if kw_title is None:
            continue

        values = []
        for c in src_col_names:
            values.append(row[c])
            if c == "title":
                values.append(kw_title)

        tgt_cur.execute(insert_sql, values)
        inserted += 1

        if inserted % 5000 == 0:
            tgt_conn.commit()
            print(f"… inserted {inserted} rows (scanned {scanned})")

    tgt_conn.commit()

    print(f"✅ Done. Scanned {scanned} rows, inserted {inserted} nerd jobs into {TARGET_DB}:{TARGET_TABLE}")

    src_conn.close()
    tgt_conn.close()


if __name__ == "__main__":
    main()

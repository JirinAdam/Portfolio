"""
db_connection.py
----------------
Helper modul pro připojení k SQLite databázi.
Import: from scripts.db_connection import get_connection, list_tables, table_info

Přímé spuštění (ověření připojení):
    python scripts/db_connection.py
"""

import sqlite3
from pathlib import Path

# Cesta k databázi — relativně od rootu projektu
DB_PATH = Path(__file__).parent.parent / "data" / "job_database.db"


def get_connection() -> sqlite3.Connection:
    """Vrátí sqlite3 připojení k databázi."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Databáze nenalezena: {DB_PATH}\n"
            "Umísti SQLite soubor do: data/job_database.db"
        )
    conn = sqlite3.connect(DB_PATH)
    return conn


def list_tables(conn: sqlite3.Connection) -> list[str]:
    """Vrátí seznam všech tabulek v databázi."""
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    return [row[0] for row in cursor.fetchall()]


def table_info(conn: sqlite3.Connection, table_name: str) -> list[dict]:
    """Vrátí informace o sloupcích dané tabulky."""
    cursor = conn.execute(f"PRAGMA table_info({table_name});")
    return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    print(f"Připojuji k: {DB_PATH}")
    conn = get_connection()
    tables = list_tables(conn)
    print(f"\nNalezeno {len(tables)} tabulka/tabulky:")
    for t in tables:
        cols = table_info(conn, t)
        cursor = conn.execute(f"SELECT COUNT(*) FROM {t};")
        count = cursor.fetchone()[0]
        print(f"  - {t}: {len(cols)} sloupců, {count:,} řádků")
    conn.close()
    print("\nPřipojení OK.")

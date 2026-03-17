import json
import re
from typing import Optional, Dict, Any, List

from Pracuj.db_cleaner.base_mapper import BaseMapper


class LanguageMapper(BaseMapper):
    """
    Mapper pro detekci jazyků v job_offers.requirements_expected.

    - Hledá tokeny začínající na prefixy (Starts with)
    - První match pro token vyhrává
    - Výsledek ukládá do job_offers.mapped_languages jako JSON list (TEXT)
      např. ["German", "English"]
    """

    # Mapping natvrdo (z language_mapping.csv)
    LANGUAGE_RULES: List[Dict[str, str]] = [
        {"starts_with": "niemiecki",     "language": "German"},
        {"starts_with": "hiszpański",    "language": "Spanish"},
        {"starts_with": "niderlandzki",  "language": "Dutch"},
        {"starts_with": "włoski",        "language": "Italian"},
        {"starts_with": "francuski",     "language": "French"},
        {"starts_with": "duński",        "language": "Danish"},
        {"starts_with": "angielski",     "language": "English"},
        {"starts_with": "ukraiński",     "language": "Ukrainian"},
        {"starts_with": "rosyjski",      "language": "Russian"},
        {"starts_with": "czeski",        "language": "Czech"},
    ]

    def __init__(self, conn):
        super().__init__(conn)
        self._ensure_column_exists()

    # ──────────────────────────────────────────────
    # DB schema
    # ──────────────────────────────────────────────

    def _ensure_column_exists(self):
        """Přidá sloupec mapped_languages do job_offers, pokud ještě neexistuje."""
        self.cursor.execute("PRAGMA table_info(job_offers)")
        existing_columns = [row[1] for row in self.cursor.fetchall()]
        if "mapped_languages" not in existing_columns:
            self.cursor.execute("ALTER TABLE job_offers ADD COLUMN mapped_languages TEXT")
            self.conn.commit()
            print("➕ Sloupec 'mapped_languages' byl přidán do tabulky job_offers")

    # ──────────────────────────────────────────────
    # BaseMapper API
    # ──────────────────────────────────────────────

    def get_mapper_name(self) -> str:
        return "LANGUAGE DATA"

    def get_emoji(self) -> str:
        return "🌐"

    def get_column_name(self) -> str:
        return "mapped_languages"

    def get_select_query(self) -> str:
        return """
            SELECT partition_id, company, url, requirements_expected
            FROM job_offers
            WHERE requirements_expected IS NOT NULL
              AND requirements_expected != ''
        """

    def get_update_query(self) -> str:
        return """
            UPDATE job_offers
            SET mapped_languages = ?
            WHERE partition_id = ?
        """

    def process_row(self, row: tuple) -> Optional[Dict[str, Any]]:
        partition_id, company, url, requirements_expected = row

        detected = self._detect_languages(requirements_expected)
        if not detected:
            return None

        return {
            "partition_id": partition_id,
            "company": company,
            "url": url,
            "original": requirements_expected[:160],
            "languages_list": detected,
            "mapped_languages": json.dumps(detected, ensure_ascii=False),
        }

    def prepare_update_params(self, update_data: Dict[str, Any]) -> tuple:
        return (update_data["mapped_languages"], update_data["partition_id"])

    # ──────────────────────────────────────────────
    # Core logic
    # ──────────────────────────────────────────────

    def _detect_languages(self, text: str) -> List[str]:
        """
        Tokenizuje text na 'slova' a hledá prefix shody podle LANGUAGE_RULES.

        - token.startswith(prefix) => match
        - deduplikace jazyků (každý max 1x), zachová pořadí prvního výskytu
        """
        if not text:
            return []

        tokens = re.split(r"""[\s\-/,.()\[\]<>:;!"']+""", text.lower())
        tokens = [t for t in tokens if t]

        found: List[str] = []
        seen = set()

        for token in tokens:
            for rule in self.LANGUAGE_RULES:
                if token.startswith(rule["starts_with"]):
                    lang = rule["language"]
                    if lang not in seen:
                        found.append(lang)
                        seen.add(lang)
                    break  # první match pro token vyhrává

        return found

    # ──────────────────────────────────────────────
    # Output / logging helpers (stejně jako ostatní mappery)
    # ──────────────────────────────────────────────

    def show_example(self, index: int, data: Dict[str, Any]):
        langs = ", ".join(data["languages_list"])
        print(f"[{index}] Company: {data['company'][:50]}")
        print(f"    URL:     {data['url']}")
        print(f"    TEXT:    {data['original']}...")
        print(f"    JAZYKY:  {langs}\n")

    def show_statistics(self, updates_data: List[Dict[str, Any]], unchanged_count: int):
        lang_stats: Dict[str, int] = {}
        for data in updates_data:
            for lang in data["languages_list"]:
                lang_stats[lang] = lang_stats.get(lang, 0) + 1

        print("=" * 100)
        print(f"📈 VÝSLEDKY ANALÝZY - {self.get_mapper_name()}")
        print("=" * 100)
        print(f"✅ Řádků s detekovaným jazykem:     {len(updates_data)}")
        print(f"   Řádků beze změny / bez matchů:  {unchanged_count}")

        if lang_stats:
            print("\n   🌐 FREKVENCE JAZYKŮ:\n")
            for lang, count in sorted(lang_stats.items(), key=lambda x: -x[1]):
                print(f"      • {lang:20} {count:,} výskytů")

        print(f"\n   Celkem k updatu: {len(updates_data)} řádků\n")
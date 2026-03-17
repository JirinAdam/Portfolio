import json
from typing import Optional, Dict, Any, List
from Pracuj.db_cleaner.base_mapper import BaseMapper


class PositionLevelsMapper(BaseMapper):
    """
    Mapper pro position_levels - přeloží polské názvy úrovní do angličtiny (standardizuje)
    Očekává JSON seznam (např. '["specjalista (Mid / Regular)"]')
    """

    POSITION_LEVELS_MAPPING = [
        # POLSKÉ VERZE
        {'to_replace': 'praktykant / stażysta', 'replace_with': 'trainee'},
        {'to_replace': 'asystent', 'replace_with': 'assistant'},
        {'to_replace': 'młodszy specjalista (Junior)', 'replace_with': 'junior specialist'},
        {'to_replace': 'specjalista (Mid / Regular)', 'replace_with': 'specialist'},
        {'to_replace': 'starszy specjalista (Senior)', 'replace_with': 'senior specialist'},
        {'to_replace': 'ekspert', 'replace_with': 'expert'},
        {'to_replace': 'kierownik / koordynator', 'replace_with': 'team manager'},
        {'to_replace': 'menedżer', 'replace_with': 'manager'},
        {'to_replace': 'dyrektor', 'replace_with': 'director'},
        {'to_replace': 'prezes', 'replace_with': 'president'},
        {'to_replace': 'pracownik fizyczny', 'replace_with': 'manual worker'},

        # ANGLICKÉ VARIANTY / OPRAVY NA STANDARD
        {'to_replace': 'specialist (Mid / Regular)', 'replace_with': 'specialist'},
        {'to_replace': 'senior specialist (Senior)', 'replace_with': 'senior specialist'},
        {'to_replace': 'junior specialist (Junior)', 'replace_with': 'junior specialist'},
        {'to_replace': 'manager / supervisor', 'replace_with': 'manager'},
        {'to_replace': 'team manager', 'replace_with': 'team manager'},
        {'to_replace': 'manager', 'replace_with': 'manager'},
        {'to_replace': 'director', 'replace_with': 'director'},
        {'to_replace': 'president', 'replace_with': 'president'},
        {'to_replace': 'trainee', 'replace_with': 'trainee'},
        {'to_replace': 'assistant', 'replace_with': 'assistant'},
        {'to_replace': 'expert', 'replace_with': 'expert'},
        {'to_replace': 'entry level & blue collar', 'replace_with': 'manual worker'},
    ]

    def get_mapper_name(self) -> str:
        return "POSITION_LEVELS DATA"

    def get_emoji(self) -> str:
        return "📊"

    def get_column_name(self) -> str:
        return "position_levels"

    def get_select_query(self) -> str:
        return '''
            SELECT partition_id, company, url, position_levels
            FROM job_offers
            WHERE position_levels IS NOT NULL
              AND position_levels != ''
        '''

    def get_update_query(self) -> str:
        return '''
            UPDATE job_offers
            SET position_levels = ?
            WHERE partition_id = ?
        '''

    def process_row(self, row: tuple) -> Optional[Dict[str, Any]]:
        partition_id, company, url, position_levels = row

        translated = self._translate_position_levels(position_levels)

        if translated and translated != position_levels:
            return {
                'partition_id': partition_id,
                'company': company,
                'url': url,
                'original': position_levels,
                'translated': translated
            }

        return None

    def prepare_update_params(self, update_data: Dict[str, Any]) -> tuple:
        return (
            update_data['translated'],
            update_data['partition_id']
        )

    def show_example(self, index: int, data: Dict[str, Any]):
        print(f"[{index}] Company: {data['company'][:50]}")
        print(f"    URL: {data['url']}")
        print(f"    PŘED:  {data['original']}")
        print(f"    PO:    {data['translated']}\n")

    def show_statistics(self, updates_data: List[Dict[str, Any]], unchanged_count: int):
        # Spočítat výskyty standardizovaných úrovní
        levels_stats = {}
        for data in updates_data:
            try:
                levels = json.loads(data['translated'])
                if isinstance(levels, list):
                    for level in levels:
                        levels_stats[level] = levels_stats.get(level, 0) + 1
            except Exception:
                # pokud to není JSON (defenzivně), započítat celý string
                lvl = data['translated']
                levels_stats[lvl] = levels_stats.get(lvl, 0) + 1

        print("=" * 100)
        print(f"📈 VÝSLEDKY ANALÝZY - {self.get_mapper_name().upper()}")
        print("=" * 100)
        print(f"✅ Nalezeno {len(updates_data)} řádků k translaci:")
        print(f"   • K překladu/opravě:      {len(updates_data)} řádků")
        print(f"   • Už OK:                  {unchanged_count} řádků")
        print(f"\n   📋 STANDARDIZOVANÉ LEVELY:\n")

        for level in sorted(levels_stats.keys()):
            count = levels_stats[level]
            print(f"      • {level:30} {count:,} výskytů")

        print(f"\n   Celkem k updatu: {len(updates_data)} řádků\n")

    def _translate_position_levels(self, position_levels_text: str) -> Optional[str]:
        """
        Přelož position_levels z polštiny do angličtiny (JSON seznam)
        Pokud není validní JSON seznam, vrátí původní text.
        """
        if not position_levels_text:
            return None

        try:
            position_levels_list = json.loads(position_levels_text)
        except (ValueError, TypeError):
            # není validní JSON - necháme původní
            return position_levels_text

        if not isinstance(position_levels_list, list):
            return position_levels_text

        translated_list: List[str] = []

        for level in position_levels_list:
            if not level:
                continue

            translated = level
            for mapping_rule in self.POSITION_LEVELS_MAPPING:
                if level.lower().strip() == mapping_rule['to_replace'].lower().strip():
                    translated = mapping_rule['replace_with']
                    break

            translated_list.append(translated)

        try:
            result = json.dumps(translated_list, ensure_ascii=False)
        except Exception:
            result = json.dumps(translated_list)

        return result if result != position_levels_text else position_levels_text
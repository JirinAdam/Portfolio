import json
from typing import Optional, Dict, Any, List
from base_mapper import BaseMapper


class WorkModesMapper(BaseMapper):
    WORK_MODE_MAPPING = [
        {'to_replace': 'praca mobilna', 'replace_with': 'mobile work'},
        {'to_replace': 'praca hybrydowa', 'replace_with': 'hybrid work'},
        {'to_replace': 'praca stacjonarna', 'replace_with': 'full office work'},
        {'to_replace': 'praca zdalna', 'replace_with': 'remote work'}
    ]

    def get_mapper_name(self) -> str:
        return "WORK_MODES DATA"

    def get_emoji(self) -> str:
        return "🏢"

    def get_column_name(self) -> str:
        return "work_modes"

    def get_select_query(self) -> str:
        return '''
               SELECT partition_id, company, url, work_modes
               FROM job_offers
               WHERE work_modes IS NOT NULL
                 AND work_modes != '' \
               '''

    def get_update_query(self) -> str:
        return '''
               UPDATE job_offers
               SET work_modes = ?
               WHERE partition_id = ? \
               '''

    def process_row(self, row: tuple) -> Optional[Dict[str, Any]]:
        partition_id, company, url, work_modes = row

        translated = self._translate_work_modes(work_modes)

        if translated and translated != work_modes:
            return {
                'partition_id': partition_id,
                'company': company,
                'url': url,
                'original': work_modes,
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
        print("=" * 100)
        print(f"📈 VÝSLEDKY ANALÝZY - {self.get_mapper_name().upper()}")
        print("=" * 100)
        print(f"✅ Nalezeno {len(updates_data)} řádků k translaci:")
        print(f"   • K překladu:             {len(updates_data)} řádků")
        print(f"   • Už v angličtině:        {unchanged_count} řádků")
        print(f"\n   Celkem k updatu: {len(updates_data)} řádků\n")

    def _translate_work_modes(self, work_modes_text: str) -> Optional[str]:
        """Přelož work_modes z polštiny do angličtiny"""
        if not work_modes_text:
            return None

        try:
            work_modes_list = json.loads(work_modes_text)
        except (ValueError, TypeError):
            return work_modes_text

        if not isinstance(work_modes_list, list):
            return work_modes_text

        translated_list = []

        for mode in work_modes_list:
            translated = mode

            for mapping_rule in self.WORK_MODE_MAPPING:
                if mode.lower().strip() == mapping_rule['to_replace'].lower().strip():
                    translated = mapping_rule['replace_with']
                    break

            translated_list.append(translated)

        result = json.dumps(translated_list)
        return result if result != work_modes_text else work_modes_text
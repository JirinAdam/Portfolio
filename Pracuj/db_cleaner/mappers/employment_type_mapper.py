from typing import Optional, Dict, Any, List
from base_mapper import BaseMapper


class EmploymentTypeMapper(BaseMapper):
    EMPLOYMENT_TYPE_MAPPING = [
        {'to_replace': 'umowa o pracę', 'replace_with': 'employment contract'},
        {'to_replace': 'umowa zlecenie', 'replace_with': 'Contract for services'},
        {'to_replace': 'umowa o dzieło', 'replace_with': 'contract for specific work'},
        {'to_replace': 'kontrakt B2B', 'replace_with': 'B2B contract'},
        {'to_replace': 'umowa agencyjna', 'replace_with': 'agency agreement'},
        {'to_replace': 'umowa o pracę tymczasową', 'replace_with': 'fixed-term contract'},
        {'to_replace': 'umowa na zastępstwo', 'replace_with': 'substitution agreement'},
        {'to_replace': 'umowa o staż / praktyki', 'replace_with': 'internship / apprenticeship contract'},
        {'to_replace': 'contract of employment', 'replace_with': 'employment contract'}
    ]

    def get_mapper_name(self) -> str:
        return "EMPLOYMENT_TYPE DATA"

    def get_emoji(self) -> str:
        return "📄"

    def get_column_name(self) -> str:
        return "employment_type"

    def get_select_query(self) -> str:
        return '''
               SELECT partition_id, company, url, employment_type
               FROM job_offers
               WHERE employment_type IS NOT NULL
                 AND employment_type != '' \
               '''

    def get_update_query(self) -> str:
        return '''
               UPDATE job_offers
               SET employment_type = ?
               WHERE partition_id = ? \
               '''

    def process_row(self, row: tuple) -> Optional[Dict[str, Any]]:
        partition_id, company, url, employment_type = row

        translated = self._translate_employment_types(employment_type)

        if translated and translated != employment_type:
            return {
                'partition_id': partition_id,
                'company': company,
                'url': url,
                'original': employment_type,
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

    def _translate_employment_types(self, employment_type_text: str) -> Optional[str]:
        """Přelož employment_type z polštiny do angličtiny"""
        if not employment_type_text:
            return None

        employment_types_list = [item.strip() for item in employment_type_text.split(',')]

        if not employment_types_list or all(item == '' for item in employment_types_list):
            return employment_type_text

        translated_list = []

        for emp_type in employment_types_list:
            if not emp_type:
                continue

            translated = emp_type

            for mapping_rule in self.EMPLOYMENT_TYPE_MAPPING:
                if emp_type.lower().strip() == mapping_rule['to_replace'].lower().strip():
                    translated = mapping_rule['replace_with']
                    break

            translated_list.append(translated)

        result = ', '.join(translated_list)
        return result if result != employment_type_text else employment_type_text
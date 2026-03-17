import re
from typing import Optional, Dict, Any, List, Tuple
from Pracuj.db_cleaner.base_mapper import BaseMapper


class SalaryMapper(BaseMapper):
    CURRENCY_MAPPING = {
        '€': 'EUR', 'EUR': 'EUR', 'eur': 'EUR', 'EURO': 'EUR', 'Euro': 'EUR', 'euro': 'EUR',
        'PLN': 'PLN', 'pln': 'PLN', 'zł': 'PLN', 'ZŁ': 'PLN', 'zl': 'PLN',
        'Kč': 'CZK', 'kč': 'CZK', 'CZK': 'CZK', 'czk': 'CZK'
    }

    def get_mapper_name(self) -> str:
        return "SALARY DATA"

    def get_emoji(self) -> str:
        return "💰"

    def get_column_name(self) -> str:
        return "we_offer"

    def get_select_query(self) -> str:
        return '''
               SELECT partition_id, company, url, we_offer
               FROM job_offers
               WHERE salary_min IS NULL
                 AND we_offer IS NOT NULL
                 AND we_offer != '' \
               '''

    def get_update_query(self) -> str:
        return '''
               UPDATE job_offers
               SET salary_min      = ?,
                   salary_max      = ?,
                   salary_currency = ?
               WHERE partition_id = ? \
               '''

    def process_row(self, row: tuple) -> Optional[Dict[str, Any]]:
        partition_id, company, url, we_offer = row

        salary_min, salary_max, salary_currency = self._extract_salary_from_text(we_offer)

        if salary_min is not None:
            return {
                'partition_id': partition_id,
                'company': company,
                'url': url,
                'we_offer': we_offer,
                'salary_min': salary_min,
                'salary_max': salary_max,
                'salary_currency': salary_currency
            }

        return None

    def prepare_update_params(self, update_data: Dict[str, Any]) -> tuple:
        return (
            update_data['salary_min'],
            update_data['salary_max'],
            update_data['salary_currency'],
            update_data['partition_id']
        )

    def show_example(self, index: int, data: Dict[str, Any]):
        salary_display = (
            f"{data['salary_min']:,} - {data['salary_max']:,}"
            if data['salary_max']
            else f"{data['salary_min']:,}"
        )

        currency_display = data['salary_currency'] or 'N/A'

        print(f"[{index}] Company: {data['company'][:50]}")
        print(f"    URL: {data['url']}")
        print(f"    Salary: {salary_display} {currency_display}")
        print(f"    From text: {data['we_offer'][:90]}...\n")

    def show_statistics(self, updates_data: List[Dict[str, Any]], unchanged_count: int):
        with_range = sum(1 for d in updates_data if d['salary_max'] is not None)
        single_values = sum(1 for d in updates_data if d['salary_max'] is None)

        currency_counts = {}
        for data in updates_data:
            curr = data['salary_currency'] or 'UNKNOWN'
            currency_counts[curr] = currency_counts.get(curr, 0) + 1

        print("=" * 100)
        print(f"📈 VÝSLEDKY ANALÝZY - {self.get_mapper_name().upper()}")
        print("=" * 100)
        print(f"✅ Nalezeno {len(updates_data)} řádků se salary informacemi:")
        print(f"   • S range (min-max):     {with_range} řádků")
        print(f"   • S jedinou hodnotou:    {single_values} řádků")
        print(f"\n   💵 Měny:")
        for curr, count in sorted(currency_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"      • {curr:10} {count:,} řádků")
        print(f"\n   Celkem k updatu: {len(updates_data)} řádků\n")

    def _extract_salary_from_text(self, text: str) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        """Extrahuje salary a currency z textu"""
        pattern = r'(\d{3,})\s*(?:(€|EUR|eur|EURO|Euro|euro|PLN|pln|zł|ZŁ|zl|Kč|kč|CZK|czk))'
        matches = re.findall(pattern, text)

        if not matches:
            return None, None, None

        salaries = []
        detected_currency = None

        for salary_str, currency_str in matches:
            salaries.append(int(salary_str))

            if detected_currency is None and currency_str:
                detected_currency = self.CURRENCY_MAPPING.get(currency_str, currency_str)

        salaries = sorted(set(salaries))

        if len(salaries) >= 2:
            return salaries[0], salaries[-1], detected_currency
        elif len(salaries) == 1:
            return salaries[0], None, detected_currency
        else:
            return None, None, None
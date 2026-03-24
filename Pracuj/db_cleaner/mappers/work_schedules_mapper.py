import json
from typing import Optional, Dict, Any
from base_mapper import BaseMapper

WORK_SCHEDULES_MAPPING = [
    {'to_replace': 'pe\u0142ny etat', 'replace_with': 'full-time'},
    {'to_replace': 'cz\u0119\u015b\u0107 etatu"', 'replace_with': 'part time'},
    {'to_replace': 'część etatu', 'replace_with': 'part time'},
    {'to_replace': 'pełny etat', 'replace_with': 'full-time'},
    {'to_replace': 'dodatkowa / tymczasowa', 'replace_with': 'additional / temporary'},

    # anglické standardizace (pokud už jsou v angličtině)
    {'to_replace': 'full-time', 'replace_with': 'full-time'},
    {'to_replace': 'part time', 'replace_with': 'part time'},
    {'to_replace': 'additional / temporary', 'replace_with': 'additional / temporary'},
]


class WorkSchedulesMapper(BaseMapper):
    def get_mapper_name(self) -> str:
        return "WORK SCHEDULES"

    def get_emoji(self) -> str:
        return "🕒"

    def get_column_name(self) -> str:
        return "work_schedules"

    def get_select_query(self) -> str:
        return '''
               SELECT partition_id, company, url, work_schedules
               FROM job_offers
               WHERE work_schedules IS NOT NULL \
               '''

    def get_update_query(self) -> str:
        return '''
               UPDATE job_offers
               SET work_schedules = ?
               WHERE partition_id = ? \
               '''

    def process_row(self, row: tuple) -> Optional[Dict[str, Any]]:
        partition_id, company, url, work_schedules = row

        translated = self._translate_work_schedules(work_schedules)

        # Blanks -> NULLs: pokud po překladu nic nezůstane, vrátit None (tj. přeskočit update)
        if translated is None:
            return None

        # Pokud se nic nezměnilo (stejné jako původní text), nepotřebujeme update
        if translated == work_schedules:
            return None

        return {
            'partition_id': partition_id,
            'company': company,
            'url': url,
            'original_work_schedules': work_schedules,
            'translated_work_schedules': translated
        }

    def prepare_update_params(self, update_data: Dict[str, Any]) -> tuple:
        return (
            update_data['translated_work_schedules'],
            update_data['partition_id']
        )

    def show_example(self, index: int, update_data: Dict[str, Any]) -> str:
        """Formátuj jeden příklad pro výstup"""
        return (
            f"   [{index}] Company: {update_data['company'][:50]}\n"
            f"        URL: {update_data['url']}\n"
            f"        PŘED:  {update_data['original_work_schedules']}\n"
            f"        PO:    {update_data['translated_work_schedules']}"
        )

    def show_statistics(self, updates_data: list, unchanged_count: int = 0) -> None:
        """Zobraz statistiku přeložených dat"""
        schedules_stats = {}

        for data in updates_data:
            try:
                schedules = json.loads(data['translated_work_schedules'])
                if isinstance(schedules, list):
                    for schedule in schedules:
                        schedules_stats[schedule] = schedules_stats.get(schedule, 0) + 1
            except:
                # Pokud není JSON, zkus rozdělit čárkami
                schedules = data['translated_work_schedules'].split(', ')
                for schedule in schedules:
                    if schedule.strip():
                        schedules_stats[schedule.strip()] = schedules_stats.get(schedule.strip(), 0) + 1

        if schedules_stats:
            print("   🕒 STANDARDIZOVANÉ ÚVAZKY:\n")
            for schedule in sorted(schedules_stats.keys()):
                count = schedules_stats[schedule]
                print(f"      • {schedule:30} {count:,} výskytů")

            if unchanged_count > 0:
                print(f"\n   📊 Nezměněno: {unchanged_count:,} řádků")

        if schedules_stats:
            print("   🕒 STANDARDIZOVANÉ ÚVAZKY:\n")
            for schedule in sorted(schedules_stats.keys()):
                count = schedules_stats[schedule]
                print(f"      • {schedule:30} {count:,} výskytů")

    def _translate_work_schedules(self, work_schedules_text: str) -> Optional[str]:
        """
        Přeloží work_schedules (JSON list nebo čárkami oddělený string) z polštiny do angličtiny.
        - Pokud vstup je prázdný / po překladu nic nezbývá -> vrátí None (NULL).
        - Pokud vstup je JSON seznam -> vrátí JSON seznam (string).
        - Jinak vrátí čárkami oddělený string.
        """
        if not work_schedules_text:
            return None

        # Zkus parsovat jako JSON seznam
        is_json = False
        items = []
        try:
            parsed = json.loads(work_schedules_text)
            if isinstance(parsed, list):
                items = [str(x) for x in parsed if x]
                is_json = True
            else:
                # není list -> fallback na splitting
                raise ValueError
        except Exception:
            # fallback: split by comma
            items = [part.strip() for part in work_schedules_text.split(',') if part and part.strip()]

        if not items:
            return None

        translated_list = []
        for item in items:
            replaced = item
            for rule in WORK_SCHEDULES_MAPPING:
                if item.lower().strip() == rule['to_replace'].lower().strip():
                    replaced = rule['replace_with']
                    break
            translated_list.append(replaced)

        # Odeber prázdné položky a duplikáty, zachovej pořadí
        seen = set()
        cleaned = []
        for t in translated_list:
            if not t or t.strip() == '':
                continue
            key = t.strip().lower()
            if key not in seen:
                seen.add(key)
                cleaned.append(t.strip())

        if not cleaned:
            return None

        if is_json:
            try:
                return json.dumps(cleaned, ensure_ascii=False)
            except Exception:
                return None
        else:
            return ', '.join(cleaned)
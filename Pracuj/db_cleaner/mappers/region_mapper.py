from typing import Optional, Dict, Any, List
from Pracuj.db_cleaner.base_mapper import BaseMapper


class RegionMapper(BaseMapper):
    REGION_MAPPING = {
        'Lower Silesia': 'dolnośląskie',
        'Kuyavia-Pomerania': 'kujawsko-pomorskie',
        'Łódź': 'łódzkie',
        'Lublin': 'lubelskie',
        'Lubusz': 'lubuskie',
        'Lesser Poland': 'małopolskie',
        'Masovian': 'mazowieckie',
        'Opole': 'opolskie',
        'Subcarpathia': 'podkarpackie',
        'Podlaskie': 'podlaskie',
        'Pomeranian': 'pomorskie',
        'Silesian': 'śląskie',
        'Świętokrzyskie': 'świętokrzyskie',
        'Warmian-Mazurian': 'warmińsko-mazurskie',
        'Greater Poland': 'wielkopolskie',
        'abroad': 'zagranica',
        'West Pomeranian': 'zachodniopomorskie'
    }

    def get_mapper_name(self) -> str:
        return "REGION DATA"

    def get_emoji(self) -> str:
        return "🌍"

    def get_column_name(self) -> str:
        return "region"

    def get_select_query(self) -> str:
        english_regions = list(self.REGION_MAPPING.keys())
        placeholders = ','.join('?' * len(english_regions))
        return f'''
            SELECT partition_id, company, url, region
            FROM job_offers
            WHERE region IN ({placeholders})
        ''', tuple(english_regions)

    def get_update_query(self) -> str:
        return '''
               UPDATE job_offers
               SET region = ?
               WHERE partition_id = ? \
               '''

    def get_rows_to_process(self) -> List[tuple]:
        """Override pro REGION - speciální query s parametry"""
        query, params = self.get_select_query()
        # Tento hack je nutný, protože get_select_query vrací tuple
        self.cursor.execute(
            '''SELECT partition_id, company, url, region
               FROM job_offers
               WHERE region IN ({})'''.format(','.join('?' * len(self.REGION_MAPPING))),
            tuple(self.REGION_MAPPING.keys())
        )
        return self.cursor.fetchall()

    def process_row(self, row: tuple) -> Optional[Dict[str, Any]]:
        partition_id, company, url, region = row

        if region in self.REGION_MAPPING:
            return {
                'partition_id': partition_id,
                'company': company,
                'url': url,
                'english_region': region,
                'polish_region': self.REGION_MAPPING[region]
            }

        return None

    def prepare_update_params(self, update_data: Dict[str, Any]) -> tuple:
        return (
            update_data['polish_region'],
            update_data['partition_id']
        )

    def show_example(self, index: int, data: Dict[str, Any]):
        print(f"[{index}] Company: {data['company'][:50]}")
        print(f"    ID: {data['partition_id']}")
        print(f"    {data['english_region']} → {data['polish_region']}")
        print(f"    URL: {data['url']}\n")

    def show_statistics(self, updates_data: List[Dict[str, Any]], unchanged_count: int):
        print("=" * 100)
        print(f"📈 VÝSLEDKY ANALÝZY - {self.get_mapper_name().upper()}")
        print("=" * 100)
        print(f"✅ Nalezeno {len(updates_data)} řádků k translaci:")
        print(f"   • K překladu:             {len(updates_data)} řádků")
        print(f"   • Už v polštině:          {unchanged_count} řádků")

        # Detaily po regionech
        region_counts = {}
        for data in updates_data:
            pol_region = data['polish_region']
            region_counts[pol_region] = region_counts.get(pol_region, 0) + 1

        print(f"\n   🗺️  DISTRIBUCE REGIONŮ:\n")
        for region in sorted(region_counts.keys()):
            count = region_counts[region]
            print(f"      • {region:30} {count:,} řádků")

        print(f"\n   Celkem k updatu: {len(updates_data)} řádků\n")
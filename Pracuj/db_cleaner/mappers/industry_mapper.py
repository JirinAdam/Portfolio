import json
from typing import Optional, Dict, Any, List, Tuple
from Pracuj.db_cleaner.base_mapper import BaseMapper


class IndustryMapper(BaseMapper):
    """
    Mapper pro industry data - detekuje industry kategorii z textu
    Mapuje na mapped_industry (kategorie EN) a kw_industry (klíčová slova EN)
    """

    INDUSTRY_MAPPING = [
        {
            'priority': 1,
            'category_en': 'IT & Digital Tech',
            'keywords_pl': [
                'it', 'programowanie', 'software development', 'testowanie', 'qa',
                'ux/ui', 'user experience', 'webdesign', 'data science', 'analiza systemowa',
                'wdrożenia erp', 'bezpieczeństwo it', 'cloud', 'devops', 'administrowanie sieciami',
                'architektura it', 'zarządzanie projektem it', 'bazy danych', 'storage',
                'administracja', 'administrowanie systemami', 'wsparcie techniczne', 'helpdesk'
            ],
            'keywords_en': [
                'programming', 'software development', 'testing', 'ux/ui', 'web design',
                'system analysis', 'erp implementation', 'it security', 'it project management',
                'architecture it', 'database', 'administration', 'system administration',
                'technical support', 'helpdesk'
            ]
        },
        {
            'priority': 2,
            'category_en': 'Medicine & Pharma',
            'keywords_pl': [
                'medycyna', 'farmacja', 'apteka', 'lekarz', 'biotechnologia', 'badania kliniczne',
                'chemia', 'kosmetyky', 'zdrowie', 'biochemi', 'farmaceutyka'
            ],
            'keywords_en': [
                'medicine', 'pharma', 'pharmaceutical', 'clinical research', 'chemistry',
                'cosmetics', 'health', 'biotech', 'pharmacy'
            ]
        },
        {
            'priority': 3,
            'category_en': 'Finance & Banking',
            'keywords_pl': [
                'finanse', 'księgowość', 'audyt', 'podatki', 'ekonomia', 'controlling',
                'ubezpieczenia', 'ryzyko', 'bankowość', 'aktuariat', 'analiza finansowa',
                'bookkeeping', 'audyt/podatki', 'analiza'
            ],
            'keywords_en': [
                'finance', 'accounting', 'audit', 'taxes', 'controlling', 'insurance',
                'risk', 'banking', 'actuary', 'bookkeeping', 'analysis'
            ]
        },
        {
            'priority': 4,
            'category_en': 'Engineering & Design',
            'keywords_pl': [
                'inżynieria', 'automatyka', 'projektowanie', 'konstrukcja', 'r&d', 'cad',
                'badania i rozwój', 'zapewnienie jakości', 'technologie', 'energetyka', 'budowa maszyn',
                'elektronika', 'elektryka'
            ],
            'keywords_en': [
                'engineering', 'automation', 'design', 'r&d', 'cad', 'quality assurance',
                'technology', 'power engineering', 'electronics', 'electrics'
            ]
        },
        {
            'priority': 5,
            'category_en': 'Technical Sales & B2B',
            'keywords_pl': [
                'sprzedaż', 'sales', 'usługi profesjonalne', 'b2b', 'oze', 'energia',
                'motoryzacja', 'rolnictwo', 'nieruchomości'
            ],
            'keywords_en': [
                'sales', 'professional services', 'b2b', 'res', 'energy', 'automotive',
                'agriculture', 'real estate'
            ]
        },
        {
            'priority': 6,
            'category_en': 'Skilled Trades',
            'keywords_pl': [
                'elektryk', 'mechanik', 'monter', 'serwisant', 'operator cnc', 'spawacz',
                'utrzymanie ruchu', 'kontrola jakości', 'technik', 'blacharz', 'lakiernik',
                'instalacje', 'serwisanci'
            ],
            'keywords_en': [
                'electrician', 'mechanic', 'fitter', 'service technician', 'cnc operator',
                'welder', 'maintenance', 'quality control', 'installations'
            ]
        },
        {
            'priority': 7,
            'category_en': 'Construction & Real Estate',
            'keywords_pl': [
                'budownictwo', 'nieruchomości', 'infrastruktura', 'mieszkaniowe',
                'zarządzanie nieruchomościami', 'facility management', 'wynajem/wycena',
                'ekspansja', 'energetyczne'
            ],
            'keywords_en': [
                'construction', 'real estate', 'infrastructure', 'property management',
                'valuation', 'expansion'
            ]
        },
        {
            'priority': 8,
            'category_en': 'Logistics & Supply Chain',
            'keywords_pl': [
                'transport', 'logistyka', 'spedycja', 'łańcuch dostaw', 'kierowca',
                'magazynowanie', 'zakupy', 'procurement', 'fleet', 'category management'
            ],
            'keywords_en': [
                'logistics', 'forwarding', 'supply chain', 'driver', 'warehousing',
                'purchasing', 'fleet management'
            ]
        },
        {
            'priority': 9,
            'category_en': 'Legal & Compliance',
            'keywords_pl': [
                'prawo', 'prawnik', 'legal', 'compliance', 'kancelaria', 'zamówienia publiczne',
                'bhp', 'ochrona środowiska', 'urzędnicy'
            ],
            'keywords_en': [
                'law', 'lawyer', 'legal services', 'compliance', 'public procurement',
                'health and safety', 'public sector'
            ]
        },
        {
            'priority': 10,
            'category_en': 'Marketing & Creative',
            'keywords_pl': [
                'marketing', 'e-commerce', 'social media', 'reklama', 'grafika', 'copywriting',
                'pr', 'eventy', 'seo', 'sem', 'media', 'animacja', 'e-marketing'
            ],
            'keywords_en': [
                'marketing', 'advertising', 'graphic design', 'public relations',
                'e-marketing', 'social media', 'seo', 'creative'
            ]
        },
        {
            'priority': 11,
            'category_en': 'HR & Recruitment',
            'keywords_pl': [
                'human resources', 'rekrutacja', 'kadry', 'płace', 'employer branding',
                'zarządzanie hr', 'payroll', 'szkolenia/rozwój'
            ],
            'keywords_en': [
                'hr', 'recruitment', 'personnel', 'payroll', 'people management',
                'training & development'
            ]
        },
        {
            'priority': 12,
            'category_en': 'Education & Science',
            'keywords_pl': [
                'edukacja', 'szkolenia', 'nauka', 'szkolnictwo', 'lektor', 'nauczyciel',
                'tłumaczenia', 'sport/rekreacja'
            ],
            'keywords_en': [
                'education', 'training', 'science', 'teaching', 'lecturer', 'translations', 'sport'
            ]
        },
        {
            'priority': 13,
            'category_en': 'Retail & Front Office',
            'keywords_pl': [
                'sprzedawca', 'kasjer', 'sieci handlowe', 'sklep', 'merchandiser',
                'odzież', 'produkty spożywcze', 'agd/rtv', 'fmcg'
            ],
            'keywords_en': [
                'retail', 'shop assistant', 'cashier', 'merchandising', 'clothing',
                'groceries', 'fmcg'
            ]
        },
        {
            'priority': 14,
            'category_en': 'Customer Service & Admin',
            'keywords_pl': [
                'obsługa klienta', 'call center', 'recepcja', 'sekretariat', 'administracja biurowa',
                'wprowadzanie danych', 'stanowiska asystenckie'
            ],
            'keywords_en': [
                'customer service', 'support', 'reception', 'secretary', 'office admin',
                'data entry', 'assistant'
            ]
        },
        {
            'priority': 15,
            'category_en': 'Hospitality & Gastronomy',
            'keywords_pl': [
                'hotelarstwo', 'gastronomia', 'turystyka', 'kucharz', 'kelner',
                'katering', 'pracownicy gastronomii'
            ],
            'keywords_en': [
                'hospitality', 'gastronomy', 'tourism', 'chef', 'waiter', 'catering'
            ]
        },
        {
            'priority': 16,
            'category_en': 'General Labor',
            'keywords_pl': [
                'praca fizyczna', 'produkcja', 'pracownik produkcyjny', 'kurier',
                'dostawca', 'sprzątanie', 'ochrona', 'rolnictwo', 'pracownik ochrony'
            ],
            'keywords_en': [
                'manual labor', 'production worker', 'courier', 'delivery',
                'cleaning', 'security', 'farming'
            ]
        }
    ]

    def get_mapper_name(self) -> str:
        return "INDUSTRY DATA"

    def get_emoji(self) -> str:
        return "🏭"

    def get_column_name(self) -> str:
        return "industry"

    def get_select_query(self) -> str:
        return '''
            SELECT partition_id, company, url, industry
            FROM job_offers
            WHERE mapped_industry IS NULL
              AND industry IS NOT NULL
              AND industry != ''
        '''

    def get_update_query(self) -> str:
        return '''
            UPDATE job_offers
            SET mapped_industry = ?,
                kw_industry = ?
            WHERE partition_id = ?
        '''

    def __init__(self, conn):
        """Přidej sloupce pokud neexistují"""
        super().__init__(conn)
        self._ensure_columns_exist()

    def _ensure_columns_exist(self):
        """Přidej mapped_industry a kw_industry sloupce pokud neexistují"""
        try:
            # Zjisti aktuální sloupce
            self.cursor.execute("PRAGMA table_info(job_offers)")
            column_names = [col[1] for col in self.cursor.fetchall()]

            # Přidej mapped_industry pokud neexistuje
            if 'mapped_industry' not in column_names:
                print("   ➕ Přidávám sloupec: mapped_industry")
                self.cursor.execute(
                    'ALTER TABLE job_offers ADD COLUMN mapped_industry TEXT DEFAULT NULL'
                )
                self.conn.commit()
                print("      ✅ OK")

            # Přidej kw_industry pokud neexistuje
            if 'kw_industry' not in column_names:
                print("   ➕ Přidávám sloupec: kw_industry")
                self.cursor.execute(
                    'ALTER TABLE job_offers ADD COLUMN kw_industry TEXT DEFAULT NULL'
                )
                self.conn.commit()
                print("      ✅ OK")

        except Exception as e:
            print(f"   ⚠️  SQLite chyba: {e}")
            print("   (Sloupce pravděpodobně již existují)")
            self.conn.rollback()

    def process_row(self, row: tuple) -> Optional[Dict[str, Any]]:
        partition_id, company, url, industry = row

        category_en, keywords_en = self._detect_industry_mapping(industry)

        if category_en is not None:
            return {
                'partition_id': partition_id,
                'company': company,
                'url': url,
                'industry': industry,
                'mapped_industry': category_en,
                'kw_industry': keywords_en
            }

        return None

    def prepare_update_params(self, update_data: Dict[str, Any]) -> tuple:
        return (
            update_data['mapped_industry'],
            update_data['kw_industry'],
            update_data['partition_id']
        )

    def show_example(self, index: int, data: Dict[str, Any]):
        print(f"[{index}] Company: {data['company'][:50]}")
        print(f"    URL: {data['url']}")
        print(f"    Original Industry: {data['industry'][:70]}")
        print(f"    Mapped Category: {data['mapped_industry']}")
        print(f"    Keywords Found: {data['kw_industry']}\n")

    def show_statistics(self, updates_data: List[Dict[str, Any]], unchanged_count: int):
        # Spočítat výskyty kategorií
        category_counts = {}
        unmapped_count = 0

        for data in updates_data:
            cat = data['mapped_industry']
            if cat:
                category_counts[cat] = category_counts.get(cat, 0) + 1
            else:
                unmapped_count += 1

        print("=" * 100)
        print(f"📈 VÝSLEDKY ANALÝZY - {self.get_mapper_name().upper()}")
        print("=" * 100)
        print(f"✅ Nalezeno {len(updates_data)} řádků k mapování:")
        print(f"   • Mapováno:               {len(updates_data)} řádků")
        print(f"   • Nenamapováno:           {unmapped_count} řádků")
        print(f"\n   📊 DISTRIBUCE KATEGORIÍ:\n")

        for cat in sorted(category_counts.keys()):
            count = category_counts[cat]
            print(f"      • {cat:35} {count:,} řádků")

        print(f"\n   Celkem k updatu: {len(updates_data)} řádků\n")

    def clean_data(self) -> int:
        """
        Override: nejdřív zkontroluj sloupce, pak volej parent
        """
        print("\n" + "=" * 100)
        print(f"{self.get_emoji()} ČIŠTĚNÍ {self.get_mapper_name().upper()}")
        print("=" * 100 + "\n")

        print("📊 Kontrola a přidání sloupců...\n")

        # Sloupce se přidají v __init__, ale zobraž info
        # (v __init__ je sloupce přidáno, takže tady jen potvrdíme)
        self.cursor.execute("PRAGMA table_info(job_offers)")
        column_names = [col[1] for col in self.cursor.fetchall()]

        if 'mapped_industry' in column_names and 'kw_industry' in column_names:
            print("✅ Sloupce jsou připraveny\n")
        else:
            print("⚠️  Sloupce se nepodařilo přidat\n")
            return 0

        # Teď volej standardní chování z BaseMapper
        return super().clean_data()

    def _detect_industry_mapping(self, industry_text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Detekuj kategorii (EN) a klíčová slova z Industry textu

        Vrací tuple: (category_en, keywords_found_en)
        - category_en: Finální kategorie (EN) z INDUSTRY_MAPPING
        - keywords_found_en: Čárkou oddělený seznam nalezených klíčových slov v angličtině

        Logika:
        - Projdi INDUSTRY_MAPPING od priority 1 (nejvyšší)
        - Hledej ANY klíčové slovo z kategorie v textu
        - Vrať první shodu + seznam nalezených klíčových slov
        """
        if not industry_text:
            return None, None

        # Normalizuj vstup
        industry_text_lower = industry_text.lower().strip()

        # Projdi mapování podle priority (od 1 nahoru)
        for mapping in sorted(self.INDUSTRY_MAPPING, key=lambda x: x['priority']):
            category_en = mapping['category_en']
            keywords_pl = mapping['keywords_pl']
            keywords_en = mapping['keywords_en']

            # Hledej klíčová slova v textu
            found_keywords_en = []

            for keyword_pl, keyword_en in zip(keywords_pl, keywords_en):
                # Case-insensitive vyhledávání
                if keyword_pl.lower() in industry_text_lower:
                    found_keywords_en.append(keyword_en)

            # Pokud jsme našli nějaké klíčové slovo, vrať kategorii + slova
            if found_keywords_en:
                # Odeber duplikáty a seřaď
                found_keywords_en = sorted(set(found_keywords_en))
                keywords_str = ', '.join(found_keywords_en)
                return category_en, keywords_str

        # Pokud nic není nalezeno
        return None, None

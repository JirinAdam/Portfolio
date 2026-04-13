import json
import re
from typing import Optional, Dict, Any, List, Tuple
from base_mapper import BaseMapper


class IndustryMapper(BaseMapper):
    """
    Mapper pro industry data - detekuje industry kategorii z textu
    Mapuje na mapped_industry (kategorie EN) a kw_industry (klíčová slova EN)

    keywords: dict {polsky_keyword: anglicky_preklad}
      - kazdy par je 1:1, nelze mit nesoulad poctu
      - matching pouziva word boundaries (regex), ne substring 'in'
    """

    INDUSTRY_MAPPING = [
        {
            'priority': 1,
            'category_en': 'IT & Digital Tech',
            'keywords': {
                'it - administracja': 'it administration',
                'it - rozwój oprogramowania': 'software development',
                'it-administration': 'it administration',
                'it software development': 'software development',
                'programowanie': 'programming',
                'programming': 'programming',
                'software development': 'software development',
                'testowanie': 'testing',
                'testing': 'testing',
                'qa': 'qa',
                'ux/ui': 'ux/ui',
                'user experience': 'user experience',
                'webdesign': 'web design',
                'data science': 'data science',
                'analiza biznesowa i systemowa': 'system analysis',
                'business analysis': 'business analysis',
                'wdrożenia erp': 'erp implementation',
                'bezpieczeństwo it': 'it security',
                'cloud': 'cloud',
                'devops': 'devops',
                'administrowanie sieciami': 'network administration',
                'administration of nets': 'network administration',
                'architektura it': 'it architecture',
                'zarządzanie projektem it': 'it project management',
                'project management': 'project management',
                'bazy danych': 'database',
                'administration of databases': 'database',
                'storage': 'storage',
                'administrowanie systemami': 'system administration',
                'administration of systems': 'system administration',
                'wsparcie techniczne': 'technical support',
                'support / helpdesk': 'helpdesk',
                'helpdesk': 'helpdesk',
                'it / telekomunikacja': 'it/telecom',
            }
        },
        {
            'priority': 2,
            'category_en': 'Medicine & Pharma',
            'keywords': {
                'medycyna': 'medicine',
                'farmacja': 'pharma',
                'farmaceutyka': 'pharmaceutical',
                'apteka': 'pharmacy',
                'lekarz': 'doctor',
                'lekarze': 'doctors',
                'biotechnologia': 'biotech',
                'badania kliniczne': 'clinical research',
                'chemia': 'chemistry',
                'kosmetyka': 'cosmetics',
                'zdrowie': 'health',
                'biochemi': 'biochemistry',
                'farmacja / medycyna': 'pharma/medicine',
            }
        },
        {
            'priority': 3,
            'category_en': 'Finance & Banking',
            'keywords': {
                'finanse': 'finance',
                'finance': 'finance',
                'księgowość': 'accounting',
                'bookkeeping': 'bookkeeping',
                'audyt': 'audit',
                'audit': 'audit',
                'podatki': 'taxes',
                'taxes': 'taxes',
                'ekonomia': 'economics',
                'economy': 'economics',
                'controlling': 'controlling',
                'kontroling': 'controlling',
                'ubezpieczenia': 'insurance',
                'ryzyko': 'risk',
                'bankowość': 'banking',
                'banking': 'banking',
                'aktuariat': 'actuary',
                'analiza finansowa': 'financial analysis',
                'pośrednictwo finansowe': 'financial brokerage',
                'finanse / bankowość / ubezpieczenia': 'finance/banking/insurance',
            }
        },
        {
            'priority': 4,
            'category_en': 'Engineering & Design',
            'keywords': {
                'inżynieria': 'engineering',
                'automatyka': 'automation',
                'projektowanie': 'design',
                'konstrukcja': 'construction engineering',
                'r&d': 'r&d',
                'cad': 'cad',
                'badania i rozwój': 'r&d',
                'zapewnienie jakości': 'quality assurance',
                'zarządzanie jakością': 'quality management',
                'technologie': 'technology',
                'energetyka': 'power engineering',
                'budowa maszyn': 'mechanical engineering',
                'elektronika': 'electronics',
                'elektryka': 'electrics',
                'mechanika': 'mechanics',
                'inżynieria / technika / produkcja': 'engineering/production',
            }
        },
        {
            'priority': 5,
            'category_en': 'Technical Sales & B2B',
            'exclude_keywords': ['nieruchomości'],
            'keywords': {
                'sprzedaż': 'sales',
                'sales': 'sales',
                'usługi profesjonalne': 'professional services',
                'b2b': 'b2b',
                'oze': 'renewable energy',
                'energia': 'energy',
                'energia / środowisko / oze': 'energy/environment',
                'motoryzacja': 'automotive',
            }
        },
        {
            'priority': 6,
            'category_en': 'Skilled Trades',
            'keywords': {
                'elektryk': 'electrician',
                'mechanik': 'mechanic',
                'monter': 'fitter',
                'monterzy': 'fitters',
                'serwisant': 'service technician',
                'serwisanci': 'service technicians',
                'operator cnc': 'cnc operator',
                'spawacz': 'welder',
                'utrzymanie ruchu': 'maintenance',
                'kontrola jakości': 'quality control',
                'technik': 'technician',
                'blacharz': 'sheet metal worker',
                'lakiernik': 'painter',
                'instalacje': 'installations',
            }
        },
        {
            'priority': 7,
            'category_en': 'Construction & Real Estate',
            'keywords': {
                'budownictwo': 'construction',
                'nieruchomości': 'real estate',
                'infrastruktura': 'infrastructure',
                'infrastrukturalne': 'infrastructure',
                'mieszkaniowe': 'residential',
                'zarządzanie nieruchomościami': 'property management',
                'facility management': 'facility management',
                'wynajem/wycena': 'valuation',
                'ekspansja': 'expansion',
                'energetyczne': 'energy infrastructure',
                'nieruchomości / budownictwo': 'real estate/construction',
            }
        },
        {
            'priority': 8,
            'category_en': 'Logistics & Supply Chain',
            'keywords': {
                'transport': 'transport',
                'logistyka': 'logistics',
                'spedycja': 'forwarding',
                'łańcuch dostaw': 'supply chain',
                'kierowca': 'driver',
                'kierowcy': 'drivers',
                'magazynowanie': 'warehousing',
                'zakupy': 'purchasing',
                'procurement': 'procurement',
                'fleet': 'fleet management',
                'category management': 'category management',
                'transport / spedycja / logistyka': 'transport/forwarding/logistics',
                'kurierzy / dostawcy': 'couriers/delivery',
            }
        },
        {
            'priority': 9,
            'category_en': 'Legal & Compliance',
            'keywords': {
                'prawo': 'law',
                'prawnik': 'lawyer',
                'legal': 'legal services',
                'compliance': 'compliance',
                'kancelaria': 'law firm',
                'zamówienia publiczne': 'public procurement',
                'bhp': 'health and safety',
                'ochrona środowiska': 'environmental protection',
                'urzędnicy': 'public sector',
            }
        },
        {
            'priority': 10,
            'category_en': 'Marketing & Creative',
            'keywords': {
                'marketing': 'marketing',
                'e-commerce': 'e-commerce',
                'social media': 'social media',
                'reklama': 'advertising',
                'grafika': 'graphic design',
                'copywriting': 'copywriting',
                'public relations': 'public relations',
                'eventy': 'events',
                'seo': 'seo',
                'sem': 'sem',
                'animacja': 'animation',
                'e-marketing': 'e-marketing',
                'e-marketing / sem / seo': 'e-marketing/sem/seo',
            }
        },
        {
            'priority': 11,
            'category_en': 'HR & Recruitment',
            'keywords': {
                'human resources': 'hr',
                'zasoby ludzkie': 'hr',
                'rekrutacja': 'recruitment',
                'kadry': 'personnel',
                'płace': 'payroll',
                'employer branding': 'employer branding',
                'zarządzanie hr': 'hr management',
                'payroll': 'payroll',
                'szkolenia/rozwój': 'training & development',
                'rekrutacja / employer branding': 'recruitment/employer branding',
            }
        },
        {
            'priority': 12,
            'category_en': 'Education & Science',
            'keywords': {
                'edukacja': 'education',
                'szkolenia': 'training',
                'nauka': 'science',
                'szkolnictwo': 'teaching',
                'lektor': 'lecturer',
                'nauczyciel': 'teacher',
                'tłumaczenia': 'translations',
                'sport/rekreacja': 'sport',
                'edukacja / szkolenia': 'education/training',
            }
        },
        {
            'priority': 13,
            'category_en': 'Retail & Front Office',
            'keywords': {
                'sprzedawca': 'retail',
                'sprzedawcy': 'retail',
                'kasjer': 'cashier',
                'kasjerzy': 'cashiers',
                'sieci handlowe': 'retail chains',
                'sklep': 'shop',
                'merchandiser': 'merchandising',
                'odzież': 'clothing',
                'produkty spożywcze': 'groceries',
                'artykuły spożywcze': 'groceries',
                'agd/rtv': 'electronics retail',
                'fmcg': 'fmcg',
            }
        },
        {
            'priority': 14,
            'category_en': 'Customer Service & Admin',
            'keywords': {
                'obsługa klienta': 'customer service',
                'call center': 'call center',
                'recepcja': 'reception',
                'sekretariat': 'secretary',
                'administracja biurowa': 'office admin',
                'wprowadzanie danych': 'data entry',
                'stanowiska asystenckie': 'assistant',
            }
        },
        {
            'priority': 15,
            'category_en': 'Hospitality & Gastronomy',
            'keywords': {
                'hotelarstwo': 'hospitality',
                'gastronomia': 'gastronomy',
                'turystyka': 'tourism',
                'kucharz': 'chef',
                'kelner': 'waiter',
                'katering': 'catering',
                'pracownicy gastronomii': 'gastronomy workers',
                'hotelarstwo / gastronomia / turystyka': 'hospitality/gastronomy/tourism',
            }
        },
        {
            'priority': 16,
            'category_en': 'General Labor',
            'keywords': {
                'praca fizyczna': 'manual labor',
                'produkcja': 'production',
                'pracownik produkcyjny': 'production worker',
                'pracownicy produkcji': 'production workers',
                'pracownicy produkcyjni': 'production workers',
                'kurier': 'courier',
                'dostawca': 'delivery',
                'sprzątanie': 'cleaning',
                'utrzymanie czystości': 'cleaning',
                'ochrona': 'security',
                'pracownik ochrony': 'security guard',
                'pracownicy ochrony': 'security guards',
                'pracownicy magazynowi': 'warehouse workers',
                'pracownicy budowlani': 'construction workers',
            }
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

    @staticmethod
    def _keyword_matches(keyword: str, text: str) -> bool:
        """Match keyword jako celé slovo/frázi, ne substring.

        Separátory: začátek/konec řetězce, mezera, čárka, lomítko, středník, závorky.
        """
        pattern = r'(?:^|[\s,/;()])' + re.escape(keyword) + r'(?:[\s,/;()]|$)'
        return bool(re.search(pattern, text, re.IGNORECASE))

    def _detect_industry_mapping(self, industry_text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Detekuj kategorii (EN) a klíčová slova z Industry textu

        Vrací tuple: (category_en, keywords_found_en)
        - category_en: Finální kategorie (EN) z INDUSTRY_MAPPING
        - keywords_found_en: Čárkou oddělený seznam nalezených klíčových slov v angličtině

        Logika:
        - Projdi INDUSTRY_MAPPING od priority 1 (nejvyšší)
        - Hledej ANY klíčové slovo z kategorie v textu (word boundary match)
        - Vrať první shodu + seznam nalezených klíčových slov
        """
        if not industry_text:
            return None, None

        # Normalizuj vstup
        industry_text_lower = industry_text.lower().strip()

        # Projdi mapování podle priority (od 1 nahoru)
        for mapping in sorted(self.INDUSTRY_MAPPING, key=lambda x: x['priority']):
            category_en = mapping['category_en']
            keywords = mapping['keywords']

            # Check exclude keywords — if any match, skip this category
            exclude_keywords = mapping.get('exclude_keywords', [])
            if any(self._keyword_matches(kw, industry_text_lower) for kw in exclude_keywords):
                continue

            # Hledej klíčová slova v textu
            found_keywords_en = []

            for keyword_pl, keyword_en in keywords.items():
                if self._keyword_matches(keyword_pl, industry_text_lower):
                    found_keywords_en.append(keyword_en)

            # Pokud jsme našli nějaké klíčové slovo, vrať kategorii + slova
            if found_keywords_en:
                # Odeber duplikáty a seřaď
                found_keywords_en = sorted(set(found_keywords_en))
                keywords_str = ', '.join(found_keywords_en)
                return category_en, keywords_str

        # Pokud nic není nalezeno
        return None, None

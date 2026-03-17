import sqlite3
import re
import json
from pathlib import Path

# ============================================================================
# REGION MAPPING - English → Polish
# ============================================================================
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

# ============================================================================
# CURRENCY MAPPING - Detect → Standard code
# ============================================================================
CURRENCY_MAPPING = {
    '€': 'EUR',
    'EUR': 'EUR',
    'eur': 'EUR',
    'EURO': 'EUR',
    'Euro': 'EUR',
    'euro': 'EUR',
    'PLN': 'PLN',
    'pln': 'PLN',
    'zł': 'PLN',
    'ZŁ': 'PLN',
    'zl': 'PLN',
    'Kč': 'CZK',
    'kč': 'CZK',
    'CZK': 'CZK',
    'czk': 'CZK'
}

# ============================================================================
# WORK_MODE MAPPING - Individual mappings (regex-based)
# ============================================================================
WORK_MODE_MAPPING = [
    {
        'to_replace': 'praca mobilna',
        'replace_with': 'mobile work'
    },
    {
        'to_replace': 'praca hybrydowa',
        'replace_with': 'hybrid work'
    },
    {
        'to_replace': 'praca stacjonarna',
        'replace_with': 'full office work'
    },
    {
        'to_replace': 'praca zdalna',
        'replace_with': 'remote work'
    }
]

# ============================================================================
# EMPLOYMENT_TYPE MAPPING - Polish → English
# ============================================================================
EMPLOYMENT_TYPE_MAPPING = [
    # ========== ZÁKLADNÍ POLSKÉ TYPY ==========
    {
        'to_replace': 'umowa o pracę',
        'replace_with': 'employment contract'
    },
    {
        'to_replace': 'umowa zlecenie',
        'replace_with': 'Contract for services'
    },
    {
        'to_replace': 'umowa o dzieło',
        'replace_with': 'contract for specific work'
    },
    {
        'to_replace': 'kontrakt B2B',
        'replace_with': 'B2B contract'
    },
    {
        'to_replace': 'umowa agencyjna',
        'replace_with': 'agency agreement'
    },
    {
        'to_replace': 'umowa o pracę tymczasową',
        'replace_with': 'fixed-term contract'
    },
    {
        'to_replace': 'umowa na zastępstwo',
        'replace_with': 'substitution agreement'
    },
    {
        'to_replace': 'umowa o staż / praktyki',
        'replace_with': 'internship / apprenticeship contract'
    },

    # ========== JIŽ PŘELOŽENÉ (ANGLICKÉ TERMÍNY) ==========
    {
        'to_replace': 'contract of employment',
        'replace_with': 'employment contract'
    }
]

# ============================================================================
# INDUSTRY MAPPING - v2.4 Ultra Comprehensive
# ============================================================================
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

# ============================================================================
# POSITION_LEVELS MAPPING - Polish → English (standardized)
# ============================================================================
POSITION_LEVELS_MAPPING = [
    # ========== POLSKÉ VERZE ==========
    {
        'to_replace': 'praktykant / stażysta',
        'replace_with': 'trainee'
    },
    {
        'to_replace': 'asystent',
        'replace_with': 'assistant'
    },
    {
        'to_replace': 'młodszy specjalista (Junior)',
        'replace_with': 'junior specialist'
    },
    {
        'to_replace': 'specjalista (Mid / Regular)',
        'replace_with': 'specialist'
    },
    {
        'to_replace': 'starszy specjalista (Senior)',
        'replace_with': 'senior specialist'
    },
    {
        'to_replace': 'ekspert',
        'replace_with': 'expert'
    },
    {
        'to_replace': 'kierownik / koordynator',
        'replace_with': 'team manager'
    },
    {
        'to_replace': 'mened\u017cer"',
        'replace_with': 'manager'
    },

    {
        'to_replace': 'menedżer',
        'replace_with': 'manager'
    },
    {
        'to_replace': 'dyrektor',
        'replace_with': 'director'
    },
    {
        'to_replace': 'prezes',
        'replace_with': 'president'
    },
    {
        'to_replace': 'pracownik fizyczny',
        'replace_with': 'manual worker'
    },

    # ========== ANGLICKÉ VERZE (OPRAVY NA STANDARD) ==========
    {
        'to_replace': 'specialist (Mid / Regular)',
        'replace_with': 'specialist'
    },
    {
        'to_replace': 'senior specialist (Senior)',
        'replace_with': 'senior specialist'
    },
    {
        'to_replace': 'junior specialist (Junior)',
        'replace_with': 'junior specialist'
    },
    {
        'to_replace': 'manager / supervisor',
        'replace_with': 'manager'
    },
    {
        'to_replace': 'team manager',
        'replace_with': 'team manager'
    },
    {
        'to_replace': 'manager',
        'replace_with': 'manager'
    },
    {
        'to_replace': 'director',
        'replace_with': 'director'
    },
    {
        'to_replace': 'president',
        'replace_with': 'president'
    },
    {
        'to_replace': 'trainee',
        'replace_with': 'trainee'
    },
    {
        'to_replace': 'assistant',
        'replace_with': 'assistant'
    },
    {
        'to_replace': 'expert',
        'replace_with': 'expert'
    },
    {
        'to_replace': 'entry level & blue collar',
        'replace_with': 'manual worker'
    },
]

def detect_industry_mapping(industry_text):
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
    for mapping in sorted(INDUSTRY_MAPPING, key=lambda x: x['priority']):
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


def clean_industry_data(conn):
    """
    Vyčisti industry data - mapuj z Industry textu na mapped_industry a kw_industry
    """
    cursor = conn.cursor()

    print("\n" + "=" * 100)
    print("🏭 ČIŠTĚNÍ INDUSTRY DATA")
    print("=" * 100 + "\n")

    # ========== NEJDŘÍVE PŘIDEJ SLOUPCE POKUD NEEXISTUJÍ ==========
    print("📊 Kontrola a přidání sloupců...\n")

    try:
        # Zjisti aktuální sloupce
        cursor.execute("PRAGMA table_info(job_offers)")
        column_names = [col[1] for col in cursor.fetchall()]

        # Přidej mapped_industry pokud neexistuje
        if 'mapped_industry' not in column_names:
            print("   ➕ Přidávám sloupec: mapped_industry")
            cursor.execute('ALTER TABLE job_offers ADD COLUMN mapped_industry TEXT DEFAULT NULL')
            conn.commit()
            print("      ✅ OK")

        # Přidej kw_industry pokud neexistuje
        if 'kw_industry' not in column_names:
            print("   ➕ Přidávám sloupec: kw_industry")
            cursor.execute('ALTER TABLE job_offers ADD COLUMN kw_industry TEXT DEFAULT NULL')
            conn.commit()
            print("      ✅ OK")

        print("\n✅ Sloupce jsou připraveny\n")

    except sqlite3.OperationalError as e:
        print(f"   ⚠️  SQLite chyba: {e}")
        print("   (Sloupce pravděpodobně již existují)\n")
        conn.rollback()

    # ========== NYNÍ MAPUJ INDUSTRY ==========

    # Najdi řádky s NULL mapped_industry
    cursor.execute('''
                   SELECT partition_id, company, url, industry
                   FROM job_offers
                   WHERE mapped_industry IS NULL
                     AND industry IS NOT NULL
                   ''')

    rows = cursor.fetchall()

    if not rows:
        print("✅ Žádné řádky k updatu (všechny mají mapped_industry)\n")
        return 0

    print(f"📌 Nalezeno {len(rows)} řádků s NULL mapped_industry\n")
    print("📊 MAPOVÁNÍ INDUSTRY INFORMACÍ...\n")

    updates_data = []
    unmapped_count = 0

    for partition_id, company, url, industry in rows:
        category_en, keywords_en = detect_industry_mapping(industry)

        if category_en is not None:
            updates_data.append({
                'partition_id': partition_id,
                'company': company,
                'url': url,
                'industry': industry,
                'mapped_industry': category_en,
                'kw_industry': keywords_en
            })
        else:
            unmapped_count += 1

    if not updates_data:
        print(f"❌ Žádné industry informace nebyly mapovány (Unmapped: {unmapped_count})\n")
        return 0

    # Statistika mapovaných kategorií
    category_counts = {}
    for data in updates_data:
        cat = data['mapped_industry']
        category_counts[cat] = category_counts.get(cat, 0) + 1

    print("=" * 100)
    print("📈 VÝSLEDKY ANALÝZY - INDUSTRY")
    print("=" * 100)
    print(f"✅ Nalezeno {len(updates_data)} řádků k mapování:")
    print(f"   • Mapováno:        {len(updates_data)} řádků")
    print(f"   • Nenamapováno:    {unmapped_count} řádků\n")
    print(f"   📊 DISTRIBUCE KATEGORIÍ:\n")

    for cat in sorted(category_counts.keys()):
        count = category_counts[cat]
        print(f"      • {cat:35} {count:,} řádků")

    print(f"\n   Celkem k updatu: {len(updates_data)} řádků\n")

    # Potvrzení
    print("=" * 100)
    user_input = input("👉 POKRAČOVAT V UPDATU INDUSTRY? (y/n): ").strip().lower()
    print("=" * 100 + "\n")

    if user_input != 'y':
        print("❌ Industry update zrušen\n")
        return 0

    # Update DB
    print("💾 UPDATUJU INDUSTRY DATA...\n")

    updated_count = 0
    for data in updates_data:
        cursor.execute('''
                       UPDATE job_offers
                       SET mapped_industry = ?,
                           kw_industry     = ?
                       WHERE partition_id = ?
                       ''', (data['mapped_industry'], data['kw_industry'], data['partition_id']))

        updated_count += 1

    conn.commit()

    print(f"✅ Aktualizováno {updated_count} řádků\n")

    # Zobraz příklady
    print("=" * 100)
    print("📋 PRVNÍCH 15 PŘÍKLADŮ - INDUSTRY UPDATE")
    print("=" * 100 + "\n")

    for i, data in enumerate(updates_data[:15], 1):
        print(f"[{i}] Company: {data['company'][:50]}")
        print(f"    URL: {data['url']}")
        print(f"    Original Industry: {data['industry'][:70]}")
        print(f"    Mapped Category: {data['mapped_industry']}")
        print(f"    Keywords Found: {data['kw_industry']}\n")

    return updated_count


def extract_salary_and_currency_from_we_offer(we_offer_text):
    """
    Extrahuj salary hodnoty + měnu z we_offer textu
    Vrací tuple: (salary_min, salary_max, salary_currency)
    - Pokud jsou 2+ čísla → nižší=min, vyšší=max
    - Pokud je jedno číslo → to je min, max=None
    - Měna se detekuje z prvního výskytu
    """
    pattern = r'(\d{3,})\s*(?:(€|EUR|eur|EURO|Euro|euro|PLN|pln|zł|ZŁ|zl|Kč|kč|CZK|czk))'

    matches = re.findall(pattern, we_offer_text)

    if not matches:
        return None, None, None

    # Extrahuj salaries a měnu
    salaries = []
    detected_currency = None

    for salary_str, currency_str in matches:
        salaries.append(int(salary_str))

        # Vezmi první detekovanou měnu
        if detected_currency is None and currency_str:
            detected_currency = CURRENCY_MAPPING.get(currency_str, currency_str)

    # Seřaď a odebrat duplikáty
    salaries = sorted(set(salaries))

    if len(salaries) >= 2:
        salary_min, salary_max = salaries[0], salaries[-1]
    elif len(salaries) == 1:
        salary_min, salary_max = salaries[0], None
    else:
        return None, None, None

    return salary_min, salary_max, detected_currency


def translate_work_modes(work_modes_text):
    """
    Přelož work_modes z polštiny do angličtiny (regex-based)

    Vstup:  ["praca zdalna", "praca hybrydowa"]
    Výstup: ["remote work", "hybrid work"]

    Princip:
    - Parsuj JSON seznam
    - Pro každý prvek v seznamu hledej matchy v WORK_MODE_MAPPING
    - Nahraď individuálně
    - Vrať nový seznam jako JSON
    """
    if not work_modes_text:
        return None

    try:
        # Parsuj JSON seznam
        work_modes_list = json.loads(work_modes_text)

    except (ValueError, TypeError) as e:
        # Pokud to není valid JSON, vrať original
        print(f"⚠️  Chyba při parsování JSON: {e}")
        print(f"   Original text: {work_modes_text}")
        return work_modes_text

    try:
        if not isinstance(work_modes_list, list):
            return work_modes_text

        # Transluj každý prvek
        translated_list = []

        for mode in work_modes_list:
            translated = mode

            # Hledej v mapping tabulce
            for mapping_rule in WORK_MODE_MAPPING:
                # Case-insensitive porovnání
                if mode.lower().strip() == mapping_rule['to_replace'].lower().strip():
                    translated = mapping_rule['replace_with']
                    break

            translated_list.append(translated)

        # Vrať jako JSON, jen pokud se něco změnilo
        result = json.dumps(translated_list)

        return result if result != work_modes_text else work_modes_text

    except (AttributeError, TypeError) as e:
        # Pokud je něco špatně se zpracováním
        print(f"⚠️  Chyba při translaci: {e}")
        print(f"   Original text: {work_modes_text}")
        return work_modes_text


def translate_position_levels(position_levels_text):
    """
    Přelož position_levels z polštiny do angličtiny (regex-based)

    Vstup:  '["specjalista (Mid / Regular)", "starszy specjalista (Senior)"]'
    Výstup: '["specialist", "senior specialist"]'

    Princip:
    - Parsuj JSON seznam
    - Pro každý prvek hledej matchy v POSITION_LEVELS_MAPPING
    - Nahraď individuálně
    - Vrať nový seznam jako JSON
    """
    if not position_levels_text:
        return None

    try:
        # Parsuj JSON seznam
        position_levels_list = json.loads(position_levels_text)

    except (ValueError, TypeError) as e:
        # Pokud to není valid JSON, vrať original
        print(f"⚠️  Chyba při parsování JSON position_levels: {e}")
        print(f"   Original text: {position_levels_text}")
        return position_levels_text

    try:
        if not isinstance(position_levels_list, list):
            return position_levels_text

        # Transluj každý prvek
        translated_list = []

        for level in position_levels_list:
            if not level:
                continue

            translated = level

            # Hledej v mapping tabulce
            for mapping_rule in POSITION_LEVELS_MAPPING:
                # Case-insensitive porovnání
                if level.lower().strip() == mapping_rule['to_replace'].lower().strip():
                    translated = mapping_rule['replace_with']
                    break

            translated_list.append(translated)

        # Vrať jako JSON
        result = json.dumps(translated_list)

        return result if result != position_levels_text else position_levels_text

    except (AttributeError, TypeError) as e:
        # Pokud je něco špatně se zpracováním
        print(f"⚠️  Chyba při translaci position_levels: {e}")
        print(f"   Original text: {position_levels_text}")
        return position_levels_text


def translate_employment_types(employment_type_text):
    """
    Přelož employment_type z polštiny do angličtiny (regex-based)

    Vstup:  "umowa o pracę, umowa zlecenie, kontrakt B2B"
    Výstup: "employment contract, contract of mandate, B2B contract"

    Princip:
    - Parsuj seznam oddělený čárkami
    - Pro každý prvek hledej matchy v EMPLOYMENT_TYPE_MAPPING
    - Nahraď individuálně
    - Vrať nový seznam oddělený čárkami
    """
    if not employment_type_text:
        return None

    try:
        # Parsuj seznam oddělený čárkami
        employment_types_list = [item.strip() for item in employment_type_text.split(',')]

        if not employment_types_list or all(item == '' for item in employment_types_list):
            return employment_type_text

        # Transluj každý prvek
        translated_list = []

        for emp_type in employment_types_list:
            if not emp_type:
                continue

            translated = emp_type

            # Hledej v mapping tabulce
            for mapping_rule in EMPLOYMENT_TYPE_MAPPING:
                # Case-insensitive porovnání
                if emp_type.lower().strip() == mapping_rule['to_replace'].lower().strip():
                    translated = mapping_rule['replace_with']
                    break

            translated_list.append(translated)

        # Vrať jako string oddělený čárkami
        result = ', '.join(translated_list)

        return result if result != employment_type_text else employment_type_text

    except (AttributeError, TypeError) as e:
        # Pokud je něco špatně se zpracováním
        return employment_type_text


def clean_salary_data(conn):
    """
    Vyčisti NULL salary_min/salary_max/salary_currency pomocí regex z we_offer
    """
    cursor = conn.cursor()

    print("\n" + "=" * 100)
    print("💰 ČIŠTĚNÍ SALARY DATA")
    print("=" * 100 + "\n")

    # Najdi řádky kde salary_min IS NULL
    cursor.execute('''
                   SELECT partition_id, company, url, we_offer
                   FROM job_offers
                   WHERE salary_min IS NULL
                     AND we_offer IS NOT NULL
                   ''')

    rows = cursor.fetchall()

    if not rows:
        print("✅ Žádné řádky k updatu (všechny mají salary_min)\n")
        return 0

    print(f"📌 Nalezeno {len(rows)} řádků s NULL salary_min\n")
    print("📊 EXTRAHOVÁNÍ SALARY INFORMACÍ...\n")

    updates_data = []

    for partition_id, company, url, we_offer in rows:
        salary_min, salary_max, salary_currency = extract_salary_and_currency_from_we_offer(we_offer)

        if salary_min is not None:
            updates_data.append({
                'partition_id': partition_id,
                'company': company,
                'url': url,
                'we_offer': we_offer,
                'salary_min': salary_min,
                'salary_max': salary_max,
                'salary_currency': salary_currency
            })

    if not updates_data:
        print("❌ Žádné salary informace nebyly nalezeny v textech\n")
        return 0

    # Statistika
    with_range = sum(1 for d in updates_data if d['salary_max'] is not None)
    single_values = sum(1 for d in updates_data if d['salary_max'] is None)

    # Currency stats
    currency_counts = {}
    for data in updates_data:
        curr = data['salary_currency'] or 'UNKNOWN'
        currency_counts[curr] = currency_counts.get(curr, 0) + 1

    print("=" * 100)
    print("📈 VÝSLEDKY ANALÝZY - SALARY")
    print("=" * 100)
    print(f"✅ Nalezeno {len(updates_data)} řádků se salary informacemi:")
    print(f"   • S range (min-max):     {with_range} řádků")
    print(f"   • S jedinou hodnotou:    {single_values} řádků")
    print(f"\n   💵 Měny:")
    for curr, count in sorted(currency_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"      • {curr:10} {count:,} řádků")
    print(f"\n   Celkem k updatu: {len(updates_data)} řádků\n")

    # Potvrzení
    print("=" * 100)
    user_input = input("👉 POKRAČOVAT V UPDATU SALARY? (y/n): ").strip().lower()
    print("=" * 100 + "\n")

    if user_input != 'y':
        print("❌ Salary update zrušen\n")
        return 0

    # Update DB
    print("💾 UPDATUJU SALARY DATA...\n")

    updated_count = 0
    for data in updates_data:
        cursor.execute('''
                       UPDATE job_offers
                       SET salary_min      = ?,
                           salary_max      = ?,
                           salary_currency = ?
                       WHERE partition_id = ?
                       ''', (data['salary_min'], data['salary_max'], data['salary_currency'], data['partition_id']))

        updated_count += 1

    conn.commit()

    print(f"✅ Aktualizováno {updated_count} řádků\n")

    # Zobraz příklady
    print("=" * 100)
    print("📋 PRVNÍCH 10 PŘÍKLADŮ - SALARY UPDATE")
    print("=" * 100 + "\n")

    for i, data in enumerate(updates_data[:10], 1):
        salary_display = (
            f"{data['salary_min']:,} - {data['salary_max']:,}"
            if data['salary_max']
            else f"{data['salary_min']:,}"
        )

        currency_display = data['salary_currency'] or 'N/A'

        print(f"[{i}] Company: {data['company'][:50]}")
        print(f"    URL: {data['url']}")
        print(f"    Salary: {salary_display} {currency_display}")
        print(f"    salary_min: {data['salary_min']:,} | salary_max: {data['salary_max']}")
        print(f"    salary_currency: {currency_display}")
        print(f"    From text: {data['we_offer'][:90]}...\n")

    return updated_count


def clean_region_data(conn):
    """
    Vyčisti region data - přelož z angličtiny do polštiny
    """
    cursor = conn.cursor()

    print("\n" + "=" * 100)
    print("🌍 ČIŠTĚNÍ REGION DATA")
    print("=" * 100 + "\n")

    # Zjisti kolik řádků má každý anglický region
    region_stats = {}

    for english_name, polish_name in REGION_MAPPING.items():
        cursor.execute(
            'SELECT COUNT(*) FROM job_offers WHERE region = ?',
            (english_name,)
        )
        count = cursor.fetchone()[0]

        if count > 0:
            region_stats[english_name] = {
                'polish_name': polish_name,
                'count': count
            }

    if not region_stats:
        print("✅ Žádné anglické názvy regionů k překladu\n")
        return 0

    # Zobraz statistiku
    print("📊 NALEZENÉ ANGLICKÉ NÁZVY REGIONŮ:\n")

    total_to_update = 0
    for english_name, data in sorted(region_stats.items(), key=lambda x: x[1]['count'], reverse=True):
        print(f"   {english_name:30} → {data['polish_name']:25} ({data['count']:,} řádků)")
        total_to_update += data['count']

    print(f"\n   Celkem k updatu: {total_to_update:,} řádků\n")

    # Potvrzení
    print("=" * 100)
    user_input = input("👉 POKRAČOVAT V UPDATU REGIONŮ? (y/n): ").strip().lower()
    print("=" * 100 + "\n")

    if user_input != 'y':
        print("❌ Region update zrušen\n")
        return 0

    # Update DB
    print("💾 UPDATUJU REGION DATA...\n")

    updated_count = 0
    for english_name, data in region_stats.items():
        cursor.execute('''
                       UPDATE job_offers
                       SET region = ?
                       WHERE region = ?
                       ''', (data['polish_name'], english_name))

        updated_count += cursor.rowcount

    conn.commit()

    print(f"✅ Aktualizováno {updated_count:,} řádků\n")

    # Zobraz příklady po updatu
    print("=" * 100)
    print("📋 PRVNÍCH 10 PŘÍKLADŮ - REGION UPDATE")
    print("=" * 100 + "\n")

    cursor.execute('''
        SELECT partition_id, company, url, region 
        FROM job_offers 
        WHERE region IN ({})
        LIMIT 10
    '''.format(','.join('?' * len(REGION_MAPPING.values()))),
                   tuple(REGION_MAPPING.values()))

    examples = cursor.fetchall()

    for i, (partition_id, company, url, region) in enumerate(examples, 1):
        print(f"[{i}] ID: {partition_id}")
        print(f"    Company: {company[:50]}")
        print(f"    Region: {region}")
        print(f"    URL: {url}\n")

    return updated_count


def clean_work_modes_data(conn):
    """
    Vyčisti work_modes data - přelož z polštiny do angličtiny (regex-based)
    Transluje INDIVIDUÁLNÍ prvky seznamu místo matchování celých seznamů
    """
    cursor = conn.cursor()

    print("\n" + "=" * 100)
    print("🏢 ČIŠTĚNÍ WORK_MODES DATA")
    print("=" * 100 + "\n")

    # Najdi všechny řádky s work_modes
    cursor.execute('''
        SELECT partition_id, company, url, work_modes
        FROM job_offers 
        WHERE work_modes IS NOT NULL
    ''')

    rows = cursor.fetchall()

    if not rows:
        print("✅ Žádné řádky s work_modes k translaci\n")
        return 0

    print(f"📌 Nalezeno {len(rows)} řádků s work_modes\n")
    print("📊 TRANSLACE WORK_MODES INFORMACÍ...\n")

    updates_data = []
    unchanged_count = 0

    for partition_id, company, url, work_modes in rows:
        translated_work_modes = translate_work_modes(work_modes)

        # Pokud se změnilo, přidej do updates
        if translated_work_modes != work_modes:
            updates_data.append({
                'partition_id': partition_id,
                'company': company,
                'url': url,
                'original_work_modes': work_modes,
                'translated_work_modes': translated_work_modes
            })
        else:
            unchanged_count += 1

    if not updates_data:
        print(f"✅ Všech {unchanged_count} řádků jsou již v angličtině\n")
        return 0

    print("=" * 100)
    print("📈 VÝSLEDKY ANALÝZY - WORK_MODES")
    print("=" * 100)
    print(f"✅ Nalezeno {len(updates_data)} řádků k translaci:")
    print(f"   • K překladu:             {len(updates_data)} řádků")
    print(f"   • Už v angličtině:        {unchanged_count} řádků")
    print(f"\n   Celkem k updatu: {len(updates_data)} řádků\n")

    # Potvrzení
    print("=" * 100)
    user_input = input("👉 POKRAČOVAT V UPDATU WORK_MODES? (y/n): ").strip().lower()
    print("=" * 100 + "\n")

    if user_input != 'y':
        print("❌ Work_modes update zrušen\n")
        return 0

    # Update DB
    print("💾 UPDATUJU WORK_MODES DATA...\n")

    updated_count = 0
    for data in updates_data:
        cursor.execute('''
            UPDATE job_offers
            SET work_modes = ?
            WHERE partition_id = ?
        ''', (data['translated_work_modes'], data['partition_id']))

        updated_count += 1

    conn.commit()

    print(f"✅ Aktualizováno {updated_count} řádků\n")

    # Zobraz příklady
    print("=" * 100)
    print("📋 PRVNÍCH 10 PŘÍKLADŮ - WORK_MODES UPDATE")
    print("=" * 100 + "\n")

    for i, data in enumerate(updates_data[:10], 1):
        print(f"[{i}] Company: {data['company'][:50]}")
        print(f"    URL: {data['url']}")
        print(f"    PŘED:  {data['original_work_modes']}")
        print(f"    PO:    {data['translated_work_modes']}\n")

    return updated_count


def clean_employment_type_data(conn):
    """
    Vyčisti employment_type data - přelož z polštiny do angličtiny (regex-based)
    Transluje INDIVIDUÁLNÍ prvky seznamu místo matchování celých seznamů
    """
    cursor = conn.cursor()

    print("\n" + "=" * 100)
    print("📄 ČIŠTĚNÍ EMPLOYMENT_TYPE DATA")
    print("=" * 100 + "\n")

    # Najdi všechny řádky s employment_type
    cursor.execute('''
        SELECT partition_id, company, url, employment_type
        FROM job_offers 
        WHERE employment_type IS NOT NULL
    ''')

    rows = cursor.fetchall()

    if not rows:
        print("✅ Žádné řádky s employment_type k translaci\n")
        return 0

    print(f"📌 Nalezeno {len(rows)} řádků s employment_type\n")
    print("📊 TRANSLACE EMPLOYMENT_TYPE INFORMACÍ...\n")

    updates_data = []
    unchanged_count = 0

    for partition_id, company, url, employment_type in rows:
        translated_employment_type = translate_employment_types(employment_type)

        # Pokud se změnilo, přidej do updates
        if translated_employment_type != employment_type:
            updates_data.append({
                'partition_id': partition_id,
                'company': company,
                'url': url,
                'original_employment_type': employment_type,
                'translated_employment_type': translated_employment_type
            })
        else:
            unchanged_count += 1

    if not updates_data:
        print(f"✅ Všech {unchanged_count} řádků jsou již v angličtině\n")
        return 0

    print("=" * 100)
    print("📈 VÝSLEDKY ANALÝZY - EMPLOYMENT_TYPE")
    print("=" * 100)
    print(f"✅ Nalezeno {len(updates_data)} řádků k translaci:")
    print(f"   • K překladu:             {len(updates_data)} řádků")
    print(f"   • Už v angličtině:        {unchanged_count} řádků")
    print(f"\n   Celkem k updatu: {len(updates_data)} řádků\n")

    # Potvrzení
    print("=" * 100)
    user_input = input("👉 POKRAČOVAT V UPDATU EMPLOYMENT_TYPE? (y/n): ").strip().lower()
    print("=" * 100 + "\n")

    if user_input != 'y':
        print("❌ Employment_type update zrušen\n")
        return 0

    # Update DB
    print("💾 UPDATUJU EMPLOYMENT_TYPE DATA...\n")

    updated_count = 0
    for data in updates_data:
        cursor.execute('''
            UPDATE job_offers
            SET employment_type = ?
            WHERE partition_id = ?
        ''', (data['translated_employment_type'], data['partition_id']))

        updated_count += 1

    conn.commit()

    print(f"✅ Aktualizováno {updated_count} řádků\n")

    # Zobraz příklady
    print("=" * 100)
    print("📋 PRVNÍCH 10 PŘÍKLADŮ - EMPLOYMENT_TYPE UPDATE")
    print("=" * 100 + "\n")

    for i, data in enumerate(updates_data[:10], 1):
        print(f"[{i}] Company: {data['company'][:50]}")
        print(f"    URL: {data['url']}")
        print(f"    PŘED:  {data['original_employment_type']}")
        print(f"    PO:    {data['translated_employment_type']}\n")

    return updated_count


def clean_position_levels_data(conn):
    """
    Vyčisti position_levels data - přelož z polštiny do angličtiny a standardizuj anglické verze
    Transluje INDIVIDUÁLNÍ prvky seznamu (JSON)
    """
    cursor = conn.cursor()

    print("\n" + "=" * 100)
    print("📊 ČIŠTĚNÍ POSITION_LEVELS DATA")
    print("=" * 100 + "\n")

    # Najdi všechny řádky s position_levels
    cursor.execute('''
                   SELECT partition_id, company, url, position_levels
                   FROM job_offers
                   WHERE position_levels IS NOT NULL
                   ''')

    rows = cursor.fetchall()

    if not rows:
        print("✅ Žádné řádky s position_levels k translaci\n")
        return 0

    print(f"📌 Nalezeno {len(rows)} řádků s position_levels\n")
    print("📊 TRANSLACE POSITION_LEVELS INFORMACÍ...\n")

    updates_data = []
    unchanged_count = 0

    for partition_id, company, url, position_levels in rows:
        translated_position_levels = translate_position_levels(position_levels)

        # Pokud se změnilo, přidej do updates
        if translated_position_levels != position_levels:
            updates_data.append({
                'partition_id': partition_id,
                'company': company,
                'url': url,
                'original_position_levels': position_levels,
                'translated_position_levels': translated_position_levels
            })
        else:
            unchanged_count += 1

    if not updates_data:
        print(f"✅ Všech {unchanged_count} řádků jsou již v angličtině / standardizovány\n")
        return 0

    # Statistika - jaké levely se vyskytují
    levels_stats = {}
    for data in updates_data:
        try:
            levels = json.loads(data['translated_position_levels'])
            for level in levels:
                levels_stats[level] = levels_stats.get(level, 0) + 1
        except:
            pass

    print("=" * 100)
    print("📈 VÝSLEDKY ANALÝZY - POSITION_LEVELS")
    print("=" * 100)
    print(f"✅ Nalezeno {len(updates_data)} řádků k translaci:")
    print(f"   • K překladu/opravě:      {len(updates_data)} řádků")
    print(f"   • Už OK:                  {unchanged_count} řádků")
    print(f"\n   📋 STANDARDIZOVANÉ LEVELY:\n")

    for level in sorted(levels_stats.keys()):
        count = levels_stats[level]
        print(f"      • {level:30} {count:,} výskytů")

    print(f"\n   Celkem k updatu: {len(updates_data)} řádků\n")

    # Potvrzení
    print("=" * 100)
    user_input = input("👉 POKRAČOVAT V UPDATU POSITION_LEVELS? (y/n): ").strip().lower()
    print("=" * 100 + "\n")

    if user_input != 'y':
        print("❌ Position_levels update zrušen\n")
        return 0

    # Update DB
    print("💾 UPDATUJU POSITION_LEVELS DATA...\n")

    updated_count = 0
    for data in updates_data:
        cursor.execute('''
                       UPDATE job_offers
                       SET position_levels = ?
                       WHERE partition_id = ?
                       ''', (data['translated_position_levels'], data['partition_id']))

        updated_count += 1

    conn.commit()

    print(f"✅ Aktualizováno {updated_count} řádků\n")

    # Zobraz příklady
    print("=" * 100)
    print("📋 PRVNÍCH 15 PŘÍKLADŮ - POSITION_LEVELS UPDATE")
    print("=" * 100 + "\n")

    for i, data in enumerate(updates_data[:15], 1):
        print(f"[{i}] Company: {data['company'][:50]}")
        print(f"    URL: {data['url']}")
        print(f"    PŘED:  {data['original_position_levels']}")
        print(f"    PO:    {data['translated_position_levels']}\n")

    return updated_count


def main():
    db_path = Path('job_database.db')

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)

        print("\n" + "=" * 100)
        print("🧹 DATABASE CLEANER - JOB OFFERS")
        print("=" * 100)

        # KROK 1: Vyčisti salary data
        salary_updated = clean_salary_data(conn)

        # KROK 2: Vyčisti region data
        region_updated = clean_region_data(conn)

        # KROK 3: Vyčisti work_modes data
        work_modes_updated = clean_work_modes_data(conn)

        # KROK 4: Vyčisti employment_type data
        employment_type_updated = clean_employment_type_data(conn)

        # KROK 5: Vyčisti position_levels data
        position_levels_updated = clean_position_levels_data(conn)

        # KROK 6: Vyčisti industry data
        industry_updated = clean_industry_data(conn)

        conn.close()

        # Final summary
        print("\n" + "=" * 100)
        print("🎉 ČIŠTĚNÍ DOKONČENO")
        print("=" * 100)
        print(f"✅ Salary updates:         {salary_updated:,} řádků")
        print(f"✅ Region updates:         {region_updated:,} řádků")
        print(f"✅ Work_modes updates:     {work_modes_updated:,} řádků")
        print(f"✅ Employment_type updates: {employment_type_updated:,} řádků")
        print(f"✅ Position_levels updates: {position_levels_updated:,} řádků")
        print(f"✅ Industry updates:       {industry_updated:,} řádků")
        print(f"✅ Total updates:          {salary_updated + region_updated + work_modes_updated + employment_type_updated + position_levels_updated + industry_updated:,} řádků")
        print("=" * 100 + "\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
"""
def main():
    db_path = Path('job_database.db')

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)

        print("\n" + "=" * 100)
        print("🧹 DATABASE CLEANER - JOB OFFERS")
        print("=" * 100)

        # KROK 1: Vyčisti salary data
        salary_updated = clean_salary_data(conn)

        # KROK 2: Vyčisti region data
        region_updated = clean_region_data(conn)

        # KROK 3: Vyčisti work_modes data
        work_modes_updated = clean_work_modes_data(conn)

        # KROK 4: Vyčisti employment_type data
        employment_type_updated = clean_employment_type_data(conn)

        # KROK 5: Vyčisti industry data (PŘIDÁ SLOUPCE SAMO)
        industry_updated = clean_industry_data(conn)

        conn.close()

        # Final summary
        print("\n" + "=" * 100)
        print("🎉 ČIŠTĚNÍ DOKONČENO")
        print("=" * 100)
        print(f"✅ Salary updates:         {salary_updated:,} řádků")
        print(f"✅ Region updates:         {region_updated:,} řádků")
        print(f"✅ Work_modes updates:     {work_modes_updated:,} řádků")
        print(f"✅ Employment_type updates: {employment_type_updated:,} řádků")
        print(f"✅ Industry updates:       {industry_updated:,} řádků")
        print(f"✅ Total updates:          {salary_updated + region_updated + work_modes_updated + employment_type_updated + industry_updated:,} řádků")
        print("=" * 100 + "\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()



if __name__ == "__main__":
    main()
"""


import cloudscraper
from bs4 import BeautifulSoup
import json
import pandas as pd
import time
import os
from pathlib import Path


def extract_job_detail(url):
    """
    Extrahuje detail jedné nabídky
    """
    scraper = cloudscraper.create_scraper()

    job_data = {
        'url': url,
        'pozice': None,
        'firma': None,
        'odvetvi': None,
        'typ_smlouvy': None,
        'plat_min': None,
        'plat_max': None,
        'mena': None,
        'mesto': None,
        'region': None,
        'zkusenost': None,
        'ukoly': None,
        'benefity': None,
        'datum_zverejneni': None,
        'platnost_do': None,
        'uroven_pozice': None,
        'uvazek': None,
        'mod_prace': None,
        'pozadovane_technologie': None,
        'vitane_technologie': None,
        'popis_prace': None,
        'pozadavky': None,
        'co_nabizime': None,
        'chyba': None
    }

    try:
        print(f"\n🔍 Stahuji: {url}")
        response = scraper.get(url, timeout=30)
        response.raise_for_status()

        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        # --- 1. JSON-LD (základní info) ---
        json_ld_script = soup.find('script', {'type': 'application/ld+json', 'id': 'job-schema-org'})

        if json_ld_script:
            job_json_ld = json.loads(json_ld_script.string)

            job_data['pozice'] = job_json_ld.get('title')

            # Firma
            hiring_org = job_json_ld.get('hiringOrganization', {})
            if isinstance(hiring_org, dict):
                job_data['firma'] = hiring_org.get('name')
            else:
                job_data['firma'] = hiring_org

            job_data['odvetvi'] = job_json_ld.get('industry')
            job_data['typ_smlouvy'] = job_json_ld.get('employmentType')

            # Plat
            salary = job_json_ld.get('baseSalary', {})
            if salary:
                job_data['plat_min'] = salary.get('minValue')
                job_data['plat_max'] = salary.get('maxValue')
                job_data['mena'] = salary.get('currency')

            # Lokace
            location = job_json_ld.get('jobLocation', {})
            job_data['mesto'] = location.get('name')

            address = location.get('address', {})
            job_data['region'] = address.get('addressRegion')

            job_data['zkusenost'] = job_json_ld.get('experienceRequirements')
            job_data['ukoly'] = job_json_ld.get('responsibilities')
            job_data['benefity'] = job_json_ld.get('jobBenefits')
            job_data['datum_zverejneni'] = job_json_ld.get('datePosted')
            job_data['platnost_do'] = job_json_ld.get('validThrough')

            print("✅ JSON-LD přečten")
        else:
            job_data['chyba'] = 'JSON-LD nenalezen'
            print("⚠️ JSON-LD nenalezen")
            return job_data

        # --- 2. NEXT_DATA (technologie, požadavky) ---
        next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})

        if next_data_script:
            try:
                next_data = json.loads(next_data_script.string)

                # Úroveň pozice
                try:
                    position_levels = \
                    next_data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']['attributes'][
                        'employment']['positionLevels']
                    if position_levels:
                        job_data['uroven_pozice'] = ', '.join([level.get('name') for level in position_levels])
                except (KeyError, IndexError, TypeError):
                    pass

                # Úvazek
                try:
                    work_schedule = \
                    next_data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']['attributes'][
                        'employment']['workSchedules']
                    if work_schedule:
                        job_data['uvazek'] = ', '.join([ws.get('name') for ws in work_schedule])
                except (KeyError, IndexError, TypeError):
                    pass

                # Mód práce
                try:
                    work_modes = \
                    next_data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']['attributes'][
                        'employment']['workModes']
                    if work_modes:
                        job_data['mod_prace'] = ', '.join([mode.get('name') for mode in work_modes])
                except (KeyError, IndexError, TypeError):
                    pass

                # Text sekce (technologie, požadavky, atd)
                try:
                    text_sections = next_data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data'][
                        'textSections']

                    for section in text_sections:
                        section_type = section.get('sectionType')

                        if section_type == 'technologies-expected':
                            techs = section.get('textElements', [])
                            job_data['pozadovane_technologie'] = ', '.join(techs)

                        elif section_type == 'technologies-optional':
                            techs = section.get('textElements', [])
                            job_data['vitane_technologie'] = ', '.join(techs)

                        elif section_type == 'job-description':
                            plaintext = section.get('plainText', '')
                            job_data['popis_prace'] = plaintext[:500] if plaintext else None

                        elif section_type == 'requirements':
                            reqs = section.get('textElements', [])
                            job_data['pozadavky'] = ', '.join(reqs)

                        elif section_type == 'offered':
                            offers = section.get('textElements', [])
                            job_data['co_nabizime'] = ', '.join(offers)

                except (KeyError, IndexError, TypeError):
                    pass

                print("✅ NEXT_DATA přečten")

            except json.JSONDecodeError as e:
                job_data['chyba'] = f'JSON decode error: {e}'
                print(f"⚠️ NEXT_DATA parse chyba: {e}")
        else:
            print("⚠️ NEXT_DATA nenalezen")

    except Exception as e:
        job_data['chyba'] = str(e)
        print(f"❌ Chyba: {e}")

    return job_data


def test_first_3_urls():
    """
    Testuje prvních 3 URL z job_urls.json
    """

    print(f"\n{'=' * 70}")
    print("TEST SCRAPINGU - PRVNÍCH 3 URL")
    print(f"{'=' * 70}\n")

    # --- NAJDI SPRÁVNÝ ADRESÁŘ ---
    script_dir = Path(__file__).parent.absolute()
    print(f"Script dir: {script_dir}\n")

    # Zkus více možností
    possible_paths = [
        script_dir / 'job_urls.json',
        Path.cwd() / 'job_urls.json',
        Path.cwd() / 'Pracuj' / 'job_urls.json',
        Path('/Users/jirkapirka/PycharmProjects/Portfolio/Pracuj/job_urls.json')
    ]

    json_path = None
    for path in possible_paths:
        if path.exists():
            json_path = path
            print(f"✅ Nalezeno: {json_path}\n")
            break

    if not json_path:
        print("❌ job_urls.json nenalezen na těchto cestách:")
        for p in possible_paths:
            print(f"   - {p}")
        return

    # Načti URL
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            urls = json.load(f)
    except Exception as e:
        print(f"❌ Chyba při čtení: {e}")
        return

    if not urls:
        print("❌ Žádné URL v job_urls.json!")
        return

    # Vezmi prvních 3
    test_urls = urls[:3]
    print(f"Testuju: {len(test_urls)} URL\n")

    all_jobs = []

    for i, url in enumerate(test_urls, 1):
        print(f"\n{'-' * 70}")
        print(f"URL {i}/3")
        print(f"{'-' * 70}")

        job = extract_job_detail(url)
        all_jobs.append(job)

        # Zobraz výsledek
        print(f"\n📋 EXTRAHOVANÁ DATA:")
        print(f"  Pozice: {job['pozice']}")
        print(f"  Firma: {job['firma']}")
        print(f"  Plat: {job['plat_min']}-{job['plat_max']} {job['mena']}")
        print(f"  Město: {job['mesto']}")
        print(f"  Úroveň: {job['uroven_pozice']}")
        print(f"  Úvazek: {job['uvazek']}")
        print(f"  Mód: {job['mod_prace']}")
        print(f"  Vyž. technologie: {job['pozadovane_technologie']}")
        if job['chyba']:
            print(f"  ⚠️ Chyba: {job['chyba']}")

        # Pauza mezi requesty
        if i < len(test_urls):
            time.sleep(2)

    # --- EXPORT DO FORMÁTŮ ---
    print(f"\n\n{'=' * 70}")
    print("EXPORT DAT")
    print(f"{'=' * 70}\n")

    df = pd.DataFrame(all_jobs)

    output_dir = script_dir

    # CSV
    csv_file = output_dir / 'jobs_test.csv'
    df.to_csv(csv_file, index=False, encoding='utf-8')
    print(f"✅ Uloženo: {csv_file}")

    # JSON
    json_file = output_dir / 'jobs_test.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_jobs, f, indent=2, ensure_ascii=False)
    print(f"✅ Uloženo: {json_file}")

    # Excel
    excel_file = output_dir / 'jobs_test.xlsx'
    df.to_excel(excel_file, index=False, engine='openpyxl')
    print(f"✅ Uloženo: {excel_file}")

    # Parquet
    parquet_file = output_dir / 'jobs_test.parquet'
    df.to_parquet(parquet_file, index=False)
    print(f"✅ Uloženo: {parquet_file}")

    # --- PREVIEW ---
    print(f"\n{'=' * 70}")
    print("PREVIEW DATAFRAME")
    print(f"{'=' * 70}\n")
    print(df.to_string())

    print(f"\n\n{'=' * 70}")
    print(f"✅ TEST HOTOV - {len(all_jobs)} nabídek zpracováno")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    test_first_3_urls()
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import time

chrome_options = Options()
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=chrome_options)

"""
Unique url scrap
"""
url = f"https://www.pracuj.pl/praca/x,oferta,1004628779"

try:
    driver.get(url)
    print("Čekám na načtení dat...")
    time.sleep(2)

    # --- 1. JSON-LD (základní info) ---
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    json_ld = soup.find('script', {'type': 'application/ld+json', 'id': 'job-schema-org'})

    if json_ld:
        job_data = json.loads(json_ld.string)

        print("\n=== ZÁKLADNÍ INFO ===")
        print("Pozice:", job_data.get('title'))
        print("Firma:", job_data.get('hiringOrganization'))
        print("Odvětví:", job_data.get('industry'))
        print("Typ smlouvy:", job_data.get('employmentType'))

        salary = job_data.get('baseSalary')
        if salary:
            print("Plat min:", salary.get('minValue'), salary.get('currency'))
            print("Plat max:", salary.get('maxValue'), salary.get('currency'))
        else:
            print("Plat: neuvedeno")

        location = job_data.get('jobLocation', {})
        address = location.get('address', {})
        print("Mesto:", location.get('name'))

        address = location.get('address', {})
        print("Region:", address.get('addressRegion'))
        print("Zkusenost:", job_data.get('experienceRequirements'))
        print("Ukoly:", job_data.get('responsibilities'))
        print("Benefity:", job_data.get('jobBenefits'))
        print("Datum zverejneni:", job_data.get('datePosted'))
        print("Platnost do:", job_data.get('validThrough'))

    # --- 2. NEXT_DATA (technologie, požadavky) ---
    next_data = driver.execute_script("return window.__NEXT_DATA__;")

    if next_data:
        try:
            position_levels_data = \
            next_data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']['attributes'][
                'employment']['positionLevels']

            if position_levels_data:
                print("\n💼 Úroveň pozice:")
                for level in position_levels_data:
                    print(f"   {level.get('name')}")
        except (KeyError, IndexError, TypeError):
            print("\n💼 Úroveň pozice: neuvedeno")


        try:
            work_schedule = \
            next_data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']['attributes'][
                'employment']['workSchedules']

            if work_schedule:
                print("\n💼 Uvazek")
                for level in work_schedule:
                    print(f"   {level.get('name')}")
        except (KeyError, IndexError, TypeError):
            print("\n💼 Úvazek: neuvedeno")


        try:
            work_mode = \
            next_data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']['attributes'][
                'employment']['workModes']

            if work_mode:
                print("\n💼 mod")
                for mode in work_mode:
                    print(f"   {mode.get('name')}")
        except (KeyError, IndexError, TypeError):
            print("\n💼 mod: neuvedeno")

        try:
            text_sections = next_data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data'][
                'textSections']

            print("\n=== TECHNOLOGIE A POŽADAVKY ===")

            for section in text_sections:
                section_type = section.get('sectionType')

                if section_type == 'technologies-expected':
                    print("\n✅ Vyžadované technologie:")
                    techs = section.get('textElements', [])
                    print(f"   {', '.join(techs)}")

                elif section_type == 'technologies-optional':
                    print("\n⭐ Vítané technologie:")
                    techs = section.get('textElements', [])
                    print(f"   {', '.join(techs)}")

                elif section_type == 'job-description':
                    print("\n📋 Popis práce:")
                    print(f"   {section.get('plainText', '')[:150]}...")

                elif section_type == 'requirements':
                    print("\n📌 Požadavky:")
                    for req in section.get('textElements', []):
                        print(f"   • {req}")

                elif section_type == 'offered':
                    print("\n🎁 Co nabízíme:")
                    for offer in section.get('textElements', []):
                        print(f"   • {offer}")

        except (KeyError, IndexError) as e:
            print(f"Chyba při čtení textSections: {e}")



finally:
    driver.quit()
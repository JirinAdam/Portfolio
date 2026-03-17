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

url = "https://www.pracuj.pl/praca/x,oferta,1004628779"

try:
    print("Oteviram stranku...")
    driver.get(url)

    print("Cekam na nacteni...")
    time.sleep(1)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    script = soup.find('script', {'type': 'application/ld+json', 'id': 'job-schema-org'})

    if script:
        print("JSON nalezen!\n")
        job_data = json.loads(script.string)

        print("Nazev pozice:", job_data.get('title'))
        print("Firma:", job_data.get('hiringOrganization'))
        print("Odvetvi:", job_data.get('industry'))
        print("Typ smlouvy:", job_data.get('employmentType'))

        salary = job_data.get('baseSalary')
        if salary:
            print("Plat min:", salary.get('minValue'), salary.get('currency'))
            print("Plat max:", salary.get('maxValue'), salary.get('currency'))
        else:
            print("Plat: neuvedeno")

        location = job_data.get('jobLocation', {})
        print("Mesto:", location.get('name'))

        address = location.get('address', {})
        print("Region:", address.get('addressRegion'))
        print("Zkusenost:", job_data.get('experienceRequirements'))
        print("Ukoly:", job_data.get('responsibilities'))
        print("Benefity:", job_data.get('jobBenefits'))
        print("Datum zverejneni:", job_data.get('datePosted'))
        print("Platnost do:", job_data.get('validThrough'))


    else:
        print("JSON stale nenalezen")
        print("Pocet JSON-LD scriptu:", len(soup.find_all('script', {'type': 'application/ld+json'})))

finally:
    driver.quit()
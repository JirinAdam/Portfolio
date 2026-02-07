from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json


def get_all_job_urls(max_pages=10):
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    all_urls = set()
    all_offer_ids = set()
    url = "https://www.pracuj.pl/praca"

    try:
        print(f"Načítám: {url}\n")
        driver.get(url)
        time.sleep(5)

        # --- COOKIES ---
        print("Akceptuji cookies...")
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-test="button-submitCookie"]'))
            )
            cookie_button.click()
            print("✅ Cookies přijato\n")
            time.sleep(2)
        except:
            print("⚠️ Cookie tlačítko nenalezeno\n")

        # --- PROJDI STRÁNKY ---
        for page_num in range(1, max_pages + 1):
            print(f"{'=' * 60}")
            print(f"STRÁNKA {page_num}")
            print(f"{'=' * 60}")

            # Čekání na data s timeout a retry
            page_loaded = False
            retry_count = 0
            max_retries = 5

            while retry_count < max_retries and not page_loaded:
                try:
                    # Čekej až se prvky naloadují
                    print(f"  ⏳ Čekám na nabídky (pokus {retry_count + 1}/{max_retries})...")

                    # Zkus dlouhé čekání na elementy
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-test="link-offer"]'))
                    )

                    # Zkontroluj __NEXT_DATA__
                    time.sleep(2)
                    next_data = driver.execute_script("return window.__NEXT_DATA__;")

                    if next_data:
                        queries = next_data['props']['pageProps']['dehydratedState']['queries']
                        if queries and queries[0]['state']['data'].get('groupedOffers'):
                            print("✅ Nabídky načteny\n")
                            page_loaded = True
                        else:
                            raise Exception("groupedOffers nejsou v datech")
                    else:
                        raise Exception("__NEXT_DATA__ není dostupný")

                except Exception as e:
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = 15
                        print(f"  ⏳ Čekám dalších {wait_time}s (Cloudflare?)...")
                        time.sleep(wait_time)
                    else:
                        print(f"❌ Stránka {page_num} se nepodařilo načíst\n")
                        print(f"✅ Vrací se {len(all_urls)} URL\n")
                        return list(all_urls)

            # --- EXTRAHUJ DATA ---
            try:
                next_data = driver.execute_script("return window.__NEXT_DATA__;")

                queries = next_data['props']['pageProps']['dehydratedState']['queries']
                first_query = queries[0]['state']['data']
                grouped_offers = first_query.get('groupedOffers', [])

                print(f"Nalezeno grouped offers: {len(grouped_offers)}")

                page_urls = set()
                page_offer_ids = set()

                for group in grouped_offers:
                    offers = group.get('offers', [])

                    for offer in offers:
                        partition_id = offer.get('partitionId')
                        offer_uri = offer.get('offerAbsoluteUri')

                        if partition_id and partition_id not in all_offer_ids:
                            if offer_uri:
                                clean_url = offer_uri.split('?')[0]
                                page_urls.add(clean_url)
                                page_offer_ids.add(partition_id)

                print(f"Extrahovano URL: {len(page_urls)}")
                all_urls.update(page_urls)
                all_offer_ids.update(page_offer_ids)
                print(f"Celkem unikátních: {len(all_offer_ids)}\n")

            except Exception as e:
                print(f"❌ Chyba extrakce: {e}\n")
                break

            # --- DALŠÍ STRÁNKA ---
            if page_num < max_pages:
                try:
                    next_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-test="bottom-pagination-button-next"]'))
                    )

                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                    time.sleep(2)
                    next_button.click()
                    print("✅ Kliknuto na 'Następna'")
                    print("⏳ Čekám 8 sekund na načtení nové stránky...\n")
                    time.sleep(8)

                except Exception as e:
                    print(f"⚠️ Konec - tlačítko nenalezeno\n")
                    break

        print(f"\n{'=' * 60}")
        print(f"✅ FINÁLNÍ POČET: {len(all_urls)} UNIKÁTNÍCH URL")
        print(f"{'=' * 60}\n")

    finally:
        driver.quit()

    return list(all_urls)


if __name__ == "__main__":
    urls = get_all_job_urls(max_pages=10)

    if urls:
        with open('job_urls.json', 'w', encoding='utf-8') as f:
            json.dump(urls, f, indent=2, ensure_ascii=False)

        print(f"✅ Uloženo {len(urls)} URL do job_urls.json\n")
        print(f"Prvních 20:")
        for i, url in enumerate(urls[:20], 1):
            print(f"{i}. {url}")
    else:
        print("❌ Žádné URL nenalezeny")
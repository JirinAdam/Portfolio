import cloudscraper
import json
import time

"""Testovy enviroment pro stahovani urls do listu job_urls.json
    Navazuje na nej url_scraper.py
"""

def get_all_job_urls_cloudscraper(max_pages=10):
    """
    HTTP scraping s Cloudflare bypassem
    """

    scraper = cloudscraper.create_scraper()

    all_urls = set()
    all_offer_ids = set()

    try:
        for page_num in range(1, max_pages + 1):
            print(f"{'=' * 60}")
            print(f"STRÁNKA {page_num}")
            print(f"{'=' * 60}\n")

            # URL s page parametrem
            if page_num == 1:
                url = "https://www.pracuj.pl/praca"
            else:
                url = f"https://www.pracuj.pl/praca?pn={page_num}"

            print(f"🌐 Načítám: {url}")

            try:
                response = scraper.get(url, timeout=30)
                response.raise_for_status()

                print(f"✅ HTTP {response.status_code}\n")

                # Hledej __NEXT_DATA__ v HTML
                html = response.text

                # Najdi script tag s __NEXT_DATA__
                start_idx = html.find('id="__NEXT_DATA__"')
                if start_idx == -1:
                    print("❌ __NEXT_DATA__ nenalezen\n")
                    return list(all_urls)

                # Najdi JSON uvnitř script tagu
                start_idx = html.find('{', start_idx)
                end_idx = html.find('</script>', start_idx)

                if start_idx == -1 or end_idx == -1:
                    print("❌ JSON nelze extrahovat\n")
                    return list(all_urls)

                json_str = html[start_idx:end_idx]

                # Parse JSON
                next_data = json.loads(json_str)

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

                # Pauza mezi requesty
                if page_num < max_pages:
                    wait_time = 3 + (page_num * 0.5)
                    print(f"⏳ Čekám {wait_time:.1f}s před další stránkou...\n")
                    time.sleep(wait_time)

            except Exception as e:
                print(f"❌ Chyba: {e}\n")
                print(f"✅ Vrací se {len(all_urls)} URL\n")
                return list(all_urls)

        print(f"\n{'=' * 60}")
        print(f"✅ FINÁLNÍ POČET: {len(all_urls)} UNIKÁTNÍCH URL")
        print(f"{'=' * 60}\n")

    except Exception as e:
        print(f"❌ Fatal chyba: {e}")

    return list(all_urls)


if __name__ == "__main__":
    urls = get_all_job_urls_cloudscraper(max_pages=10)

    if urls:
        with open('job_urls.json', 'w', encoding='utf-8') as f:
            json.dump(urls, f, indent=2, ensure_ascii=False)

        print(f"✅ Uloženo {len(urls)} URL do job_urls.json\n")
        print(f"Prvních 20:")
        for i, url in enumerate(urls[:20], 1):
            print(f"{i}. {url}")
    else:
        print("❌ Žádné URL nenalezeny")
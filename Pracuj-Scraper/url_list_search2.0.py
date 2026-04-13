import cloudscraper
import json
import time
from pathlib import Path


def get_all_job_urls_complete():
    """
    Scrapes ALL job URLs with error handling and retry logic
    """

    scraper = cloudscraper.create_scraper()
    all_urls = set()
    all_offer_ids = set()

    print(f"\n{'=' * 70}")
    print("SCRAPING ALL JOB URLS - COMPLETE WITH RETRY")
    print(f"{'=' * 70}\n")

    max_pages = 2000
    failed_pages = []
    last_update = 0
    retry_limit = 3
    empty_pages_count = 0
    empty_pages_limit = 10

    try:
        page_num = 1
        while page_num <= max_pages:
            # URL with page parameter
            if page_num == 1:
                url = "https://www.pracuj.pl/praca"
            else:
                url = f"https://www.pracuj.pl/praca?pn={page_num}"

            retry_count = 0
            success = False

            while retry_count < retry_limit and not success:
                try:
                    response = scraper.get(url, timeout=30)
                    response.raise_for_status()

                    html = response.text

                    # Find script tag with __NEXT_DATA__
                    start_idx = html.find('id="__NEXT_DATA__"')
                    if start_idx == -1:
                        print(f"❌ Page {page_num}: __NEXT_DATA__ not found")
                        failed_pages.append((page_num, "__NEXT_DATA__ not found"))
                        success = True
                        break

                    # Find JSON within script tag
                    start_idx = html.find('{', start_idx)
                    end_idx = html.find('</script>', start_idx)

                    if start_idx == -1 or end_idx == -1:
                        print(f"❌ Page {page_num}: JSON extraction failed")
                        failed_pages.append((page_num, "JSON extraction failed"))
                        success = True
                        break

                    json_str = html[start_idx:end_idx]
                    next_data = json.loads(json_str)

                    queries = next_data['props']['pageProps']['dehydratedState']['queries']

                    grouped_offers = []
                    used_query_index = None

                    for qi, q in enumerate(queries):
                        try:
                            candidate = q.get('state', {}).get('data') or {}
                            if isinstance(candidate, dict) and candidate.get('groupedOffers'):
                                grouped_offers = candidate['groupedOffers']
                                used_query_index = qi
                                break
                        except Exception:
                            continue

                    if not grouped_offers:
                        def _find_grouped_offers(obj):
                            if isinstance(obj, dict):
                                if 'groupedOffers' in obj and obj['groupedOffers']:
                                    return obj['groupedOffers']
                                for v in obj.values():
                                    result = _find_grouped_offers(v)
                                    if result:
                                        return result
                            elif isinstance(obj, list):
                                for item in obj:
                                    result = _find_grouped_offers(item)
                                    if result:
                                        return result
                            return None

                        fallback = _find_grouped_offers(next_data)
                        if fallback:
                            grouped_offers = fallback
                            used_query_index = 'recursive-fallback'

                    print(f"[DEBUG] Page {page_num}: groupedOffers from query index={used_query_index}, count={len(grouped_offers)}")

                    # ⚠️ If empty, try again
                    if not grouped_offers:
                        if retry_count < retry_limit - 1:
                            print(f"⚠️  Page {page_num}: Empty response - RETRY {retry_count + 1}/{retry_limit}")
                            time.sleep(3)
                            retry_count += 1
                            continue
                        else:
                            # All retries failed - count empty pages
                            empty_pages_count += 1
                            print(f"❌ Page {page_num}: Empty [{empty_pages_count}/{empty_pages_limit}]")
                            failed_pages.append((page_num, "Empty grouped_offers after retries"))

                            # If we have 3 empty pages in a row - BREAK
                            if empty_pages_count >= empty_pages_limit:
                                print(
                                    f"\n✅ {empty_pages_limit} consecutive empty pages - END OF DATA (scraped {len(all_urls)} URLs)")
                                success = True
                                page_num = max_pages + 1  # BREAK from while loop
                                break
                            else:
                                success = True
                                break

                    # Reset empty counter when we find data
                    empty_pages_count = 0

                    page_count = 0
                    for group in grouped_offers:
                        offers = group.get('offers', [])

                        for offer in offers:
                            partition_id = offer.get('partitionId')
                            offer_uri = offer.get('offerAbsoluteUri')

                            if partition_id and partition_id not in all_offer_ids:
                                if offer_uri:
                                    clean_url = offer_uri.split('?')[0]
                                    all_urls.add(clean_url)
                                    all_offer_ids.add(partition_id)
                                    page_count += 1

                    # UPDATE EVERY 1000 URLS
                    if len(all_urls) - last_update >= 1000:
                        print(f"[{page_num}] ✅ {len(all_urls)} URLs (page: +{page_count})")
                        last_update = len(all_urls)

                    success = True
                    time.sleep(0.5)

                except json.JSONDecodeError as e:
                    print(f"❌ Page {page_num}: JSON parse error - RETRY")
                    retry_count += 1
                    time.sleep(2)
                except Exception as e:
                    print(f"❌ Page {page_num}: {str(e)[:50]} - RETRY")
                    retry_count += 1
                    time.sleep(2)

            if not success:
                print(f"❌ Page {page_num}: All attempts failed - SKIP")
                failed_pages.append((page_num, "All retries failed"))

            page_num += 1

    except KeyboardInterrupt:
        print(f"\n\n⚠️  USER INTERRUPTED")

    except Exception as e:
        print(f"❌ Fatal error: {e}")

    # REPORT
    print(f"\n{'=' * 70}")
    print(f"✅ FINAL COUNT: {len(all_urls)} UNIQUE URLs")
    print(f"✅ PARTITION IDs: {len(all_offer_ids)} UNIQUE OFFERS")
    print(f"{'=' * 70}\n")

    if failed_pages:
        print(f"⚠️  Problem pages ({len(failed_pages)}):")
        for page, reason in failed_pages[:10]:
            print(f"   - pn={page}: {reason}")
        if len(failed_pages) > 10:
            print(f"   ... and {len(failed_pages) - 10} more")

    # Save to JSON
    script_dir = Path(__file__).parent.absolute()
    output_file = script_dir / 'job_urls_complete.json'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sorted(list(all_urls)), f, indent=2, ensure_ascii=False)

    print(f"\n📁 Saved: {output_file}")
    print(f"📊 Size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")

    return list(all_urls)


if __name__ == "__main__":
    urls = get_all_job_urls_complete()
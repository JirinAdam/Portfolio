import cloudscraper
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path


def debug_next_data_structure():
    """
    Debuguje strukturu NEXT_DATA
    """
    scraper = cloudscraper.create_scraper()
    url = "https://www.pracuj.pl/praca"

    try:
        print("🔍 Debuguji NEXT_DATA strukturu...\n")
        response = scraper.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')

        next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
        if next_data_script:
            next_data = json.loads(next_data_script.string)

            # Vypiš top-level keys
            print("TOP-LEVEL KEYS:")
            print(json.dumps(list(next_data.keys()), indent=2))

            # Naviguj do props
            print("\n\nPROPS KEYS:")
            props = next_data.get('props', {})
            print(json.dumps(list(props.keys()), indent=2))

            # Naviguj do pageProps
            print("\n\nPAGEPROPS KEYS:")
            page_props = props.get('pageProps', {})
            print(json.dumps(list(page_props.keys()), indent=2))

            # Naviguj do dehydratedState
            print("\n\nDEHYDRATEDSTATE KEYS:")
            dehydrated = page_props.get('dehydratedState', {})
            print(json.dumps(list(dehydrated.keys()), indent=2))

            # Naviguj do queries
            print("\n\nQUERIES STRUCTURE:")
            queries = dehydrated.get('queries', [])
            print(f"Počet queries: {len(queries)}")

            if queries:
                for i, query in enumerate(queries):
                    print(f"\nQuery {i}:")
                    print(f"  Keys: {list(query.keys())}")
                    if 'state' in query:
                        state = query['state']
                        print(f"  State keys: {list(state.keys())}")
                        if 'data' in state:
                            data = state['data']
                            print(f"  Data type: {type(data)}")
                            print(f"  Data value: {data}")

                            # Pokud je dict, vypiš keys
                            if isinstance(data, dict):
                                print(f"  Data keys: {list(data.keys())}")
                                # Vypiš sample
                                if 'jobOffers' in data:
                                    print(f"\n  jobOffers prvních 3:")
                                    for offer in data['jobOffers'][:3]:
                                        print(f"    - {offer}")
                                if 'pagination' in data:
                                    print(f"\n  pagination: {data['pagination']}")

            # Výpis všech query queryKey (abychom věděli co tam máme)
            print("\n\n" + "=" * 70)
            print("VŠECHNY QUERY KEYS:")
            print("=" * 70)
            for i, query in enumerate(queries):
                query_key = query.get('queryKey', [])
                query_hash = query.get('queryHash')
                data = query.get('state', {}).get('data')
                print(f"Query {i}: {query_key} | Data type: {type(data).__name__}")

        else:
            print("❌ NEXT_DATA script nenalezen!")

    except Exception as e:
        print(f"❌ Chyba: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_next_data_structure()

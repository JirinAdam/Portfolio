import cloudscraper
import re
import json

url = "https://www.pracuj.pl/praca/doradca-klienta-k-m-n-kielce-swietokrzyska-20,oferta,1004635483"

scraper = cloudscraper.create_scraper()

try:
    response = scraper.get(url, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Size: {len(response.text)} bytes")

    # Extract __NEXT_DATA__
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">({.*?})</script>',
        response.text,
        re.DOTALL
    )

    if not match:
        print("❌ __NEXT_DATA__ NOT found")
        exit(1)

    print("✅ __NEXT_DATA__ found")

    next_data = json.loads(match.group(1))
    print("✅ JSON valid")

    # Try to navigate
    try:
        data = next_data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']
        print("✅ Navigated to data successfully")

        # Check top-level keys
        print(f"\n📋 Data keys: {list(data.keys())}")

        # Get attributes
        attributes = data.get('attributes', {})
        print(f"✅ Attributes found: {len(attributes)} keys")
        print(f"   Keys: {list(attributes.keys())}")

        # Get employment
        employment = attributes.get('employment', {})
        print(f"✅ Employment found: {len(employment)} keys")
        print(f"   Keys: {list(employment.keys())}")

        # Get salary from typesOfContracts
        types_of_contracts = employment.get('typesOfContracts', [])
        print(f"✅ Types of contracts: {len(types_of_contracts)} items")

        if types_of_contracts:
            contract = types_of_contracts[0]
            print(f"   First contract keys: {list(contract.keys())}")

            salary = contract.get('salary', {})
            print(f"   Salary type: {type(salary)}")
            print(f"   Salary value: {salary}")

        # Get textSections
        text_sections = data.get('textSections', [])
        print(f"✅ Text sections: {len(text_sections)} items")

        for i, section in enumerate(text_sections):
            section_type = section.get('sectionType')
            text_elements = section.get('textElements', [])
            print(f"   [{i}] {section_type}: {len(text_elements)} elements")

        # Get workplaces
        workplaces = attributes.get('workplaces', [])
        print(f"✅ Workplaces: {len(workplaces)} items")
        if workplaces:
            workplace = workplaces[0]
            print(f"   First workplace keys: {list(workplace.keys())}")
            print(f"   City: {workplace.get('city')}")
            print(f"   Region: {workplace.get('voivodeship')}")

        print("\n✅ ALL DATA EXTRACTION SUCCESSFUL")

    except (KeyError, IndexError, TypeError) as e:
        print(f"❌ Navigation error: {e}")
        print(f"\n🔍 Trying to find path...")

        # Print structure
        print(f"next_data keys: {list(next_data.keys())}")

        if 'props' in next_data:
            print(f"  → props keys: {list(next_data['props'].keys())}")

            if 'pageProps' in next_data['props']:
                print(f"    → pageProps keys: {list(next_data['props']['pageProps'].keys())}")

                if 'dehydratedState' in next_data['props']['pageProps']:
                    ds = next_data['props']['pageProps']['dehydratedState']
                    print(f"      → dehydratedState keys: {list(ds.keys())}")

                    if 'queries' in ds:
                        print(f"        → queries count: {len(ds['queries'])}")
                        if ds['queries']:
                            print(f"        → first query keys: {list(ds['queries'][0].keys())}")

except Exception as e:
    import traceback

    print(f"❌ Error: {e}")
    traceback.print_exc()
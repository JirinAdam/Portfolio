import json
import re
from pathlib import Path
from bs4 import BeautifulSoup


def analyze_html(html_file='test.html'):
    """
    Analyze HTML structure and extract key info
    """

    if not Path(html_file).exists():
        print(f"❌ File not found: {html_file}")
        return

    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()

    print(f"\n{'=' * 80}")
    print(f"HTML ANALYSIS: {html_file}")
    print(f"{'=' * 80}\n")

    print(f"📊 FILE SIZE: {len(html):,} bytes\n")

    # --- 1. EXTRAHUJ __NEXT_DATA__ ---
    print(f"{'─' * 80}")
    print("1️⃣  __NEXT_DATA__ STRUCTURE")
    print(f"{'─' * 80}\n")

    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">({.*?})</script>', html, re.DOTALL)

    if match:
        try:
            json_str = match.group(1)
            next_data = json.loads(json_str)

            print(f"✅ __NEXT_DATA__ Found!")
            print(f"   Size: {len(json_str):,} bytes\n")

            # Navigate to data
            try:
                data = next_data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']
                print(f"✅ Successfully navigated to data\n")

                # Print top-level keys
                print(f"📋 TOP-LEVEL KEYS in 'data':")
                for key in data.keys():
                    value_type = type(data[key]).__name__

                    if isinstance(data[key], dict):
                        size = len(data[key])
                        print(f"   • {key:40s} ({value_type}) - {size} items")
                    elif isinstance(data[key], list):
                        size = len(data[key])
                        print(f"   • {key:40s} ({value_type}) - {size} items")
                    elif isinstance(data[key], str):
                        size = len(data[key])
                        preview = data[key][:60].replace('\n', ' ')
                        print(f"   • {key:40s} ({value_type}) - {size} chars: '{preview}...'")
                    else:
                        print(f"   • {key:40s} ({value_type})")

                # --- 2. ANALYZE attributes ---
                print(f"\n{'─' * 80}")
                print("2️⃣  ATTRIBUTES")
                print(f"{'─' * 80}\n")

                attributes = data.get('attributes', {})
                if attributes:
                    print(f"📋 ATTRIBUTES KEYS ({len(attributes)} items):")
                    for key in sorted(attributes.keys()):
                        value_type = type(attributes[key]).__name__

                        if isinstance(attributes[key], dict):
                            size = len(attributes[key])
                            print(f"   • {key:40s} ({value_type}) - {size} items")
                        elif isinstance(attributes[key], list):
                            size = len(attributes[key])
                            if size > 0:
                                first_item = attributes[key][0]
                                if isinstance(first_item, dict):
                                    first_keys = list(first_item.keys())[:3]
                                    print(f"   • {key:40s} ({value_type}) - {size} items [keys: {first_keys}]")
                                else:
                                    print(f"   • {key:40s} ({value_type}) - {size} items")
                            else:
                                print(f"   • {key:40s} ({value_type}) - EMPTY")
                        elif isinstance(attributes[key], str):
                            size = len(attributes[key])
                            preview = attributes[key][:50].replace('\n', ' ')
                            print(f"   • {key:40s} ({value_type}) - {size} chars")
                        else:
                            print(f"   • {key:40s} ({value_type})")

                # --- 3. ANALYZE employment (if exists) ---
                print(f"\n{'─' * 80}")
                print("3️⃣  EMPLOYMENT")
                print(f"{'─' * 80}\n")

                employment = attributes.get('employment', {})
                if employment:
                    print(f"📋 EMPLOYMENT KEYS ({len(employment)} items):")
                    for key in sorted(employment.keys()):
                        value_type = type(employment[key]).__name__

                        if isinstance(employment[key], list):
                            size = len(employment[key])
                            if size > 0:
                                first_item = employment[key][0]
                                if isinstance(first_item, dict):
                                    first_keys = list(first_item.keys())
                                    print(f"   • {key:40s} (list) - {size} items")
                                    print(f"      └─ structure: {first_keys}")
                                else:
                                    print(f"   • {key:40s} (list) - {size} items: {employment[key][:3]}")
                            else:
                                print(f"   • {key:40s} (list) - EMPTY")
                        elif isinstance(employment[key], dict):
                            size = len(employment[key])
                            print(f"   • {key:40s} (dict) - {size} items")
                        else:
                            print(f"   • {key:40s} ({value_type}): {employment[key]}")
                else:
                    print("❌ No employment data found")

                # --- 4. ANALYZE textSections (if exists) ---
                print(f"\n{'─' * 80}")
                print("4️⃣  TEXT SECTIONS")
                print(f"{'─' * 80}\n")

                text_sections = data.get('textSections', [])
                if text_sections:
                    print(f"✅ Found {len(text_sections)} text sections:\n")
                    for i, section in enumerate(text_sections, 1):
                        section_type = section.get('sectionType', 'N/A')
                        text_elements = section.get('textElements', [])
                        plain_text = section.get('plainText', '')

                        print(f"   [{i}] {section_type}")
                        print(f"       • textElements: {len(text_elements)} items")
                        if text_elements:
                            print(f"         └─ first 3: {text_elements[:3]}")
                        print(f"       • plainText: {len(plain_text)} chars")
                        if plain_text:
                            preview = plain_text[:80].replace('\n', ' ')
                            print(f"         └─ preview: '{preview}...'")
                        print()
                else:
                    print("❌ No textSections found")

                # --- 5. ANALYZE salary (if exists) ---
                print(f"{'─' * 80}")
                print("5️⃣  SALARY DATA")
                print(f"{'─' * 80}\n")

                salary = attributes.get('salary')
                if salary:
                    print(f"✅ Salary data found:")
                    if isinstance(salary, dict):
                        for key, value in salary.items():
                            print(f"   • {key}: {value}")
                    else:
                        print(f"   {salary}")
                else:
                    print("❌ No salary data found")

                # --- 6. KEY STATISTICS ---
                print(f"\n{'─' * 80}")
                print("6️⃣  KEY FIELDS SUMMARY")
                print(f"{'─' * 80}\n")

                key_fields = {
                    'jobTitle': attributes.get('jobTitle'),
                    'displayEmployerName': attributes.get('displayEmployerName'),
                    'description': len(attributes.get('description', '')) if attributes.get('description') else 0,
                    'salary': '✅' if salary else '❌',
                    'employment': '✅' if employment else '❌',
                    'textSections': f"{len(text_sections)} sections" if text_sections else '❌',
                    'categories': len(attributes.get('categories', [])),
                }

                for field, value in key_fields.items():
                    print(f"   {field:30s}: {value}")

                # --- 7. PRINT SAMPLE DATA ---
                print(f"\n{'─' * 80}")
                print("7️⃣  SAMPLE DATA")
                print(f"{'─' * 80}\n")

                print(f"📌 Job Title: {attributes.get('jobTitle')}")
                print(f"📌 Company: {attributes.get('displayEmployerName')}")
                print(f"📌 Description (first 200 chars):")
                desc = attributes.get('description', '')
                if desc:
                    print(f"   {desc[:200]}...")
                else:
                    print("   (none)")

                # --- EXPORT TO JSON ---
                print(f"\n{'─' * 80}")
                print("💾 EXPORT OPTIONS")
                print(f"{'─' * 80}\n")

                # Save sample attributes
                with open('sample_attributes.json', 'w', encoding='utf-8') as f:
                    json.dump(attributes, f, indent=2, ensure_ascii=False)
                print(f"✅ Saved: sample_attributes.json")

                # Save sample employment
                if employment:
                    with open('sample_employment.json', 'w', encoding='utf-8') as f:
                        json.dump(employment, f, indent=2, ensure_ascii=False)
                    print(f"✅ Saved: sample_employment.json")

                # Save full data
                with open('sample_full_data.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"✅ Saved: sample_full_data.json")

            except (KeyError, IndexError, TypeError) as e:
                print(f"❌ Cannot navigate data structure: {str(e)}")
                print(f"\nFallback: Printing first 500 chars of __NEXT_DATA__:")
                print(json.dumps(next_data, indent=2, ensure_ascii=False)[:500])

        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")

    else:
        print("❌ __NEXT_DATA__ not found in HTML")

    # --- 8. CHECK JSON-LD ---
    print(f"\n{'─' * 80}")
    print("8️⃣  JSON-LD SCHEMA")
    print(f"{'─' * 80}\n")

    json_ld_match = re.search(r'<script id="job-schema-org" type="application/ld\+json">({.*?})</script>', html,
                              re.DOTALL)

    if json_ld_match:
        try:
            json_ld = json.loads(json_ld_match.group(1))

            print(f"✅ JSON-LD Found!")
            print(f"   Type: {json_ld.get('@type')}")
            print(f"   Title: {json_ld.get('title')}")
            print(f"   Organization: {json_ld.get('hiringOrganization')}")
            print(f"   City: {json_ld.get('jobLocation', {}).get('name')}")

            salary_ld = json_ld.get('baseSalary')
            if salary_ld:
                print(
                    f"   Salary: {salary_ld.get('minValue')} - {salary_ld.get('maxValue')} {salary_ld.get('currency')}")
            else:
                print(f"   Salary: ❌")

        except json.JSONDecodeError:
            print("❌ Cannot parse JSON-LD")
    else:
        print("❌ JSON-LD not found")

    print(f"\n{'=' * 80}\n")


if __name__ == "__main__":
    analyze_html('test.html')
import json
import re


def extract_next_data(html):
    """Extract __NEXT_DATA__ JSON from HTML"""
    try:
        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">({.*?})</script>',
            html,
            re.DOTALL
        )
        if not match:
            return None
        json_str = match.group(1)
        next_data = json.loads(json_str)
        return next_data
    except (json.JSONDecodeError, AttributeError):
        return None


# Vezmi HTML jednoho jobu
html_file = "/Pracuj/test_salary.html"  # změň na skutečný soubor

with open(html_file, 'r', encoding='utf-8') as f:
    html = f.read()

next_data = extract_next_data(html)

if next_data:
    data = next_data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']
    attributes = data.get('attributes', {})

    # HLEDEJ VŠECHNY KLÍČE
    print("=== KEYS IN ATTRIBUTES ===")
    print(list(attributes.keys()))

    print("\n=== SECTIONS ===")
    if 'sections' in attributes:
        sections = attributes['sections']
        print(f"Found 'sections': {len(sections)} items")
        for i, section in enumerate(sections):
            print(f"\n[{i}] sectionType: {section.get('sectionType')}")
            if 'model' in section:
                model = section.get('model', {})
                custom_items = model.get('customItems', [])
                print(f"    customItems: {len(custom_items)}")
                if custom_items:
                    for item in custom_items[:3]:
                        print(f"      • {item}")

    print("\n=== TEXT_SECTIONS ===")
    if 'textSections' in attributes:
        text_sections = attributes['textSections']
        print(f"Found 'textSections': {len(text_sections)} items")
        for section in text_sections[:5]:
            print(f"  sectionType: {section.get('sectionType')}")
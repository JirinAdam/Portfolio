import sqlite3
import re
from pathlib import Path

# ============================================================================
# CURRENCY MAPPING - Detect → Standard code (IDENTICKÉ jako db_cleaner)
# ============================================================================
CURRENCY_MAPPING = {
    '€': 'EUR',
    'EUR': 'EUR',
    'eur': 'EUR',
    'EURO': 'EUR',
    'Euro': 'EUR',
    'euro': 'EUR',
    'PLN': 'PLN',
    'pln': 'PLN',
    'zł': 'PLN',
    'ZŁ': 'PLN',
    'zl': 'PLN',
    'Kč': 'CZK',
    'kč': 'CZK',
    'CZK': 'CZK',
    'czk': 'CZK'
}


def extract_currency_from_we_offer(we_offer_text):
    """
    Extrahuj MĚNU z we_offer textu
    Vrací: salary_currency (standardizovaný kód)
    - Detekuje první výskyt měny v textu
    """
    pattern = r'(\d{3,})\s*(?:(€|EUR|eur|EURO|Euro|euro|PLN|pln|zł|ZŁ|zl|Kč|kč|CZK|czk))'

    matches = re.findall(pattern, we_offer_text)

    if not matches:
        return None

    # Vezmi první detekovanou měnu
    for salary_str, currency_str in matches:
        if currency_str:
            return CURRENCY_MAPPING.get(currency_str, currency_str)

    return None


def fix_currency_data(conn):
    """
    Vyčisti NULL salary_currency pomocí regex z we_offer
    """
    cursor = conn.cursor()

    print("\n" + "=" * 100)
    print("🪙 OPRAVA SALARY CURRENCY DATA")
    print("=" * 100 + "\n")

    # Najdi řádky kde salary_currency IS NULL
    # ALE salary_min IS NOT NULL (aby měly salary)
    cursor.execute('''
                   SELECT partition_id, company, url, we_offer, salary_min, salary_max
                   FROM job_offers
                   WHERE salary_currency IS NULL
                     AND salary_min IS NOT NULL
                     AND we_offer IS NOT NULL
                   ''')

    rows = cursor.fetchall()

    if not rows:
        print("✅ Žádné řádky k updatu (všechny mají salary_currency)\n")
        return 0

    print(f"📌 Nalezeno {len(rows)} řádků s NULL salary_currency\n")
    print("📊 EXTRAHOVÁNÍ CURRENCY INFORMACÍ...\n")

    updates_data = []

    for partition_id, company, url, we_offer, salary_min, salary_max in rows:
        salary_currency = extract_currency_from_we_offer(we_offer)

        if salary_currency is not None:
            updates_data.append({
                'partition_id': partition_id,
                'company': company,
                'url': url,
                'we_offer': we_offer,
                'salary_min': salary_min,
                'salary_max': salary_max,
                'salary_currency': salary_currency
            })

    if not updates_data:
        print("❌ Žádné currency informace nebyly nalezeny v textech\n")
        return 0

    # Statistika měn
    currency_counts = {}
    for data in updates_data:
        curr = data['salary_currency']
        currency_counts[curr] = currency_counts.get(curr, 0) + 1

    print("=" * 100)
    print("📈 VÝSLEDKY ANALÝZY - CURRENCY")
    print("=" * 100)
    print(f"✅ Nalezeno {len(updates_data)} řádků s currency informacemi:\n")
    print("   💵 Detekované měny:")
    for curr, count in sorted(currency_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"      • {curr:10} {count:,} řádků")
    print(f"\n   Celkem k updatu: {len(updates_data)} řádků\n")

    # Potvrzení
    print("=" * 100)
    user_input = input("👉 POKRAČOVAT V UPDATU CURRENCY? (y/n): ").strip().lower()
    print("=" * 100 + "\n")

    if user_input != 'y':
        print("❌ Currency update zrušen\n")
        return 0

    # Update DB
    print("💾 UPDATUJU CURRENCY DATA...\n")

    updated_count = 0
    for data in updates_data:
        cursor.execute('''
                       UPDATE job_offers
                       SET salary_currency = ?
                       WHERE partition_id = ?
                       ''', (data['salary_currency'], data['partition_id']))

        updated_count += 1

    conn.commit()

    print(f"✅ Aktualizováno {updated_count} řádků\n")

    # Zobraz příklady
    print("=" * 100)
    print("📋 PRVNÍCH 10 PŘÍKLADŮ - CURRENCY UPDATE")
    print("=" * 100 + "\n")

    for i, data in enumerate(updates_data[:10], 1):
        salary_display = (
            f"{data['salary_min']:,} - {data['salary_max']:,}"
            if data['salary_max']
            else f"{data['salary_min']:,}"
        )

        print(f"[{i}] Company: {data['company'][:50]}")
        print(f"    URL: {data['url']}")
        print(f"    Salary: {salary_display} {data['salary_currency']}")
        print(f"    salary_currency: {data['salary_currency']}")
        print(f"    From text: {data['we_offer'][:90]}...\n")

    return updated_count


def main():
    db_path = Path('job_database.db')

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)

        print("\n" + "=" * 100)
        print("🪙 CURRENCY FIXER - JOB OFFERS")
        print("=" * 100)

        # Vyčisti currency data
        currency_updated = fix_currency_data(conn)

        conn.close()

        # Final summary
        print("\n" + "=" * 100)
        print("🎉 OPRAVA DOKONČENA")
        print("=" * 100)
        print(f"✅ Currency updates: {currency_updated:,} řádků")
        print("=" * 100 + "\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
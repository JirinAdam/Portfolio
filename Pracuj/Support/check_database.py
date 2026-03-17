import sqlite3
import json
from pathlib import Path


def check_database(db_path='job_database_test.db'):
    """
    Check and display database contents
    """

    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # --- 1. TABLE INFO ---
    print(f"\n{'=' * 80}")
    print(f"DATABASE: {db_path}")
    print(f"{'=' * 80}\n")

    cursor.execute('SELECT COUNT(*) FROM job_offers')
    total_records = cursor.fetchone()[0]
    print(f"📊 TOTAL RECORDS: {total_records}\n")

    # --- 2. COLUMN INFO ---
    cursor.execute("PRAGMA table_info(job_offers)")
    columns = cursor.fetchall()

    print(f"📋 COLUMNS ({len(columns)}):")
    for col in columns:
        print(f"   {col['cid'] + 1:2d}. {col['name']:30s} ({col['type']})")

    # --- 3. DATA STATISTICS ---
    print(f"\n{'=' * 80}")
    print(f"📈 DATA STATISTICS")
    print(f"{'=' * 80}\n")

    stats = {
        'title': 'With Title',
        'company': 'With Company',
        'salary_min': 'With Salary',
        'city': 'With City',
        'technologies_required': 'With Technologies',
        'position_levels': 'With Position Levels',
        'work_modes': 'With Work Modes',
        'job_description': 'With Description',
        'requirements': 'With Requirements',
        'offered': 'With Offered Benefits'
    }

    for col, label in stats.items():
        cursor.execute(f'SELECT COUNT(*) FROM job_offers WHERE {col} IS NOT NULL')
        count = cursor.fetchone()[0]
        percentage = (count / total_records * 100) if total_records > 0 else 0
        print(f"   ✅ {label:30s}: {count:4d} ({percentage:5.1f}%)")

    # --- 4. SAMPLE RECORDS ---
    print(f"\n{'=' * 80}")
    print(f"📝 SAMPLE RECORDS (First 3)")
    print(f"{'=' * 80}\n")

    cursor.execute('''
                   SELECT partition_id,
                          title,
                          company,
                          city,
                          salary_min,
                          salary_max,
                          technologies_required,
                          position_levels,
                          work_modes
                   FROM job_offers LIMIT 3
                   ''')

    records = cursor.fetchall()

    for idx, row in enumerate(records, 1):
        print(f"\n{'─' * 80}")
        print(f"RECORD {idx}")
        print(f"{'─' * 80}")
        print(f"🔹 ID:          {row['partition_id']}")
        print(f"🔹 Title:       {row['title']}")
        print(f"🔹 Company:     {row['company']}")
        print(f"🔹 City:        {row['city']}")
        print(f"💰 Salary:      {row['salary_min']} - {row['salary_max']}")

        if row['technologies_required']:
            techs = json.loads(row['technologies_required'])
            print(f"🔧 Technologies: {', '.join(techs[:5])}" +
                  (f" + {len(techs) - 5} more" if len(techs) > 5 else ""))
        else:
            print(f"🔧 Technologies: (None)")

        if row['position_levels']:
            levels = json.loads(row['position_levels'])
            print(f"💼 Position:    {', '.join(levels)}")
        else:
            print(f"💼 Position:    (None)")

        if row['work_modes']:
            modes = json.loads(row['work_modes'])
            print(f"📍 Work Mode:   {', '.join(modes)}")
        else:
            print(f"📍 Work Mode:   (None)")

    # --- 5. DETAILED VIEW OF FIRST RECORD ---
    if total_records > 0:
        print(f"\n{'=' * 80}")
        print(f"🔍 DETAILED VIEW (First Record - ALL FIELDS)")
        print(f"{'=' * 80}\n")

        cursor.execute('SELECT * FROM job_offers LIMIT 1')
        row = cursor.fetchone()

        for col in columns:
            col_name = col['name']
            value = row[col_name]

            # Pretty print JSON fields
            if col_name in ['technologies_required', 'technologies_optional',
                            'position_levels', 'work_schedules', 'work_modes',
                            'requirements', 'offered']:
                if value:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        value = f"[{len(parsed)} items] {str(parsed[:3])}..."
                    else:
                        value = str(parsed)[:100]

            # Truncate long strings
            if isinstance(value, str) and len(value) > 80:
                value = value[:80] + "..."

            print(f"   {col_name:30s}: {value}")

    # --- 6. SQL QUERIES EXAMPLES ---
    print(f"\n{'=' * 80}")
    print(f"💡 USEFUL SQL QUERIES")
    print(f"{'=' * 80}\n")

    # Top companies
    print("TOP 5 COMPANIES:")
    cursor.execute('''
                   SELECT company, COUNT(*) as count
                   FROM job_offers
                   WHERE company IS NOT NULL
                   GROUP BY company
                   ORDER BY count DESC
                       LIMIT 5
                   ''')
    for row in cursor.fetchall():
        print(f"   • {row[0]}: {row[1]} offers")

    # Top cities
    print("\nTOP 5 CITIES:")
    cursor.execute('''
                   SELECT city, COUNT(*) as count
                   FROM job_offers
                   WHERE city IS NOT NULL
                   GROUP BY city
                   ORDER BY count DESC
                       LIMIT 5
                   ''')
    for row in cursor.fetchall():
        print(f"   • {row[0]}: {row[1]} offers")

    # Salary range
    print("\nSALARY STATISTICS:")
    cursor.execute('''
                   SELECT MIN(salary_min) as min_salary,
                          MAX(salary_max) as max_salary,
                          AVG(salary_min) as avg_min,
                          AVG(salary_max) as avg_max
                   FROM job_offers
                   WHERE salary_min IS NOT NULL
                     AND salary_max IS NOT NULL
                   ''')
    row = cursor.fetchone()
    if row[0]:
        print(f"   Min offered: {row[0]}")
        print(f"   Max offered: {row[1]}")
        print(f"   Avg Min: {row[2]:.0f}")
        print(f"   Avg Max: {row[3]:.0f}")
    else:
        print("   No salary data")

    conn.close()
    print(f"\n{'=' * 80}\n")


if __name__ == "__main__":
    check_database('job_database_test.db')
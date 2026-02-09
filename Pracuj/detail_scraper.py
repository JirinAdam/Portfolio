import cloudscraper
import sqlite3
import json
import time
from pathlib import Path
import re


class JobDetailsScraper:
    """
    Complete job scraper for pracuj.pl using __NEXT_DATA__
    """

    def __init__(self, db_path='job_database.db'):
        self.scraper = cloudscraper.create_scraper()
        self.db_path = db_path
        self.failed_urls = []
        self.init_database()

    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS job_offers
                       (
                           partition_id
                           TEXT
                           PRIMARY
                           KEY,
                           url
                           TEXT
                           UNIQUE
                           NOT
                           NULL,
                           title
                           TEXT,
                           company
                           TEXT,
                           description
                           TEXT,
                           industry
                           TEXT,
                           employment_type
                           TEXT,
                           salary_min
                           INTEGER,
                           salary_max
                           INTEGER,
                           salary_currency
                           TEXT,
                           city
                           TEXT,
                           region
                           TEXT,
                           postal_code
                           TEXT,
                           position_levels
                           TEXT,
                           work_schedules
                           TEXT,
                           work_modes
                           TEXT,
                           technologies_os
                           TEXT,
                           responsibilities
                           TEXT,
                           requirements_expected
                           TEXT,
                           date_posted
                           DATE,
                           valid_through
                           DATE
                       )
                       ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_company ON job_offers(company)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_city ON job_offers(city)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_region ON job_offers(region)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON job_offers(title)')

        conn.commit()
        conn.close()
        print(f"✅ Database initialized: {self.db_path}\n")

    def extract_next_data(self, html):
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

    def extract_job_data(self, html, url):
        """Extract job data from __NEXT_DATA__"""
        try:
            next_data = self.extract_next_data(html)

            if not next_data:
                return None

            job_data = {}

            # Navigate to data
            try:
                data = next_data['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']
            except (KeyError, IndexError, TypeError):
                return None

            # --- BASIC INFO ---
            attributes = data.get('attributes', {})

            job_data['title'] = attributes.get('jobTitle')
            job_data['company'] = attributes.get('displayEmployerName')
            job_data['description'] = attributes.get('description')

            # --- CATEGORIES (INDUSTRY) ---
            categories = attributes.get('categories', [])
            job_data['industry'] = json.dumps(
                [cat.get('name') for cat in categories if cat.get('name')]
            ) if categories else None

            # --- EMPLOYMENT DATA ---
            employment = attributes.get('employment', {})

            # Position Levels
            position_levels = employment.get('positionLevels', [])
            job_data['position_levels'] = json.dumps(
                [pl.get('name') for pl in position_levels if pl.get('name')]
            ) if position_levels else None

            # Work Schedules
            work_schedules = employment.get('workSchedules', [])
            job_data['work_schedules'] = json.dumps(
                [ws.get('name') for ws in work_schedules if ws.get('name')]
            ) if work_schedules else None

            # Work Modes
            work_modes = employment.get('workModes', [])
            job_data['work_modes'] = json.dumps(
                [wm.get('name') for wm in work_modes if wm.get('name')]
            ) if work_modes else None

            # Contract Type & Salary
            types_of_contracts = employment.get('typesOfContracts', [])
            if types_of_contracts:
                contract = types_of_contracts[0]
                job_data['employment_type'] = contract.get('name')

                # SALARY - FIX: Handle None and dict
                salary = contract.get('salary')

                if isinstance(salary, dict):
                    job_data['salary_min'] = salary.get('minValue')
                    job_data['salary_max'] = salary.get('maxValue')

                    salary_currency = salary.get('currency')
                    job_data['salary_currency'] = salary_currency if isinstance(salary_currency, str) else 'PLN'
                else:
                    # Salary is None or other type
                    job_data['salary_min'] = None
                    job_data['salary_max'] = None
                    job_data['salary_currency'] = 'PLN'

            # --- TEXT SECTIONS ---
            text_sections = data.get('textSections', [])

            for section in text_sections:
                section_type = section.get('sectionType')
                text_elements = section.get('textElements', [])

                if section_type == 'technologies-os':
                    job_data['technologies_os'] = json.dumps(text_elements) if text_elements else None

                elif section_type == 'responsibilities':
                    job_data['responsibilities'] = json.dumps(text_elements) if text_elements else None

                elif section_type == 'requirements-expected':
                    job_data['requirements_expected'] = json.dumps(text_elements) if text_elements else None

            # --- LOCATION - FIX: Use inlandLocation for city/region ---
            workplaces = attributes.get('workplaces', [])
            if workplaces:
                workplace = workplaces[0]

                # Try to get city from inlandLocation
                inland_location = workplace.get('inlandLocation', {})
                if isinstance(inland_location, dict):
                    job_data['city'] = inland_location.get('city')
                    job_data['region'] = inland_location.get('voivodeship')
                    job_data['postal_code'] = inland_location.get('postalCode')
                else:
                    # Fallback na displayAddress
                    display_address = workplace.get('displayAddress', '')
                    job_data['city'] = display_address if display_address else None
                    job_data['region'] = None
                    job_data['postal_code'] = None

            # --- DATES ---
            pub_details = data.get('publicationDetails', {})
            job_data['date_posted'] = pub_details.get('dateOfInitialPublicationUtc')
            job_data['valid_through'] = pub_details.get('expirationDateUtc')

            # --- PARTITION ID ---
            job_data['partition_id'] = url.split('/')[-1]
            job_data['url'] = url

            return job_data

        except Exception as e:
            return None

    def save_to_database(self, job_data):
        """Save to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO job_offers (
                    partition_id, url, title, company, description,
                    industry, employment_type,
                    salary_min, salary_max, salary_currency,
                    city, region, postal_code,
                    position_levels, work_schedules, work_modes,
                    technologies_os, responsibilities,
                    requirements_expected,
                    date_posted, valid_through
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_data.get('partition_id'),
                job_data.get('url'),
                job_data.get('title'),
                job_data.get('company'),
                job_data.get('description'),
                job_data.get('industry'),
                job_data.get('employment_type'),
                job_data.get('salary_min'),
                job_data.get('salary_max'),
                job_data.get('salary_currency'),
                job_data.get('city'),
                job_data.get('region'),
                job_data.get('postal_code'),
                job_data.get('position_levels'),
                job_data.get('work_schedules'),
                job_data.get('work_modes'),
                job_data.get('technologies_os'),
                job_data.get('responsibilities'),
                job_data.get('requirements_expected'),
                job_data.get('date_posted'),
                job_data.get('valid_through')
            ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"   ❌ DB error: {str(e)[:50]}")
            return False

    def scrape_url(self, url, retry_limit=3):
        """Scrape single URL with retry"""
        retry_count = 0

        while retry_count < retry_limit:
            try:
                response = self.scraper.get(url, timeout=30)
                response.raise_for_status()

                job_data = self.extract_job_data(response.text, url)

                if job_data and self.save_to_database(job_data):
                    return True
                else:
                    return False

            except Exception as e:
                retry_count += 1
                if retry_count < retry_limit:
                    print(f"   ⚠️  Retry {retry_count}/{retry_limit}...", end=" ", flush=True)
                    time.sleep(2)
                else:
                    self.failed_urls.append((url.split('/')[-1][:40], str(e)[:30]))
                    return False

        return False

    def scrape_all_urls(self, url_list, batch_size=50):
        """Scrape all URLs in batches"""
        total = len(url_list)
        successful = 0
        failed = 0

        print(f"\n{'=' * 80}")
        print(f"SCRAPING {total} URLs - pracuj.pl")
        print(f"{'=' * 80}\n")

        for i, url in enumerate(url_list, 1):
            url_short = url.split('/')[-1][:45]
            print(f"[{i:3d}/{total}] {url_short}...", end=" ", flush=True)

            if self.scrape_url(url):
                successful += 1
                print("✅")
            else:
                failed += 1
                print("❌")

            # Progress report every 50 URLs
            if i % batch_size == 0:
                print(f"\n   → Progress: {i}/{total} ({(i / total * 100):.1f}%)\n")

            time.sleep(0.3)

        # Final report
        print(f"\n{'=' * 80}")
        print(f"✅ SUCCESS: {successful}/{total} ({(successful / total * 100):.1f}%)")
        print(f"❌ FAILED: {failed}/{total}")
        print(f"{'=' * 80}\n")

        self.print_database_stats()
        self.print_sample_data()

    def print_database_stats(self):
        """Print database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM job_offers')
            total = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM job_offers WHERE salary_min IS NOT NULL')
            with_salary = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM job_offers WHERE title IS NOT NULL')
            with_title = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM job_offers WHERE responsibilities IS NOT NULL')
            with_resp = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM job_offers WHERE city IS NOT NULL')
            with_city = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM job_offers WHERE region IS NOT NULL')
            with_region = cursor.fetchone()[0]

            cursor.execute(
                'SELECT AVG(salary_max - salary_min) FROM job_offers WHERE salary_min IS NOT NULL AND salary_max IS NOT NULL')
            avg_range = cursor.fetchone()[0]

            conn.close()

            print(f"📊 DATABASE STATISTICS:")
            print(f"   Total offers: {total}")
            print(f"   With title: {with_title}")
            print(f"   With salary: {with_salary}")
            print(f"   With city: {with_city}")
            print(f"   With region: {with_region}")
            print(f"   With responsibilities: {with_resp}")
            if avg_range:
                print(f"   Avg salary range: {int(avg_range):,}\n")
            else:
                print()

        except Exception as e:
            print(f"❌ Error: {e}")

    def print_sample_data(self):
        """Print sample records"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # With salary
            cursor.execute('SELECT * FROM job_offers WHERE salary_min IS NOT NULL ORDER BY rowid DESC LIMIT 1')
            row_with_salary = cursor.fetchone()

            # Random
            cursor.execute('SELECT * FROM job_offers ORDER BY RANDOM() LIMIT 1')
            row_random = cursor.fetchone()

            print(f"{'=' * 80}")
            print(f"SAMPLE RECORDS")
            print(f"{'=' * 80}\n")

            if row_with_salary:
                print(f"🔹 WITH SALARY:")
                print(f"   Title: {row_with_salary['title']}")
                print(f"   Company: {row_with_salary['company']}")
                print(f"   📍 Location: {row_with_salary['city']}, {row_with_salary['region']}")
                print(
                    f"   💰 Salary: {row_with_salary['salary_min']:,} - {row_with_salary['salary_max']:,} {row_with_salary['salary_currency']}")
                print(f"   🏷️  Type: {row_with_salary['employment_type']}")

                if row_with_salary['position_levels']:
                    levels = json.loads(row_with_salary['position_levels'])
                    print(f"   💼 Position: {', '.join(levels)}")

                if row_with_salary['work_modes']:
                    modes = json.loads(row_with_salary['work_modes'])
                    print(f"   🌐 Work Mode: {', '.join(modes)}")

                if row_with_salary['requirements_expected']:
                    reqs = json.loads(row_with_salary['requirements_expected'])
                    print(f"   📚 Requirements: {len(reqs)} items")
                    for req in reqs[:2]:
                        print(f"      • {req[:70]}")

            if row_random:
                print(f"\n{'─' * 80}")
                print(f"🔹 RANDOM RECORD:")
                print(f"   Title: {row_random['title']}")
                print(f"   Company: {row_random['company']}")
                print(f"   📍 Location: {row_random['city']}, {row_random['region']}")
                if row_random['salary_min']:
                    print(
                        f"   💰 Salary: {row_random['salary_min']:,} - {row_random['salary_max']:,} {row_random['salary_currency']}")
                else:
                    print(f"   💰 Salary: Not specified")
                print(f"   🏷️  Type: {row_random['employment_type']}")

                if row_random['position_levels']:
                    levels = json.loads(row_random['position_levels'])
                    print(f"   💼 Position: {', '.join(levels)}")

            print(f"\n{'=' * 80}\n")

            conn.close()

        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    url_file = Path(__file__).parent.absolute() / 'job_urls_complete.json'

    if not url_file.exists():
        print(f"❌ File not found: {url_file}")
        exit(1)

    with open(url_file, 'r', encoding='utf-8') as f:
        urls = json.load(f)

    print(f"✅ Loaded {len(urls)} URLs\n")

    scraper = JobDetailsScraper(db_path='job_database.db')

    # Scrape all URLs
    scraper.scrape_all_urls(urls)
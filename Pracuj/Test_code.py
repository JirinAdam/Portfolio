import cloudscraper
import sqlite3
import json
import time
from pathlib import Path
import re
import random


class JobDetailsScraper:
    """Complete job scraper for pracuj.pl"""

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
            CREATE TABLE IF NOT EXISTS job_offers (
                partition_id TEXT PRIMARY KEY,
                url TEXT UNIQUE NOT NULL,
                industry TEXT,
                company TEXT,
                title TEXT,
                description TEXT,
                employment_type TEXT,
                salary_min INTEGER,
                salary_max INTEGER,
                salary_currency TEXT,
                city TEXT,
                region TEXT,
                postal_code TEXT,
                position_levels TEXT,
                work_schedules TEXT,
                work_modes TEXT,
                technologies_os TEXT,
                technologies_optional TEXT,
                requirements_expected TEXT,
                we_offer TEXT,
                benefits TEXT,
                date_posted DATE,
                valid_through DATE
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
        """Extract __NEXT_DATA__ JSON"""
        try:
            match = re.search(
                r'<script id="__NEXT_DATA__"[^>]*type="application/json"[^>]*>',
                html
            )
            if not match:
                return None

            start_idx = match.end()
            json_start = html.find('{', start_idx)

            if json_start == -1:
                return None

            brace_count = 0
            json_end = json_start

            for i in range(json_start, len(html)):
                if html[i] == '{':
                    brace_count += 1
                elif html[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break

            if brace_count != 0:
                return None

            json_str = html[json_start:json_end]
            full_data = json.loads(json_str)

            try:
                dehydrated = full_data.get('props', {}).get('pageProps', {}).get('dehydratedState', {})
                queries = dehydrated.get('queries', [])

                if queries and len(queries) > 0:
                    data = queries[0].get('state', {}).get('data', {})
                    return data

                return full_data.get('props', {}).get('pageProps', {})

            except (KeyError, IndexError, TypeError):
                return None

        except (json.JSONDecodeError, AttributeError, ValueError):
            pass

        return None

    def extract_ld_json(self, html):
        """Extract LD+JSON from HTML"""
        try:
            pattern = r'<script[^>]*type="application/ld\+json"[^>]*>'
            match = re.search(pattern, html)

            if not match:
                return None

            start_idx = match.end()
            json_start = html.find('{', start_idx)

            if json_start == -1:
                return None

            brace_count = 0
            json_end = json_start

            for i in range(json_start, len(html)):
                if html[i] == '{':
                    brace_count += 1
                elif html[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break

            if brace_count != 0:
                return None

            json_str = html[json_start:json_end]
            return json.loads(json_str)

        except (json.JSONDecodeError, AttributeError, ValueError):
            pass

        return None

    def extract_job_data(self, html, url):
        """Extract job data from LD+JSON (priority) and __NEXT_DATA__ (fallback)"""
        try:
            next_data = self.extract_next_data(html)
            ld_json = self.extract_ld_json(html)

            if not next_data and not ld_json:
                return None

            job_data = {}
            data = next_data

            if ld_json:
                job_data['title'] = ld_json.get('title')
                job_data['company'] = ld_json.get('hiringOrganization')
                job_data['description'] = ld_json.get('responsibilities')

                industry = ld_json.get('industry')
                job_data['industry'] = industry if isinstance(industry, str) else None

                job_data['employment_type'] = ld_json.get('employmentType')
                job_data['requirements_expected'] = ld_json.get('experienceRequirements')
                job_data['benefits'] = ld_json.get('jobBenefits')

                city = None
                region = None
                postal_code = None

                job_location = ld_json.get('jobLocation', {})
                if isinstance(job_location, dict):
                    city = job_location.get('name')
                    address = job_location.get('address', {})
                    if isinstance(address, dict):
                        region = address.get('addressRegion')
                        postal_code = address.get('postalCode')
                        if not city:
                            city = address.get('addressLocality')

                job_data['city'] = city
                job_data['region'] = region
                job_data['postal_code'] = postal_code

                date_posted = ld_json.get('datePosted')
                job_data['date_posted'] = date_posted if isinstance(date_posted, str) else None

                valid_through = ld_json.get('validThrough')
                job_data['valid_through'] = valid_through if isinstance(valid_through, str) else None

                salary_min = None
                salary_max = None
                salary_currency = None

                if ld_json:
                    try:
                        base_salary = ld_json.get('baseSalary', {})

                        if isinstance(base_salary, dict):
                            salary_min = base_salary.get('minValue')
                            salary_max = base_salary.get('maxValue')
                            salary_currency = base_salary.get('currency')

                            if salary_min is not None and not isinstance(salary_min, (int, float)):
                                salary_min = None
                            if salary_max is not None and not isinstance(salary_max, (int, float)):
                                salary_max = None

                    except Exception:
                        pass

                if salary_min is None or salary_max is None:
                    if data:
                        try:
                            attributes = data.get('attributes', {})
                            employment = attributes.get('employment', {})
                            types_of_contracts = employment.get('typesOfContracts', [])

                            if types_of_contracts and isinstance(types_of_contracts, list):
                                for contract in types_of_contracts:
                                    salary = contract.get('salary')
                                    if salary:
                                        salary_min = salary.get('from')
                                        salary_max = salary.get('to')
                                        currency_obj = salary.get('currency', {})
                                        if isinstance(currency_obj, dict):
                                            salary_currency = currency_obj.get('code', 'PLN')
                                        break

                            if not salary_min and not salary_max:
                                if 'salary' in employment:
                                    salary = employment.get('salary')
                                    if isinstance(salary, dict):
                                        salary_min = salary.get('from')
                                        salary_max = salary.get('to')
                                        currency_obj = salary.get('currency', {})
                                        if isinstance(currency_obj, dict):
                                            salary_currency = currency_obj.get('code', 'PLN')

                        except Exception:
                            pass

                job_data['salary_min'] = salary_min
                job_data['salary_max'] = salary_max
                job_data['salary_currency'] = salary_currency if isinstance(salary_currency, str) else 'PLN'

            if data:
                attributes = data.get('attributes', {})
                employment = attributes.get('employment', {})

                position_levels = employment.get('positionLevels', [])
                job_data['position_levels'] = json.dumps(
                    [pl.get('name') for pl in position_levels if pl.get('name')]
                ) if position_levels else None

                work_schedules = employment.get('workSchedules', [])
                job_data['work_schedules'] = json.dumps(
                    [ws.get('name') for ws in work_schedules if ws.get('name')]
                ) if work_schedules else None

                work_modes = employment.get('workModes', [])
                job_data['work_modes'] = json.dumps(
                    [wm.get('name') for wm in work_modes if wm.get('name')]
                ) if work_modes else None

            technologies_required = []
            technologies_optional = []

            if data:
                try:
                    sections = data.get('sections', [])

                    if isinstance(sections, list):
                        for section in sections:
                            if not isinstance(section, dict):
                                continue

                            sub_sections = section.get('subSections')

                            if not isinstance(sub_sections, list):
                                continue

                            for sub_section in sub_sections:
                                if not isinstance(sub_section, dict):
                                    continue

                                section_type = sub_section.get('sectionType')

                                if section_type == 'technologies-expected':
                                    model = sub_section.get('model', {})
                                    if isinstance(model, dict):
                                        custom_items = model.get('customItems', [])
                                        if isinstance(custom_items, list):
                                            technologies_required = [
                                                item.get('name') for item in custom_items
                                                if isinstance(item, dict) and item.get('name') and isinstance(
                                                    item.get('name'), str)
                                            ]

                                elif section_type == 'technologies-optional':
                                    model = sub_section.get('model', {})
                                    if isinstance(model, dict):
                                        custom_items = model.get('customItems', [])
                                        if isinstance(custom_items, list):
                                            technologies_optional = [
                                                item.get('name') for item in custom_items
                                                if isinstance(item, dict) and item.get('name') and isinstance(
                                                    item.get('name'), str)
                                            ]

                except Exception:
                    pass

            job_data['technologies_os'] = json.dumps(technologies_required) if technologies_required else None
            job_data['technologies_optional'] = json.dumps(technologies_optional) if technologies_optional else None

            # --- OFFERED - PLAIN TEXT FROM textSections ---
            we_offer = None

            if data:
                try:
                    text_sections = data.get('textSections', [])

                    for section in text_sections:
                        if not isinstance(section, dict):
                            continue

                        if section.get('sectionType') != 'offered':
                            continue

                        plain_text = section.get('plainText')
                        if isinstance(plain_text, str) and plain_text.strip():
                            we_offer = plain_text.strip()
                            break

                except Exception:
                    pass

            job_data['we_offer'] = we_offer if we_offer else None

            job_data['partition_id'] = url.split('/')[-1]
            job_data['url'] = url

            return job_data

        except Exception:
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
                    technologies_os, technologies_optional,
                    requirements_expected,
                    we_offer,
                    benefits,
                    date_posted, valid_through
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                job_data.get('technologies_optional'),
                job_data.get('requirements_expected'),
                job_data.get('we_offer'),
                job_data.get('benefits'),
                job_data.get('date_posted'),
                job_data.get('valid_through')
            ))

            conn.commit()
            conn.close()
            return True

        except Exception:
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
                    wait_time = 2 * retry_count
                    time.sleep(wait_time)
                else:
                    self.failed_urls.append((url.split('/')[-1][:40], str(e)[:30]))
                    return False

        return False

    def get_unprocessed_urls(self, url_list):
        """Načti z DB jaké URLs už jsou zpracované a vrať jenom nové"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT partition_id FROM job_offers')

            # Set pro O(1) lookup
            processed_ids = {row[0] for row in cursor.fetchall()}
            conn.close()

            # Filtruj - vrať jen ty co nejsou v DB
            unprocessed = [
                url for url in url_list
                if url.split('/')[-1] not in processed_ids
            ]

            return unprocessed

        except Exception as e:
            print(f"❌ Error loading processed URLs: {e}")
            return url_list

    def scrape_all_urls(self, url_list, batch_size=100):
        """Scrape all URLs - auto skip already processed"""

        # KLÍČOVÉ: Filtruj zduplikované
        unprocessed = self.get_unprocessed_urls(url_list)

        if not unprocessed:
            print("✅ Všechny URLs již zpracované!\n")
            return

        total = len(unprocessed)
        already_done = len(url_list) - total

        print(f"\n{'=' * 80}")
        print(f"SCRAPING {total} URLs (z {len(url_list)} celkem)")
        print(f"Already processed: {already_done}")
        print(f"{'=' * 80}\n")

        successful = 0
        failed = 0
        consecutive_fails = 0
        start_time = time.time()

        for i, url in enumerate(unprocessed, 1):
            url_short = url.split('/')[-1][:45]
            print(f"[{i:3d}/{total}] {url_short}...", end=" ", flush=True)

            if self.scrape_url(url):
                successful += 1
                print("✅")
                consecutive_fails = 0
            else:
                failed += 1
                consecutive_fails += 1
                print("❌")

                if consecutive_fails >= 5:
                    print(f"\n   ⚠️  5x consecutive fails - WAF/IP ban")
                    print(f"   💤 Čekání 120 sekund...\n")
                    time.sleep(120)
                    consecutive_fails = 0

            delay = random.uniform(1.5, 2.2)
            time.sleep(delay)

            # Progress every 100 URLs
            if i % batch_size == 0:
                print(f"\n   → Progress: {i}/{total} ({(i / total * 100):.1f}%)")
                batch_delay = random.uniform(2, 5)
                print(f"   💤 Batch break - {batch_delay:.1f}s...\n")
                time.sleep(batch_delay)

        end_time = time.time()
        elapsed = end_time - start_time
        elapsed_str = self._format_time(elapsed)

        print(f"\n{'=' * 80}")
        print(f"✅ SUCCESS: {successful}/{total} ({(successful / total * 100):.1f}%)")
        print(f"❌ FAILED: {failed}/{total}")
        print(f"⏱️  EXECUTION TIME: {elapsed_str}")
        print(f"{'=' * 80}\n")

        self.print_database_stats()
        self.print_sample_data()

    def _format_time(self, seconds):
        """Format seconds to HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"

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

            cursor.execute('SELECT COUNT(*) FROM job_offers WHERE city IS NOT NULL')
            with_city = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM job_offers WHERE region IS NOT NULL')
            with_region = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM job_offers WHERE technologies_os IS NOT NULL')
            with_tech = cursor.fetchone()[0]

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
            print(f"   With technologies: {with_tech}")
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

            cursor.execute('SELECT * FROM job_offers WHERE salary_min IS NOT NULL ORDER BY rowid DESC LIMIT 1')
            row_with_salary = cursor.fetchone()

            cursor.execute('SELECT * FROM job_offers WHERE technologies_os IS NOT NULL ORDER BY rowid DESC LIMIT 1')
            row_with_tech = cursor.fetchone()

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

            if row_with_tech:
                print(f"\n{'─' * 80}")
                print(f"🔹 WITH TECHNOLOGIES:")
                print(f"   Title: {row_with_tech['title']}")
                print(f"   Company: {row_with_tech['company']}")

                if row_with_tech['technologies_os']:
                    techs = json.loads(row_with_tech['technologies_os'])
                    print(f"   🔧 Required technologies: {', '.join(techs[:5])}")
                    if len(techs) > 5:
                        print(f"      ... and {len(techs) - 5} more")

                if row_with_tech['technologies_optional']:
                    opt_techs = json.loads(row_with_tech['technologies_optional'])
                    print(f"   ⭐ Optional technologies: {', '.join(opt_techs[:5])}")
                    if len(opt_techs) > 5:
                        print(f"      ... and {len(opt_techs) - 5} more")

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

    # Auto-skip already processed URLs
    scraper.scrape_all_urls(urls)
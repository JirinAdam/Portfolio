"""
Password strength checker module.
Analyzes existing passwords and rates their security.
Includes HIBP API integration with rate limiting.

Reuses ALL analysis functions from project module - THIS CLASS IS JUST A HIBP WRAPPER!
"""

import csv
from pathlib import Path
from collections import defaultdict
import hashlib
import requests
import time


class PasswordChecker:
    """
    wrapper for HIBP API checks.
    All entropy/rating logic is delegated to project.evaluate_entropy() and rate_strength().

    This class handles ONLY:
    1. CSV loading
    2. Password analysis orchestration
    3. HIBP API calls
    4. Output formatting
    """

    def __init__(self, csv_file: str = None):
        """Initialize checker and load passwords."""
        if csv_file is None:
            current_dir = Path(__file__).parent.parent
            csv_file = current_dir / 'passwords.csv'

        self.csv_file = Path(csv_file)
        self.passwords = []
        self._load_passwords()

    def _load_passwords(self) -> None:
        """Load passwords from CSV file."""
        if not self.csv_file.exists():
            raise FileNotFoundError(
                f"File '{self.csv_file}' not found.\n"
                f"Expected location: {self.csv_file.absolute()}\n"
                f"Create a passwords.csv file with format:\n"
                f"Service,Password\n"
                f"facebook.com,tF7W!fG6"
            )

        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    password = row.get('Password')
                    service = row.get('Service')
                    if password:
                        self.passwords.append({
                            'password': password.strip(),
                            'service': (service.strip() if service else 'N/A')
                        })
            print(f"✓ Loaded {len(self.passwords)} passwords from CSV\n")
        except Exception as e:
            raise Exception(f"Error reading CSV: {e}")

    def _get_charset_size(self, password: str) -> int:
        """Determine charset size from password composition."""
        charset_size = 0
        if any(c.islower() for c in password):
            charset_size += 26
        if any(c.isupper() for c in password):
            charset_size += 26
        if any(c.isdigit() for c in password):
            charset_size += 10
        if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            charset_size += 32
        return charset_size if charset_size > 0 else 26

    def _analyze_password(self, password: str) -> dict:
        """Use project.py functions to analyze password."""

        #Lazy import to avoid circular import error
        from FinalProject.project import evaluate_entropy, rate_strength, calculate_crack_time

        charset_size = self._get_charset_size(password)
        length = len(password)

        # ✅ DELEGATE TO PROJECT MODULE
        entropy = evaluate_entropy(length, charset_size)
        rating_data = rate_strength(entropy)
        crack_time = calculate_crack_time(entropy)

        return {
            'entropy': entropy,
            'rating': rating_data['rating'],
            'crack_time': crack_time,
            'emoji': rating_data['emoji']
        }

    def check_hibp(self, password: str) -> dict:
        """
        Check password against Have I Been Pwned API.
        Only method that does ORIGINAL work (not delegated).
        """
        try:
            sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
            prefix = sha1_hash[:5]
            suffix = sha1_hash[5:]

            url = f"https://api.pwnedpasswords.com/range/{prefix}"
            headers = {'User-Agent': 'PasswordSecurityToolkit/1.0'}
            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 429:
                return {
                    'breached': None,
                    'count': None,
                    'status': 'rate_limited',
                    'retry_after': response.headers.get('Retry-After', 'unknown'),
                    'error': f'Rate limited by HIBP API. Retry after: {response.headers.get("Retry-After", "unknown")}s'
                }
            elif response.status_code == 503:
                return {'breached': None, 'count': None, 'status': 'service_unavailable', 'error': 'HIBP API temporarily unavailable'}
            elif response.status_code == 400:
                return {'breached': None, 'count': None, 'status': 'bad_request', 'error': 'Invalid API request'}
            elif response.status_code == 200:
                for hash_line in response.text.split('\r\n'):
                    if ':' in hash_line:
                        h, count = hash_line.split(':')
                        if h == suffix:
                            return {'breached': True, 'count': int(count), 'status': 'found'}
                return {'breached': False, 'count': 0, 'status': 'clean'}
            else:
                return {'breached': None, 'count': None, 'status': 'unknown_error', 'error': f'HTTP {response.status_code}'}
        except requests.exceptions.Timeout:
            return {'breached': None, 'count': None, 'status': 'timeout', 'error': 'HIBP API request timed out (5s)'}
        except requests.exceptions.ConnectionError:
            return {'breached': None, 'count': None, 'status': 'connection_error', 'error': 'Failed to connect to HIBP API'}
        except Exception as e:
            return {'breached': None, 'count': None, 'status': 'error', 'error': f'Unexpected error: {str(e)}'}

    def analyze_all(self) -> list:
        """Analyze all passwords using project module functions."""
        results = []
        print("Analyzing passwords...\n")

        start_time = time.time()

        for idx, pwd_data in enumerate(self.passwords, 1):
            password = pwd_data['password']
            service = pwd_data['service']

            # ✅ USE PROJECT FUNCTIONS
            analysis = self._analyze_password(password)
            hibp = self.check_hibp(password)

            results.append({
                'password': password,
                'service': service,
                'entropy': analysis['entropy'],
                'rating': analysis['rating'],
                'crack_time': analysis['crack_time'],
                'emoji': analysis['emoji'],
                'hibp_breached': hibp.get('breached'),
                'hibp_count': hibp.get('count'),
                'hibp_status': hibp.get('status', 'unknown'),
                'hibp_error': hibp.get('error')
            })

            print(f"  [{idx}/{len(self.passwords)}] {service} {analysis['emoji']} {analysis['rating']:<12} | {password}")

            if hibp.get('status') == 'rate_limited':
                retry_after = int(hibp.get('retry_after', 900))
                print(f"\n⚠️  RATE LIMIT EXCEEDED! Please wait {retry_after}s before retrying.\n")
                break

            if idx < len(self.passwords):
                time.sleep(0.5)

        elapsed = time.time() - start_time
        print(f"\n✓ Analysis completed in {elapsed:.2f}s")
        print(f"✓ HIBP API requests made: {len(results)}\n")

        # Sort by strength
        rating_order = {'CRITICAL': 0, 'VERY WEAK': 1, 'WEAK': 2, 'MODERATE': 3, 'GOOD': 4, 'STRONG': 5, 'VERY STRONG': 6, 'EXCEPTIONAL': 7, 'MAXIMUM': 8}
        results.sort(key=lambda x: rating_order.get(x['rating'], 9))

        return results

    def print_analysis(self, results: list) -> None:
        """Print organized analysis grouped by rating with security warnings."""

        #Lazy import to avoid circular import error
        from FinalProject.project import calculate_crack_time

        grouped = defaultdict(list)
        for result in results:
            grouped[result['rating']].append(result)

        rating_order = ['CRITICAL', 'VERY WEAK', 'WEAK', 'MODERATE', 'GOOD', 'STRONG', 'VERY STRONG', 'EXCEPTIONAL', 'MAXIMUM']

        print("\n" + "=" * 160)
        print(f"\n{' ':<60}PASSWORD SECURITY ANALYSIS - GROUPED BY STRENGTH")
        print("\n" + "=" * 160)
        print(f"{'Strength':<23} {'Online Attack':<25} {'GPU Farm Attack':<26} {'Entropy':<25} {'HIBP Status':<20}")
        print(f"{'(Rating)':<23} {'(Rate: 7.2k/day)':<25} {'(1 PetaFLOPS)':<26} {' ':<25} {'(Breach DB)':<20}")
        print("=" * 160 + "\n")

        for rating in rating_order:
            if rating not in grouped:
                continue

            passwords = grouped[rating]
            emoji = passwords[0]['emoji']

            print(f"{emoji} {rating} ({len(passwords)} password(s))")
            print("-" * 160)

            for pwd_data in passwords:
                hibp_status = pwd_data.get('hibp_status', 'unknown')
                hibp_count = pwd_data.get('hibp_count')

                # HIBP display
                hibp_display = {
                    'found': f"🚨 BREACHED ({hibp_count}x)",
                    'clean': "✓ Clean",
                    'rate_limited': "⏱️  RATE LIMITED",
                    'timeout': "⏰ TIMEOUT",
                    'connection_error': "🌐 CONNECTION ERROR",
                    'service_unavailable': "🔴 SERVICE UNAVAILABLE",
                    'bad_request': "❌ BAD REQUEST"
                }.get(hibp_status, "❓ UNKNOWN")

                # Calculate attack times
                entropy = pwd_data['entropy']
                online_rate = 7200 / 86400  # 7.2k attempts per day
                gpu_farm_rate = 1e15  # 1 PetaFLOPS

                online_time = calculate_crack_time(entropy, online_rate)
                gpu_time = calculate_crack_time(entropy, gpu_farm_rate)

                print(f"  • {pwd_data['service']:<20} {online_time:<25} {gpu_time:<25} {pwd_data['entropy']:.2f} bits {'':<15} {hibp_display:<20}")

                if pwd_data.get('hibp_error'):
                    print(f"     └─ ℹ️  {pwd_data['hibp_error']}")

            print()

        print("=" * 160 + "\n")

        # ✅ SECURITY WARNINGS SECTION
        self._print_security_warnings(results)

    def _print_security_warnings(self, results: list) -> None:
        """Print security warnings for breached and weak passwords."""

        # Check for breached passwords
        breached = [r for r in results if r['hibp_breached'] is True]

        # GPU crackable: entropy < 50 bits (crackable in seconds by GPU farm)
        gpu_crackable = [r for r in results if r['entropy'] < 68]

        if breached or gpu_crackable:
            print("\n" + "🚨" * 40)
            print(f"{' ':<40}SECURITY ALERTS")
            print("🚨" * 40 + "\n")

        # Breached passwords warning
        if breached:
            breach_count = len(breached)
            affected_services = [r['service'] for r in breached]
            print(f"🚨 ACTION REQUIRED: {breach_count} password(s) have been found in known breaches!")
            print(f"   Recommend: Change these passwords immediately!")
            print(f"   Affected accounts: {', '.join(affected_services)}\n")

        # GPU crackable passwords warning
        if gpu_crackable:
            gpu_count = len(gpu_crackable)
            affected_services = [r['service'] for r in gpu_crackable]
            print(f"⚠️  CRITICAL: {gpu_count} password(s) can be cracked within HOURS by modern GPU farms!")
            print(f"   - If your database leaks, attackers will break them instantly")
            print(f"   - Minimum recommendation: Increase length or character types")
            print(f"   - Affected accounts: {', '.join(affected_services)}\n")

        if breached or gpu_crackable:  #redundant
            print("=" * 160 + "\n")
"""
Password & Passphrase Security Toolkit
Main module with orchestration and core analysis functions.
Import from generators/classes
"""

import math
from generators import PasswordGenerator
from generators import DicewareGenerator



def evaluate_entropy(length: int, charset_size: int) :
    """
    Calculates theoretical entropy for password/passphrase.
    """
    entropy = length * math.log2(charset_size)
    return entropy


def rate_strength(entropy: float) -> dict:
    """
    Rate password/passphrase strength based on entropy.
    Emphasis on GPU farm attacks.

    """

    # Helper function for time description
    def _get_time_description(seconds: float) -> str:
        """Convert seconds to readable time description."""
        if seconds < 1:
            return "instantly (< 1 second)"
        elif seconds < 60:
            return f"in seconds ({seconds:.1f} sec)"
        elif seconds < 3600:
            return f"in minutes ({seconds / 60:.1f} min)"
        elif seconds < 86400:
            return f"in hours ({seconds / 3600:.1f} hours)"
        elif seconds < 604800:  # 7 days
            return f"in days ({seconds / 86400:.1f} days)"
        elif seconds < 2592000:  # 30 days
            return f"in weeks ({seconds / 604800:.1f} weeks)"
        elif seconds < 31536000:  # 1 year
            return f"in months ({seconds / 2592000:.1f} months)"
        elif seconds < 31536000 * 100:  # 100 years
            return f"in years ({seconds / 31536000:.1f} years)"
        elif seconds < 31536000 * 10000:  # 10k years
            return f"in centuries ({seconds / (31536000 * 100):.1f} centuries)"
        elif seconds < 31536000 * 1000000:  # 1M years
            return f"in millennia ({seconds / (31536000 * 1000):.1f} millennia)"
        else:
            return "beyond geological timescales (>1M years)"

    # Calculate GPU farm crack time
    gpu_farm_rate = 1e15  # 10^15 guesses/s (fast hash, e.g. MD5 on ~4,500 RTX 5090)
    total_combinations = 2 ** entropy
    seconds = (total_combinations / 2) / gpu_farm_rate
    time_desc = _get_time_description(seconds)

    # Rating logic based on entropy ranges
    if entropy < 32:
        return {
            'rating': 'CRITICAL',
            'emoji': '🔓',
            'description': f'Crackable by GPU farms {time_desc}',
            'warning': '🚨 CRITICAL: This password offers NO protection against modern attacks!',
            'recommendation': 'CHANGE IMMEDIATELY - Completely unsafe',
            'standards': []
        }

    elif entropy < 40:
        return {
            'rating': 'VERY WEAK',
            'emoji': '⏰',
            'description': f'Crackable by GPU farms {time_desc}',
            'warning': '⚠️  WARNING: Trivially crackable by automated tools',
            'recommendation': 'Not safe for any real use',
            'standards': [
                '⚠️  Far below a 4-word EFF Diceware passphrase (~51.7 bits)'
            ]
        }

    elif entropy < 50:
        return {
            'rating': 'WEAK',
            'emoji': '🔐',
            'description': f'Crackable by GPU farms {time_desc}',
            'warning': '⚠️  Vulnerable to professional attackers with GPU resources',
            'recommendation': 'Use only for low-value, non-sensitive accounts',
            'standards': [
                '⚠️  Below a 4-word EFF Diceware passphrase (~51.7 bits)'
            ]
        }

    elif entropy < 63:
        return {
            'rating': 'MODERATE',
            'emoji': '✓',
            'description': f'Crackable by GPU farms {time_desc}',
            'warning': '💡 Minimal protection against offline (leaked database) attacks',
            'recommendation': 'Increase length (15+ characters or 6+ Diceware words)',
            'standards': [
                'ℹ️  Comparable to a 4-word EFF Diceware passphrase (~51.7 bits)',
                '⚠️  Below the EFF recommendation of 6+ words (~77.5 bits)'
            ]
        }

    elif entropy < 80:
        # GOOD/STRONG range - internal granularity
        if entropy < 70:
            rating_level = 'GOOD'
            emoji = '✅'
            standards = [
                '⚠️  Below the EFF recommendation of 6+ words (~77.5 bits)'
            ]
        else:
            rating_level = 'STRONG'
            emoji = '🔒'
            standards = [
                'ℹ️  Around the EFF 6-word passphrase recommendation (~77.5 bits)'
            ]

        return {
            'rating': rating_level,
            'emoji': emoji,
            'description': f'Resistant to GPU farms for {time_desc.replace("in ", "")}',
            'warning': '✓ Good protection for standard use cases',
            'recommendation': 'Suitable for most applications',
            'standards': standards
        }

    elif entropy < 100:
        return {
            'rating': 'VERY STRONG',
            'emoji': '⚜️',
            'description': f'Resistant to GPU farms for {time_desc.replace("in ", "")}',
            'warning': '✓ Excellent protection - enterprise grade security',
            'recommendation': 'Excellent for sensitive/critical data',
            'standards': [
                '✓ Exceeds the EFF 6-word passphrase recommendation (~77.5 bits)',
                '✓ Beyond practical brute-force attacks'
            ]
        }

    elif entropy < 128:
        return {
            'rating': 'EXCEPTIONAL',
            'emoji': '🏆',
            'description': f'Resistant to GPU farms for {time_desc.replace("in ", "")}',
            'warning': '✓ Maximum practical security for current threats',
            'recommendation': 'Exceeds common password guidance',
            'standards': [
                '✓ Exceeds the EFF 6-word passphrase recommendation (~77.5 bits)',
                'ℹ️  Below AES-128 key strength (NIST post-quantum security category 1 baseline)'
            ]
        }

    else:
        return {
            'rating': 'MAXIMUM',
            'emoji': '💎',
            'description': f'Resistant to GPU farms for {time_desc.replace("in ", "")}',
            'warning': '✓ Quantum-resistant level - future-proof security',
            'recommendation': 'Ultimate security level',
            'standards': [
                '✓ At least AES-128 key strength (NIST post-quantum security category 1)',
                '✓ NIST: Grover\'s algorithm gives little or no practical advantage at this level'
            ]
        }


def calculate_crack_time(entropy: float, attempts_per_second: float = 1e15) -> str:
    """
    Calculate time required to crack password via brute force.
    Uses average case (50% of combinations need to be tried).
    Default GPU farm rate: 10^15 guesses/sec (fast hash such as MD5) (Futureproof rate calculation.
    Nowadays only state actors do operate such high computing power : ~5000 RTX 5090)
    """
    total_combinations = 2 ** entropy
    # On average, password found in half the attempts
    seconds = (total_combinations / 2) / attempts_per_second

    if seconds < 1:
        return "< 1 sec"
    elif seconds < 60:
        return f"{seconds:.1f} sec"
    elif seconds < 3600:
        return f"{seconds / 60:.1f} min"
    elif seconds < 86400:
        return f"{seconds / 3600:.1f} hours"
    elif seconds < 31536000:
        return f"{seconds / 86400:.1f} days"
    elif seconds < 31536000 * 1000:
        return f"{seconds / 31536000:.1f} years"
    elif seconds < 31536000 * 1000000:
        return f"{seconds / (31536000 * 1000):.1f}k years"
    else:
        return "NEVER (>1M years)"


def calculate_quantum_crack_time(entropy: float, quantum_speed: float = 1e7) -> str:
    """
    Calculate time to crack password using quantum computer with Grover's algorithm.

    Formula: T = (pi/4) * 2^(E/2) / S
    Grover's algorithm needs ~(pi/4)*sqrt(N) iterations to succeed with high probability.
    Unlike classical brute force there is no "on average half of the space" shortcut:
    the full iteration count must run before measuring.
    Note: Grover parallelizes poorly (p machines give only sqrt(p) speed-up),
    so a single fast quantum computer is assumed.
    """
    seconds = (math.pi / 4) * (2 ** (entropy / 2)) / quantum_speed

    if seconds < 1:
        return "< 1 sec"
    elif seconds < 60:
        return f"{seconds:.1f} sec"
    elif seconds < 3600:
        return f"{seconds / 60:.1f} min"
    elif seconds < 86400:
        return f"{seconds / 3600:.1f} hours"
    elif seconds < 31536000:
        return f"{seconds / 86400:.1f} days"
    elif seconds < 31536000 * 1000:
        return f"{seconds / 31536000:.1f} years"
    elif seconds < 31536000 * 1000000:
        return f"{seconds / (31536000 * 1000):.1f}k years"
    else:
        return "NEVER (>1M years)"



def check_length_policy(length: int) -> list[str]:
    """
    Check length against public standards.
    Length is the only password property NIST SP 800-63B-4 and OWASP ASVS 5.0 (6.2.1)
    regulate - they define no entropy levels and forbid composition rules.
    """
    if length >= 15:
        return [
            '✓ NIST SP 800-63B-4: 15+ characters (single-factor minimum)',
            '✓ OWASP ASVS 5.0 (6.2.1): meets the recommended 15 characters'
        ]
    elif length >= 8:
        return [
            '⚠️  NIST SP 800-63B-4: 8-14 characters allowed only as part of MFA (single-factor needs 15+)',
            '✓ OWASP ASVS 5.0 (6.2.1): meets the 8-character minimum (15+ strongly recommended)'
        ]
    else:
        return ['❌ NIST SP 800-63B-4 / OWASP ASVS 5.0: below the 8-character minimum']


def _print_strength_table(entropy: float, credential_type: str = "password", length: int = None) -> None:
    """
    Print security analysis table (internal helper function).
    Quantum crack time calculation (see calculate_quantum_crack_time)
        Formula: T = (pi/4) * 2^(E/2) / S
    where:
        T = time in seconds
        E = entropy in bits
        S = speed in operations/second (1e7 = 10 million ops/sec for 2030)
    """

    strength = rate_strength(entropy)

    # Calculate times for different scenarios
    online_rate = 7200 / 86400  # 7.2k attempts per day converted to per second
    gpu_farm_rate = 1e15  # 10^15 guesses/s
    quantum_speed = 1e7

    online_time = calculate_crack_time(entropy, online_rate)
    gpu_time = calculate_crack_time(entropy, gpu_farm_rate)
    quantum_time = calculate_quantum_crack_time(entropy, quantum_speed)

    # Table header
    print("\n" + "=" * 90)
    print(f"{" ":<12} ⚠️  SECURITY ANALYSIS - Crack Time Estimates (50% probability)")
    print("=" * 90)
    print(f"{'Strength':<20} {'Online Attack':<25} {'GPU Farm Attack':<25} {'Quantum (Future)':<25}")
    print(f"{'(Rating)':<20} {'(Rate: 7.2k/day)':<25} {'(10^15 guesses/s)':<25} {'(Grover\'s Algo.)':<25}")
    print("-" * 117)

    # Main data row
    rating_text = f"{strength['emoji']} {strength['rating']}"
    print(f"{rating_text:<20} {online_time:<25} {gpu_time:<25} {quantum_time:<25}")
    print("-" * 117)

    # Additional information
    print(f"\n📊 Entropy: {entropy:.2f} bits")
    print(f"💡 {strength['description']}")
    print(f"{strength['warning']}")
    print(f"📝 Recommendation: {strength['recommendation']}")

    # Special warnings based on entropy
    if entropy < 50:
        print(f"\n🚨 CRITICAL SECURITY WARNING:")
        print(f"   - This {credential_type} can be cracked in SECONDS by modern GPU farms!")
        print(f"   - If your database leaks, attackers will break it instantly")
        print(f"   - Minimum recommendation: Increase length (15+ characters or 6+ Diceware words)")
    elif entropy < 70:
        print(f"\n⚠️  SECURITY NOTICE:")
        print(f"   - This {credential_type} offers only moderate protection against offline attacks")
        print(f"   - GPU farms can still crack it in hours/days if database is leaked")
        print(f"   - Consider: Increase length (length matters more than character types)")
    elif entropy < 80:
        print(f"\n💡 SECURITY TIP:")
        print(f"   - Good {credential_type} strength for most uses")
        print(f"   - For critical accounts, consider even stronger credentials")

    # Reference points (entropy based)
    if strength['standards']:
        print(f"\n📚 Reference points:")
        for standard in strength['standards']:
            print(f"   {standard}")

    # Length policy (NIST SP 800-63B-4 / OWASP ASVS 5.0)
    if length is not None:
        print(f"\n🏛️  Standards (length {length} characters):")
        for line in check_length_policy(length):
            print(f"   {line}")

    print("=" * 117 + "\n")


def _get_password_preferences() -> tuple[bool, bool, bool, bool]:
    """
    Prompt user for password character type preferences.
    Requires at least 2 character types (tool design choice - NIST SP 800-63B-4
    and OWASP ASVS 5.0 set no composition rules; length matters more).
    """
    MIN_CHARSET_TYPES = 2

    while True:
        print("\nWhich characters do you want in the password?")
        use_uppercase = input("Uppercase letters (A-Z)? (y/n): ").lower() == "y"
        use_lowercase = input("Lowercase letters (a-z)? (y/n): ").lower() == "y"
        use_digits = input("Digits (0-9)? (y/n): ").lower() == "y"
        use_special = input("Special characters (!@#$...)? (y/n): ").lower() == "y"

        selected_count = sum([use_uppercase, use_lowercase, use_digits, use_special])

        if selected_count >= MIN_CHARSET_TYPES:
            return use_uppercase, use_lowercase, use_digits, use_special
        else:
            print(f"\n❌ You must select at least {MIN_CHARSET_TYPES} character types!")
            print(f"   Currently selected: {selected_count}")
            print("   Please try again...\n")


def _get_password_length() -> int:
    """
    Prompt user for password length with validation.
    """
    while True:
        try:
            length = int(input("What should the password length be? "))
            if length < 8:
                print("❌ Length must be at least 8!\n")
                continue
            return length
        except ValueError:
            print("❌ Please enter a number!\n")


def _get_num_words() -> int:
    """
    Prompt user for number of words with validation.

    Returns:
        Valid number of words (minimum 4)
    """
    while True:
        try:
            num_words = int(input("How many words should the passphrase have? "))
            if num_words < 4:
                print("❌ Number of words must be at least 4 (minimum security)!\n")
                continue
            if num_words > 10:
                print("⚠️  Warning: More than 10 words is quite long but very secure!\n")
            return num_words
        except ValueError:
            print("❌ Please enter a number!\n")


def _run_password_generator() -> None:
    """Run random password generation mode."""
    print("\n" + "🔑" * 20)
    print(f"{" ":<10}PASSWORD GENERATOR")
    print("🔑" * 20 + "\n")

    # Get user input
    length = _get_password_length()
    use_uppercase, use_lowercase, use_digits, use_special = _get_password_preferences()

    # Initialize generator and generate password
    try:
        generator = PasswordGenerator()
        password = generator.generate(
            length=length,
            use_uppercase=use_uppercase,
            use_lowercase=use_lowercase,
            use_digits=use_digits,
            use_special=use_special
        )

        # Calculate entropy
        charset_size = generator.get_charset_size(
            use_uppercase, use_lowercase, use_digits, use_special
        )
        entropy = evaluate_entropy(length, charset_size)

        # Display results


        print(f"Length: {length} characters")
        print(f"Charset size: {charset_size} characters")

        # Display strength table
        _print_strength_table(entropy, "password", length)

        text_line = f"✨ 🔐     YOUR PASSWORD:   {password}     🔐 ✨"
        line_length = len(text_line)
        num_keys = (line_length + 26) // 3  # Rozdělí délku, aby emojis odpovídaly

        print("\n" + "🔑" * num_keys)
        print(text_line)
        print("🔑" * num_keys + "\n")


    except Exception as e:
        print(f"❌ Error: {e}")


def _run_passphrase_generator() -> None:
    """Run Diceware passphrase generation mode."""
    print("\n" + "📖"  * 20)
    print(f"{" ":<10}PASSPHRASE GENERATOR")
    print("📖" * 20 + "\n")

    # Get user input
    num_words = _get_num_words()

    # Initialize generator and generate passphrase
    try:
        generator = DicewareGenerator()
        passphrase = generator.generate(num_words)

        # Calculate entropy
        entropy = evaluate_entropy(num_words, 7776)  # 7776 = 6^5

        print(f"Number of words: {num_words}")
        print(f"Wordlist size: 7776 words (EFF Large List)")
        print(f"Entropy per word: ~12.925 bits")

        # Display strength table
        _print_strength_table(entropy, "passphrase", len(passphrase))

        # Display Passphrase
        text_line = f"✨ 📚     YOUR PASSPHRASE:   {passphrase}     📚 ✨"
        line_length = len(text_line)
        num_emojis = (line_length  -6) //2

        print("\n" + "📖" * num_emojis)
        print(text_line)
        print("📖" * num_emojis + "\n")

    except FileNotFoundError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


def _run_password_checker() -> None:
    """Run password security analysis mode."""
    # ✅ IMPORTUJ AŽ TADY (v runtime, nikoliv na startu)
    from generators import PasswordChecker

    print("\n" + "🛡️" * 20)
    print(f"{" ":<10}PASSWORD SECURITY CHECKER")
    print("🛡️" * 20 + "\n")

    try:
        checker = PasswordChecker()
        results = checker.analyze_all()
        checker.print_analysis(results)

        # Summary statistics
        total = len(results)
        breached_count = sum(1 for r in results if r['hibp_breached'] is True)
        """
        print(f"\n📊 SUMMARY:")
        print(f"  Total passwords analyzed: {total}")
        print(f"  Breached passwords found: {breached_count}")

        if breached_count > 0:
            print(f"\n🚨 ACTION REQUIRED: {breached_count} password(s) have been found in known breaches!")
            print(f"   Recommend: Change these passwords immediately!")
        else:
            print(f"\n✓ Good news: No passwords found in known breaches (as of last check)")
        """
    except FileNotFoundError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


def main() -> None:
    """
    Main orchestrator function - displays menu and handles user choices.
    """
    print("=" * 50)
    print (f"🔐{' ':<18} \033[1m{'PASSMAN'}\033[0m")
    print(f"🔐 {' ':<10} PASSWORD SECURITY TOOLKIT")
    print("=" * 50)

    while True:
        print("\nSelect mode:")
        print("  1. Generate Random Password")
        print("  2. Generate Diceware Passphrase")
        print("  3. Check Password Security")
        print("  4. Exit")

        choice = input("\nEnter choice (1-4): ").strip()

        if choice == '1':
            _run_password_generator()
        elif choice == '2':
            _run_passphrase_generator()
        elif choice == '3':
            _run_password_checker()
        elif choice == '4':
            print("\nGoodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")

        again = input("\nContinue? (y/n): ").lower()
        if again != 'y':
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()
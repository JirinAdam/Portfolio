"""
Password & Passphrase Security Toolkit
Main module with orchestration and core analysis functions.
Import from generators/classes
"""

import math
from FinalProject.generators import PasswordGenerator
from FinalProject.generators import DicewareGenerato



def evaluate_entropy(length: int, charset_size: int) -> float:
    """
    Calculate theoretical entropy for password/passphrase.

    Entropy formula: length × log₂(charset_size)

    Args:
        length: Password length OR number of words in passphrase
        charset_size: Number of available characters OR 7776 (for Diceware)

    """
    if length < 1:
        raise ValueError("Length must be at least 1")
    if charset_size < 2:
        raise ValueError("Charset size must be at least 2")

    entropy = length * math.log2(charset_size)
    return entropy


def rate_strength(entropy: float) -> dict:
    """
    Rate password/passphrase strength based on entropy.

    Classification based on NIST/OWASP standards with emphasis on GPU farm attacks.

    Args:
        entropy: Password entropy in bits (float)

    """

    # Helper function for time description
    def _get_time_description(seconds: float) -> str:
        """Convert seconds to human-readable time description."""
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
    gpu_farm_rate = 1e15  # 1 PetaFLOPS
    total_combinations = 2 ** entropy
    seconds = (total_combinations / 2) / gpu_farm_rate
    time_desc = _get_time_description(seconds)

    # Rating logic based on entropy ranges
    if entropy < 32:
        return {
            'rating': 'CRITICAL',
            'emoji': '🔴',
            'description': f'Crackable by GPU farms {time_desc}',
            'warning': '🚨 CRITICAL: This password offers NO protection against modern attacks!',
            'recommendation': 'CHANGE IMMEDIATELY - Completely unsafe',
            'standards': []
        }

    elif entropy < 40:
        return {
            'rating': 'VERY WEAK',
            'emoji': '🟠',
            'description': f'Crackable by GPU farms {time_desc}',
            'warning': '⚠️  WARNING: Trivially crackable by automated tools',
            'recommendation': 'Not safe for any real use',
            'standards': [
                '⚠️  Below NIST AAL1 minimum',
                '✓ OWASP ASVS Level 1 (opportunistic only)'
            ]
        }

    elif entropy < 50:
        return {
            'rating': 'WEAK',
            'emoji': '🟡',
            'description': f'Crackable by GPU farms {time_desc}',
            'warning': '⚠️  Vulnerable to professional attackers with GPU resources',
            'recommendation': 'Use only for low-value, non-sensitive accounts',
            'standards': [
                '✓ NIST SP 800-63B AAL1 (basic authentication)',
                '⚠️  Below OWASP Level 2 minimum'
            ]
        }

    elif entropy < 63:
        return {
            'rating': 'MODERATE',
            'emoji': '🟢',
            'description': f'Crackable by GPU farms {time_desc}',
            'warning': '💡 Minimal protection - meets basic standards only',
            'recommendation': 'Consider increasing password length or character types',
            'standards': [
                '✓ NIST SP 800-63B AAL2 (lower bound)',
                '✓ OWASP ASVS Level 2 (minimum)'
            ]
        }

    elif entropy < 80:
        # GOOD/STRONG range - internal granularity
        if entropy < 70:
            rating_level = 'GOOD'
            emoji = '🔵'
            standards = [
                '✓ NIST SP 800-63B AAL2 (recommended)',
                '✓ OWASP ASVS Level 2 (compliant)'
            ]
        else:
            rating_level = 'STRONG'
            emoji = '💙'
            standards = [
                '✓ NIST SP 800-63B AAL2 (exceeds)',
                '✓ OWASP ASVS Level 2 (exceeds)',
                '✓ Approaching AAL3 threshold'
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
            'emoji': '🟣',
            'description': f'Resistant to GPU farms for {time_desc.replace("in ", "")}',
            'warning': '✓ Excellent protection - enterprise grade security',
            'recommendation': 'Excellent for sensitive/critical data',
            'standards': [
                '✓ NIST SP 800-63B AAL3 (high security)',
                '✓ OWASP ASVS Level 3 (high-security apps)',
                '✓ Beyond practical brute-force attacks'
            ]
        }

    elif entropy < 128:
        return {
            'rating': 'EXCEPTIONAL',
            'emoji': '💜',
            'description': f'Resistant to GPU farms for {time_desc.replace("in ", "")}',
            'warning': '✓ Maximum practical security for current threats',
            'recommendation': 'Exceeds all current standards',
            'standards': [
                '✓ NIST SP 800-63B AAL3 (far exceeds)',
                '✓ OWASP ASVS Level 3 (far exceeds)',
                '✓ Nation-state attack resistant',
                '⚠️  Still vulnerable to future quantum attacks'
            ]
        }

    else:
        return {
            'rating': 'MAXIMUM',
            'emoji': '⭐',
            'description': f'Resistant to GPU farms for {time_desc.replace("in ", "")}',
            'warning': '✓ Quantum-resistant level - future-proof security',
            'recommendation': 'Ultimate security level',
            'standards': [
                '✓ NIST SP 800-63B AAL3 (far exceeds)',
                '✓ OWASP ASVS Level 3 (far exceeds)',
                '✓ Post-quantum cryptography ready',
                '✓ Protected against Grover\'s algorithm'
            ]
        }


def calculate_crack_time(entropy: float, attempts_per_second: float = 1e15) -> str:
    """
    Calculate human-readable time required to crack password via brute force.

    Uses average case (50% of combinations need to be tried).
    Default GPU farm rate: 1 PetaFLOPS (1×10^15 attempts/sec)

    Args:
        entropy: Password entropy in bits (float)
        attempts_per_second: Cracking speed in attempts per second (default: 1e15 for GPU farm)


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


def _print_strength_table(entropy: float, credential_type: str = "password") -> None:
    """
    Print security analysis table (internal helper function).

    Args:
        entropy: Credential entropy in bits
        credential_type: "password" or "passphrase" (for display)
    """
    strength = rate_strength(entropy)

    # Calculate times for different scenarios
    online_rate = 7200 / 86400  # 7.2k attempts per day converted to per second
    gpu_farm_rate = 1e15  # 1 PetaFLOPS

    online_time = calculate_crack_time(entropy, online_rate)
    gpu_time = calculate_crack_time(entropy, gpu_farm_rate)
    quantum_time = calculate_crack_time(entropy / 2, gpu_farm_rate)  # Grover's effect

    # Table header
    print("\n" + "=" * 117)
    print("⚠️  SECURITY ANALYSIS - Crack Time Estimates (50% probability)")
    print("=" * 117)
    print(f"{'Strength':<20} {'Online Attack':<25} {'GPU Farm Attack':<25} {'Quantum (Future)':<25}")
    print(f"{'(Rating)':<20} {'(Rate: 7.2k/day)':<25} {'(1 PetaFLOPS)':<25} {'(Grover\'s Algo.)':<25}")
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
        print(f"   - Minimum recommendation: Increase length or character types")
    elif entropy < 70:
        print(f"\n⚠️  SECURITY NOTICE:")
        print(f"   - This {credential_type} meets minimum standards but could be stronger")
        print(f"   - GPU farms can still crack it in hours/days if database is leaked")
        print(f"   - Consider: Increase length or add character types")
    elif entropy < 80:
        print(f"\n💡 SECURITY TIP:")
        print(f"   - Good {credential_type} strength for most uses")
        print(f"   - For critical accounts, consider even stronger credentials")

    # Standards (if any)
    if strength['standards']:
        print(f"\n🏆 Compliance Status:")
        for standard in strength['standards']:
            print(f"   {standard}")

    print("=" * 117 + "\n")


def _get_password_preferences() -> tuple[bool, bool, bool, bool]:
    """
    Prompt user for password character type preferences.
    Requires at least 2 character types (industry standard).
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
            print(f"\n❌ You must select at least {MIN_CHARSET_TYPES} character types (industry standard)!")
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
    print("          PASSWORD GENERATOR")
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
        _print_strength_table(entropy, "password")

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
    print("          PASSPHRASE GENERATOR")
    print("📖" * 20 + "\n")

    # Get user input
    num_words = _get_num_words()

    # Initialize generator and generate passphrase
    try:
        generator = DicewareGenerator('eff_largelist.csv')
        passphrase = generator.generate(num_words)

        # Calculate entropy
        entropy = evaluate_entropy(num_words, 7776)  # 7776 = 6^5

        print(f"Number of words: {num_words}")
        print(f"Wordlist size: 7776 words (EFF Large List)")
        print(f"Entropy per word: ~12.925 bits")

        # Display strength table
        _print_strength_table(entropy, "passphrase")

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
    print("\n" + "=" * 50)
    print("PASSWORD SECURITY CHECKER")
    print("=" * 50 + "\n")

    try:
        checker = PasswordChecker()
        results = checker.analyze_all()
        checker.print_analysis(results)

        # Summary statistics
        total = len(results)
        breached_count = sum(1 for r in results if r['hibp_breached'] is True)

        print(f"\n📊 SUMMARY:")
        print(f"  Total passwords analyzed: {total}")
        print(f"  Breached passwords found: {breached_count}")

        if breached_count > 0:
            print(f"\n🚨 ACTION REQUIRED: {breached_count} password(s) have been found in known breaches!")
            print(f"   Recommend: Change these passwords immediately!")
        else:
            print(f"\n✓ Good news: No passwords found in known breaches (as of last check)")

    except FileNotFoundError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


def main() -> None:

    # Main orchestrator function - displays menu and handles user choices.
    
    print("=" * 50)
    print("🔐 PASSWORD SECURITY TOOLKIT")
    print("=" * 50)

    while True:
        print("\nSelect mode:")
        print("  1. Generate Random Password")
        print("  2. Generate Diceware Passphrase")
        print("  3. Exit")

        choice = input("\nEnter choice (1-3): ").strip()

        if choice == '1':
            _run_password_generator()
        elif choice == '2':
            _run_passphrase_generator()
        elif choice == '3':
            print("\nGoodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

        again = input("\nShall we return to the main menu? (y/n): ").lower()
        if again != 'y':
            print("Goodbye!")
            break

if __name__ == "__main__":
    main()

"""Functional version for separated use only"""
import secrets
import string
import math


def generate_password(length: int, use_uppercase: bool, use_lowercase: bool,
                      use_digits: bool, use_special: bool) -> str:
    """
    Generate a random password based on specified criteria.

    Args:
        length: Password length
        use_uppercase: Include uppercase letters
        use_lowercase: Include lowercase letters
        use_digits: Include digits
        use_special: Include special characters

    Returns:
        Randomly generated password
    """
    # Build character set
    charset = ""
    if use_uppercase:
        charset += string.ascii_uppercase
    if use_lowercase:
        charset += string.ascii_lowercase
    if use_digits:
        charset += string.digits
    if use_special:
        charset += string.punctuation

    # Generate password
    return "".join(secrets.choice(charset) for _ in range(length))


def calculate_charset_size(use_uppercase: bool, use_lowercase: bool,
                           use_digits: bool, use_special: bool) -> int:
    """
    Calculate the total character set size based on selected categories.

    Args:
        use_uppercase: Include uppercase letters
        use_lowercase: Include lowercase letters
        use_digits: Include digits
        use_special: Include special characters

    Returns:
        Total number of available characters
    """
    size = 0
    if use_uppercase:
        size += len(string.ascii_uppercase)
    if use_lowercase:
        size += len(string.ascii_lowercase)
    if use_digits:
        size += len(string.digits)
    if use_special:
        size += len(string.punctuation)
    return size


def rate_password_strength(effective_entropy):
    """
    Ohodnotí sílu hesla s důrazem na offline útoky (GPU farms).

    Rating se určuje podle NIST/OWASP standardů.
    Description se dynamicky mění podle skutečného GPU farm času.
    """
    # Vypočítej skutečný GPU farm čas pro description
    gpu_farm_rate = 1e15  # 1 PetaFLOPS
    total_combinations = 2 ** effective_entropy
    seconds = (total_combinations / 2) / gpu_farm_rate

    # Funkce pro určení časového popisu
    def get_time_description(secs):
        if secs < 1:
            return "instantly (< 1 second)"
        elif secs < 60:
            return f"in seconds ({secs:.1f} sec)"
        elif secs < 3600:
            return f"in minutes ({secs / 60:.1f} min)"
        elif secs < 86400:
            return f"in hours ({secs / 3600:.1f} hours)"
        elif secs < 604800:  # 7 days
            return f"in days ({secs / 86400:.1f} days)"
        elif secs < 2592000:  # 30 days
            return f"in weeks ({secs / 604800:.1f} weeks)"
        elif secs < 31536000:  # 1 year
            return f"in months ({secs / 2592000:.1f} months)"
        elif secs < 31536000 * 100:  # 100 years
            return f"in years ({secs / 31536000:.1f} years)"
        elif secs < 31536000 * 10000:  # 10k years
            return f"in centuries ({secs / (31536000 * 100):.1f} centuries)"
        elif secs < 31536000 * 1000000:  # 1M years
            return f"in millennia ({secs / (31536000 * 1000):.1f} millennia)"
        else:
            return "beyond geological timescales (>1M years)"

    time_desc = get_time_description(seconds)

    # Rating podle entropy ranges
    if effective_entropy < 32:
        return {
            'rating': 'CRITICAL',
            'emoji': '🔴',
            'description': f'Crackable by GPU farms {time_desc}',
            'warning': '🚨 CRITICAL: This password offers NO protection against modern attacks!',
            'recommendation': 'CHANGE IMMEDIATELY - Completely unsafe',
            'standards': []
        }

    elif effective_entropy < 40:
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

    elif effective_entropy < 50:
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

    elif effective_entropy < 63:
        return {
            'rating': 'MODERATE',
            'emoji': '🟢',
            'description': f'Crackable by GPU farms {time_desc}',
            'warning': '💡 Minimal protection - meets basic standards only',
            'recommendation': 'Consider increasing to 12+ characters',
            'standards': [
                '✓ NIST SP 800-63B AAL2 (lower bound)',
                '✓ OWASP ASVS Level 2 (minimum)'
            ]
        }

    elif effective_entropy < 80:
        # GOOD/STRONG range - internal granularity
        if effective_entropy < 70:
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

    elif effective_entropy < 100:
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

    elif effective_entropy < 128:
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


def calculate_crack_time(entropy, attempts_per_second):
    """
    Vypočítá čas potřebný k prolomení hesla.

    Args:
        entropy: Entropie hesla v bitech
        attempts_per_second: Počet pokusů za sekundu

    Returns:
        Formátovaný string s časem
    """
    total_combinations = 2 ** entropy
    # Průměrně se najde v polovině pokusů
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


def print_strength_table(entropy):
    """
    Vytiskne tabulku s důrazem na reálné hrozby.

    Args:
        entropy: Entropie hesla v bitech
    """
    strength = rate_password_strength(entropy)

    # Výpočet časů pro různé scénáře
    online_rate = 7200 / 86400  # 7.2k attempts per day converted to per second
    gpu_farm_rate = 1e15  # 1 PetaFLOPS

    online_time = calculate_crack_time(entropy, online_rate)
    gpu_time = calculate_crack_time(entropy, gpu_farm_rate)
    quantum_time = calculate_crack_time(entropy / 2, gpu_farm_rate)  # Grover efekt

    # Hlavička tabulky
    print("\n" + "=" * 117)
    print("⚠️  SECURITY ANALYSIS - Crack Time Estimates (50% probability)")
    print("=" * 117)
    print(f"{'Strength':<20} {'Online Attack':<25} {'GPU Farm Attack':<25} {'Quantum (Future)':<25}")
    print(f"{'(Rating)':<20} {'(Rate: 7.2k/day)':<25} {'(1 PetaFLOPS)':<25} {'(Grover\'s Algo.)':<25}")
    print("-" * 117)

    # Hlavní řádek s daty
    rating_text = f"{strength['emoji']} {strength['rating']}"
    print(f"{rating_text:<20} {online_time:<25} {gpu_time:<25} {quantum_time:<25}")
    print("-" * 117)

    # Doplňující informace
    print(f"\n📊 Entropy: {entropy:.2f} bits")
    print(f"💡 {strength['description']}")
    print(f"{strength['warning']}")
    print(f"📝 Recommendation: {strength['recommendation']}")

    # Speciální varování podle entropy
    if entropy < 50:
        print(f"\n🚨 CRITICAL SECURITY WARNING:")
        print(f"   - This password can be cracked in SECONDS by modern GPU farms!")
        print(f"   - If your password database leaks, attackers will break it instantly")
        print(f"   - Minimum recommendation: 12 characters with mixed types")
        print(f"   - Better: 16+ characters (passphrases are easier to remember)")
    elif entropy < 70:
        print(f"\n⚠️  SECURITY NOTICE:")
        print(f"   - This password meets minimum standards but could be stronger")
        print(f"   - GPU farms can still crack it in hours if database is leaked")
        print(f"   - Consider: 14+ characters for better long-term security")
    elif entropy < 80:
        print(f"\n💡 SECURITY TIP:")
        print(f"   - Good password strength for most uses")
        print(f"   - For critical accounts (banking, email), consider 16+ characters")

    # Standardy (pokud existují)
    if strength['standards']:
        print(f"\n🏆 Compliance Status:")
        for standard in strength['standards']:
            print(f"   {standard}")

    print("=" * 117 + "\n")


def evaluate_password_strength(length: int, charset_size: int) -> None:
    """
    Evaluate password strength based on entropy.

    Entropy = log2(N^L), where:
    - N = alphabet size (number of available characters)
    - L = password length

    Args:
        length: Password length
        charset_size: Size of character set used
    """
    entropy = length * math.log2(charset_size)

    print(f"Length: {length} characters")
    print(f"Charset size: {charset_size} characters")

    # Nahrazení původního outputu tabulkou
    print_strength_table(entropy)


def get_password_length() -> int:
    """
    Prompt user for password length with validation.

    Returns:
        Valid password length (minimum 8)
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


def get_character_preferences() -> tuple[bool, bool, bool, bool]:
    """
    Prompt user for character type preferences.
    Requires at least 2 character types (industry standard).

    Returns:
        Tuple of (use_uppercase, use_lowercase, use_digits, use_special)
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


def main():
    """Main function to run the password generator."""
    print("=" * 50)
    print("PASSWORD GENERATOR")
    print("=" * 50 + "\n")

    # Get user input
    length = get_password_length()
    use_uppercase, use_lowercase, use_digits, use_special = get_character_preferences()

    # Calculate charset size
    charset_size = calculate_charset_size(use_uppercase, use_lowercase,
                                          use_digits, use_special)

    # Generate password
    password = generate_password(length, use_uppercase, use_lowercase,
                                 use_digits, use_special)

    print("\n" + "=" * 50)
    print(f"Your password: {password}")
    print("=" * 50 + "\n")

    # Evaluate strength
    evaluate_password_strength(length, charset_size)


if __name__ == "__main__":
    main()
"""Functional version for separated use only"""
import secrets
import csv
import math
from pathlib import Path


def load_wordlist(csv_file='eff_largelist.csv'):
    """
    Load EFF Large List from CSV file.

    Args:
        csv_file: Path to CSV file with EFF Large List

    Returns:
        Dictionary mapping dice rolls to words
    """
    wordlist = {}
    filepath = Path(csv_file)

    if not filepath.exists():
        raise FileNotFoundError(
            f"File '{csv_file}' not found.\n"
            f"Download EFF Large List from: https://www.eff.org/files/2016/07/18/eff_large_wordlist.txt\n"
            f"Convert to CSV: index,word\n"
            f"Save as: {csv_file}"
        )

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 2:
                index, word = row
                wordlist[index] = word.strip().lower()

    return wordlist


def roll_five_dice():
    """
    Simulate 5 dice rolls (1-6).

    Returns:
        String with 5 digits like '23415'
    """
    rolls = []
    for _ in range(5):
        roll = secrets.randbelow(6) + 1  # 1-6
        rolls.append(str(roll))
    return "".join(rolls)


def get_word_from_roll(dice_roll, wordlist):
    """
    Get word from wordlist for given dice roll.

    Args:
        dice_roll: String like '23415'
        wordlist: Dictionary of words

    Returns:
        Word from EFF Large List
    """
    return wordlist.get(dice_roll, "[ERROR: Index not found]")


def generate_passphrase(num_words, wordlist, separator=" "):
    """
    Generate Diceware passphrase.

    Args:
        num_words: Number of words
        wordlist: Dictionary of words from EFF list
        separator: Word separator (default: space)

    Returns:
        Generated passphrase string
    """
    if num_words < 1:
        raise ValueError("Number of words must be at least 1")

    words = []
    for _ in range(num_words):
        dice = roll_five_dice()
        word = get_word_from_roll(dice, wordlist)
        words.append(word)

    return separator.join(words)


def calculate_passphrase_entropy(num_words):
    """
    Calculate theoretical entropy for Diceware passphrase.

    Each word from EFF Large List (7776 words) provides log2(7776) ≈ 12.925 bits

    Args:
        num_words: Number of words in passphrase

    Returns:
        Entropy in bits
    """
    wordlist_size = 7776  # 6^5 combinations
    entropy_per_word = math.log2(wordlist_size)
    return num_words * entropy_per_word


def calculate_crack_time(entropy, attempts_per_second):
    """
    Calculate time required to crack password.

    Args:
        entropy: Password entropy in bits
        attempts_per_second: Number of attempts per second

    Returns:
        Formatted string with time estimate
    """
    total_combinations = 2 ** entropy
    # On average, found in half the attempts
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


def rate_password_strength(effective_entropy):
    """
    Rate password strength with emphasis on offline attacks (GPU farms).

    Rating is determined by NIST/OWASP standards.
    Description dynamically changes based on actual GPU farm cracking time.

    Args:
        effective_entropy: Password entropy in bits

    Returns:
        Dictionary containing rating, emoji, description, warning, recommendation, and standards
    """
    # Calculate actual GPU farm time for description
    gpu_farm_rate = 1e15  # 1 PetaFLOPS
    total_combinations = 2 ** effective_entropy
    seconds = (total_combinations / 2) / gpu_farm_rate

    # Helper function to determine time description
    def get_time_description(secs):
        """Convert seconds to human-readable time description."""
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

    # Rating based on entropy ranges
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
            'recommendation': 'Consider increasing to 6+ words',
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


def print_strength_table(entropy):
    """
    Print strength analysis table with emphasis on real threats.

    Args:
        entropy: Passphrase entropy in bits
    """
    strength = rate_password_strength(entropy)

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
        print(f"   - This passphrase can be cracked in SECONDS by modern GPU farms!")
        print(f"   - If your password database leaks, attackers will break it instantly")
        print(f"   - Minimum recommendation: 5+ words")
        print(f"   - Better: 6+ words for adequate security")
    elif entropy < 70:
        print(f"\n⚠️  SECURITY NOTICE:")
        print(f"   - This passphrase meets minimum standards but could be stronger")
        print(f"   - GPU farms can still crack it in hours/days if database is leaked")
        print(f"   - Consider: 6+ words for better long-term security")
    elif entropy < 80:
        print(f"\n💡 SECURITY TIP:")
        print(f"   - Good passphrase strength for most uses")
        print(f"   - For critical accounts (banking, email), consider 7+ words")

    # Standards (if any)
    if strength['standards']:
        print(f"\n🏆 Compliance Status:")
        for standard in strength['standards']:
            print(f"   {standard}")

    print("=" * 117 + "\n")


def evaluate_passphrase_strength(num_words):
    """
    Evaluate passphrase strength based on entropy.

    Diceware entropy = num_words × log2(7776)

    Args:
        num_words: Number of words in passphrase
    """
    entropy = calculate_passphrase_entropy(num_words)

    print(f"Number of words: {num_words}")
    print(f"Wordlist size: 7776 words (EFF Large List)")
    print(f"Entropy per word: ~12.925 bits")

    # Use same table as password generator
    print_strength_table(entropy)


def get_num_words():
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
                print("⚠️  Warning: More than 10 words is quite long but very secure!")
            return num_words
        except ValueError:
            print("❌ Please enter a number!\n")


def main():
    """Main function to run the passphrase generator."""
    print("=" * 50)
    print("PASSPHRASE GENERATOR")
    print("=" * 50 + "\n")

    # Load wordlist
    try:
        wordlist = load_wordlist('eff_largelist.csv')
        print(f"✓ EFF Large List loaded: {len(wordlist)} words\n")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return

    # Get user input
    num_words = get_num_words()

    # Generate passphrase
    passphrase = generate_passphrase(num_words, wordlist)

    print("\n" + "=" * 50)
    print(f"Your passphrase: {passphrase}")
    print("=" * 50 + "\n")

    # Evaluate strength (same output as password generator)
    evaluate_passphrase_strength(num_words)


if __name__ == "__main__":
    main()
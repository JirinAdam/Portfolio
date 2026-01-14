"""
DICEWARE PASSPHRASE GENERATOR - EFF Large List
Method: 5 dice rolls (11111-66666) → 7776 words

Usage:
  python diceware_eff.py
  python diceware_eff.py --words 6
  python diceware_eff.py --words 8
"""

import secrets
import csv
import sys
from pathlib import Path


class DicewareGenerator:
    """Diceware Passphrase generator from EFF Large List."""

    def __init__(self, csv_file='eff_largelist.csv'):
        """
        Initialize generator and load dictionary from CSV.

        Args:
            csv_file: Path to CSV file with EFF Large List
        """
        self.csv_file = Path(csv_file)
        self.wordlist = {}
        self._load_wordlist()

    def _load_wordlist(self):
        """Load EFF Large List from CSV file."""
        if not self.csv_file.exists():
            raise FileNotFoundError(
                f"File '{self.csv_file}' not found.\n"
                f"Download EFF Large List from: https://www.eff.org/files/2016/07/18/eff_large_wordlist.txt\n"
                f"Convert to CSV: index,word\n"
                f"Save as: {self.csv_file}"
            )

        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 2:
                    index, word = row
                    self.wordlist[index] = word.strip().lower()

        print(f"✓ EFF Large List loaded: {len(self.wordlist)} words")

    def roll_five_dice(self) -> str:
        """
        Simulates 5 dice rolls (1-6).
        Returns string '11111' to '66666'.

        Returns:
            String with 5 digits (1-6 each)
        """
        rolls = []
        for _ in range(5):
            roll = secrets.randbelow(6) + 1  # 1-6
            rolls.append(str(roll))

        return "".join(rolls)

    def get_word(self, dice_roll: str) -> str:
        """
        Returns word from dictionary for given dice roll.

        Args:
            dice_roll: String like '23415'

        Returns:
            Word from EFF Large List
        """
        if dice_roll not in self.wordlist:
            # Fallback - if index is not exactly in list
            return "[ERROR: Index not found]"

        return self.wordlist[dice_roll]

    def generate_passphrase(self, num_words: int = 7, verbose: bool = True) -> str:
        """
        Generate Diceware Passphrase.

        Args:
            num_words: Number of words (recommended 4-7)
            verbose: Print process details

        Returns:
            Passphrase as "word1 word2 word3 ..."
        """
        if num_words < 1:
            raise ValueError("Number of words must be at least 1")

        if num_words > 20:
            print(f"⚠️  Warning: {num_words} words is quite long!")

        if verbose:
            print(f"\n{'=' * 70}")
            print(f"GENERATING DICEWARE PASSPHRASE ({num_words} words)")
            print(f"{'=' * 70}\n")

        words = []

        for i in range(num_words):
            # Roll 5 dice
            dice = self.roll_five_dice()

            # Word lookup
            word = self.get_word(dice)
            words.append(word)

            if verbose:
                print(f"  Word {i + 1}: Rolls={dice} → '{word}'")

        passphrase = " ".join(words)

        if verbose:
            # Simple entropy information
            import math
            entropy = num_words * math.log2(7776)
            print(f"\n{'-' * 70}")
            print(f"Generated Passphrase:")
            print(f"  '{passphrase}'")
            print(f"\nEntropy: {num_words} × log₂(7776) ≈ {entropy:.1f} bits")
            print(f"{'=' * 70}\n")

        return passphrase


def main():
    """Main function to run the passphrase generator."""
    print("=" * 50)
    print("PASSPHRASE GENERATOR")
    print("=" * 50 + "\n")

    # Argument parsing
    num_words = 6

    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            print("""
Diceware Passphrase Generator - EFF Large List

USAGE:
  python diceware_eff.py              # 6 words (default)
  python diceware_eff.py --words 7    # 7 words
  python diceware_eff.py --words 8    # 8 words
  python diceware_eff.py --help       # Help

RECOMMENDATIONS:
  4 words  = 51.8 bits (⚠️ Very Poor)
  5 words  = 64.8 bits (Good start - NIST Standard Minimum)
  6 words  = 77.7 bits (✅ Good Standard) ← Recommended for convenience 
  7 words  = 90.6 bits (✅ STRONG)
  8 words  = 103.4 bits (✅ ✅ VERY Strong) 
  9 words  = 116.3 bits (✅ ✅ ✅ High Security)
  10 words = 129.2 bits (🔐 Quantum ready) 


EFF LARGE LIST:
  7776 words (6^5 combinations)
  Download: https://www.eff.org/files/2016/07/18/eff_large_wordlist.txt
            """)
            return

        if sys.argv[1] == '--words' and len(sys.argv) > 2:
            try:
                num_words = int(sys.argv[2])
            except ValueError:
                print("❌ Error: Number of words must be a number")
                return

    # Execution
    try:
        generator = DicewareGenerator('eff_largelist.csv')
        passphrase = generator.generate_passphrase(num_words=num_words, verbose=True)

        # Output
        print(f"✓ Passphrase generated successfully!")
        print(f"\n🔐 Your secure passphrase:")
        print(f"   {passphrase}")
        print(f"\n💡 Tip: Memorize it or store it securely")

    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
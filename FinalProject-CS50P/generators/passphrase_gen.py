"""
Diceware Passphrase Generator Class
Generates passphrases using EFF Large Word List.
"""

import secrets
import csv
import math
from pathlib import Path


class DicewareGenerator:
    """
    Diceware passphrase generator using EFF Large Word List.

    Method: 5 dice rolls (11111-66666) → 7776 words

    Attributes:
        wordlist (dict): Mapping of dice rolls to words
        WORDLIST_SIZE (int): Number of words in EFF list (7776)
        ENTROPY_PER_WORD (float): Bits of entropy per word (~12.925)
    """

    WORDLIST_SIZE = 7776  # 6^5
    ENTROPY_PER_WORD = math.log2(7776)  # ~12.925 bits

    def __init__(self, wordlist_file: str = 'eff_largelist.csv'):
        """
        Initialize generator and load wordlist.

        """
        self.wordlist_file = Path(wordlist_file)
        self.wordlist = {}
        self._load_wordlist()

    def _load_wordlist(self) -> None:
        """
        Load EFF Large Word List from CSV file.

        CSV format should be: index,word

        """
        if not self.wordlist_file.exists():
            raise FileNotFoundError(
                f"File '{self.wordlist_file}' not found.\n"
                f"Download EFF Large List from:\n"
                f"https://www.eff.org/files/2016/07/18/eff_large_wordlist.txt\n"
                f"Convert to CSV format: index,word\n"
                f"Save as: {self.wordlist_file}"
            )

        with open(self.wordlist_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 2:
                    index, word = row
                    self.wordlist[index] = word.strip().lower()

        print(f"✓ EFF Large List loaded: {len(self.wordlist)} words")

    def _roll_dice(self, num_dice: int = 5) -> str:
        """
        Simulate multiple dice rolls (1-6). Default 5
        """
        return "".join(str(secrets.randbelow(6) + 1) for _ in range(num_dice))

    def _get_word(self, dice_roll: str) -> str:
        """
        Get word from wordlist for given dice roll.

        """
        return self.wordlist.get(dice_roll, "[ERROR: Index not found]")

    def generate(self, num_words: int = 6, separator: str = " ") -> str:
        """
        Generate Diceware passphrase.

        Process:
        1. For each word, roll 5 dice
        2. Use dice result as index to lookup word
        3. Combine words with separator

        """
        if num_words < 1:
            raise ValueError("Number of words must be at least 1")

        words = []
        for _ in range(num_words):
            dice = self._roll_dice()
            word = self._get_word(dice)
            words.append(word)

        return separator.join(words)
"""
Password Generator Class
"""

import secrets
import string


class PasswordGenerator:
    """
    Generate random passwords with configurable character sets.

    """

    CHARSET_TYPES = ('uppercase', 'lowercase', 'digits', 'special')
    SPECIAL_CHARS = '^*%$!&@#'

    def __init__(self):
        """Initialize with standard character set sizes."""
        self.charset_sizes = {
            'uppercase': len(string.ascii_uppercase),  # 26
            'lowercase': len(string.ascii_lowercase),  # 26
            'digits': len(string.digits),  # 10
            'special': len(self.SPECIAL_CHARS)  # 8
        }

    def get_charset_size(self, use_uppercase: bool = True,
                         use_lowercase: bool = True,
                         use_digits: bool = True,
                         use_special: bool = True) -> int:
        """
        Calculate total character set size based on selections.

        """
        size = 0
        if use_uppercase:
            size += self.charset_sizes['uppercase']
        if use_lowercase:
            size += self.charset_sizes['lowercase']
        if use_digits:
            size += self.charset_sizes['digits']
        if use_special:
            size += self.charset_sizes['special']
        return size

    def _build_charset(self, use_uppercase: bool = True,
                       use_lowercase: bool = True,
                       use_digits: bool = True,
                       use_special: bool = True) -> str:
        """
        Build character set string based on selections.

        """
        charset = ""
        if use_uppercase:
            charset += string.ascii_uppercase
        if use_lowercase:
            charset += string.ascii_lowercase
        if use_digits:
            charset += string.digits
        if use_special:
            charset += self.SPECIAL_CHARS
        return charset

    def generate(self, length: int = 12, use_uppercase: bool = True,
                 use_lowercase: bool = True, use_digits: bool = True,
                 use_special: bool = True) -> str:
        """
        Generate random password based on specified criteria.
        """
        charset = self._build_charset(use_uppercase, use_lowercase,
                                      use_digits, use_special)
        password = ''.join(secrets.choice(charset) for _ in range(length))
        return password

"""
Generators package - Export all public classes and functions.
"""

from .password_gen import PasswordGenerator
from .passphrase_gen import DicewareGenerator
from .password_checker import PasswordChecker

# Import core functions from main module for reuse
import sys
from pathlib import Path

# Přidej parent directory do path aby se importoval main
main_dir = Path(__file__).parent.parent
sys.path.insert(0, str(main_dir))

from FinalProject.project import evaluate_entropy, rate_strength, calculate_crack_time

__all__ = ['PasswordGenerator','DicewareGenerator','PasswordChecker','evaluate_entropy','rate_strength','calculate_crack_time']
# 🔐 Password & Passphrase Security Toolkit

#### Video Demo: <https://youtu.be/X8-mPKOeXGY>

#### Description:

The **Password & Passphrase Security Toolkit** is a comprehensive command-line application designed to help users generate secure passwords, create memorable passphrases, and analyze the security of their existing credentials. This project was developed as a final project for CS50, combining cryptographic principles with practical security assessment tools.

## 🎯 Project Overview

In today's digital world, password security is paramount. This toolkit addresses three critical needs:

1. **Generating cryptographically secure random passwords** with customizable character sets.
2. **Creating memorable Diceware passphrases** using the EFF Large Word List.
3. **Analyzing existing passwords** for strength and checking against known data breaches.

The application calculates **entropy** (a measure of password randomness) and provides detailed security assessments based on industry standards including **NIST SP 800-63B** and **OWASP ASVS**.

## 📁 Project Structure
FinalProject/
├── project.py # Main orchestration module
├── passwords.csv # User's passwords for analysis
├── test_project.py # Comprehensive pytest test suite
├── eff_largelist.csv # EFF Diceware word list (7776 words)
├── generators/
│ ├── init.py # Package exports
│ ├── password_gen.py # Random password generator class
│ ├── passphrase_gen.py # Diceware passphrase generator class
│ └── password_checker.py # Password analyzer with HIBP integration
├── requirements.txt # Project dependencies
└── README.md # This file

## 📄 File Descriptions

### `project.py`

The main module serving as the application's entry point. It contains the core orchestration logic and reusable analysis functions:
- **`evaluate_entropy`**: Calculates bits via the formula length × log₂(charset_size).
- **`rate_strength`**: Classifies strength into 9 categories based on entropy thresholds.
- **`calculate_crack_time`**: Estimates brute-force resistance against various attack speeds.

**Design Decision:** I chose to centralize all entropy and rating logic here to maintain a single source of truth. The generator and checker classes import these functions rather than reimplementing them, strictly following the **DRY (Don't Repeat Yourself)** principle.

### `generators/password_gen.py`

Contains the `PasswordGenerator` class. It allows for customizable character sets (uppercase, lowercase, digits, symbols) and enforces a minimum of two character types.

**Design Decision:** I debated # 🔐 Password & Passphrase Security Toolkit

#### Video Demo: <URL_HERE>

#### Description:

The **Password & Passphrase Security Toolkit** is a comprehensive command-line application designed to help users generate secure passwords, create memorable passphrases, and analyze the security of their existing credentials. This project was developed as a final project for CS50, combining cryptographic principles with practical security assessment tools.

## 🎯 Project Overview

In today's digital world, password security is paramount. This toolkit addresses three critical needs:

1. **Generating cryptographically secure random passwords** with customizable character sets.
2. **Creating memorable Diceware passphrases** using the EFF Large Word List.
3. **Analyzing existing passwords** for strength and checking against known data breaches.

The application calculates **entropy** (a measure of password randomness) and provides detailed security assessments based on industry standards including **NIST SP 800-63B** and **OWASP ASVS**.

## 📁 Project Structure
FinalProject/
├── project.py # Main orchestration module
├── passwords.csv # User's passwords for analysis
├── test_project.py # Comprehensive pytest test suite
├── eff_largelist.csv # EFF Diceware word list (7776 words)
├── generators/
│ ├── init.py # Package exports
│ ├── password_gen.py # Random password generator class
│ ├── passphrase_gen.py # Diceware passphrase generator class
│ └── password_checker.py # Password analyzer with HIBP integration
├── requirements.txt # Project dependencies
└── README.md # This file

## 📄 File Descriptions

### `project.py`

The main module serving as the application's entry point. It contains the core orchestration logic and reusable analysis functions:
- **`evaluate_entropy`**: Calculates bits via the formula length × log₂(charset_size).
- **`rate_strength`**: Classifies strength into 9 categories based on entropy thresholds.
- **`calculate_crack_time`**: Estimates brute-force resistance against various attack speeds.

**Design Decision:** I chose to centralize all entropy and rating logic here to maintain a single source of truth. The generator and checker classes import these functions rather than reimplementing them, strictly following the **DRY (Don't Repeat Yourself)** principle.

### `generators/password_gen.py`

Contains the `PasswordGenerator` class. It allows for customizable character sets (uppercase, lowercase, digits, symbols) and enforces a minimum of two character types.

**Design Decision:** I debated between using the standard `random` library versus `secrets`. I chose `secrets` because it provides access to the operating system's most secure source of randomness, which is critical for cryptographic applications, whereas `random` is deterministic and unsuitable for security.

### `generators/passphrase_gen.py`

Contains the `DicewareGenerator` class. It utilizes the EFF Large Word List (7,776 words) to create passphrases. Each word adds ~12.9 bits of entropy. The Diceware method was selected because it balances high security with memorability; a 6-word passphrase (~77.5 bits) is stronger than complex 12-character passwords but significantly easier for humans to recall.

### `generators/password_checker.py`

This module handles the analysis of existing credentials loaded from `passwords.csv`. It calculates local entropy metrics and integrates with the **Have I Been Pwned (HIBP)** API.

**Design Decision:** Privacy was a priority. I implemented the **k-Anonymity** model for the API integration. The tool hashes passwords using SHA-1 and sends only the first 5 characters of the hash to the API. This ensures the user's actual passwords are never transmitted over the network.

### `tests/test_project.py`

A comprehensive test suite using `pytest`. It includes unit tests for all mathematical functions, boundary checks for entropy ratings (e.g., ensuring 49.9 bits is treated differently than 50.0), and mock-based integration tests for user input and API responses.

## 🔧 Technical Implementation

### Entropy Calculation

Password entropy is calculated as:

$$E = L \times \log_2(C)$$

Where **E** is entropy in bits, **L** is length, and **C** is the pool of unique characters available.

### Strength Classification

| Entropy (bits) | Rating | Recommendation |
|---|---|---|
| < 32 | CRITICAL | Change immediately |
| 32-50 | VERY WEAK / WEAK | Low-value accounts only |
| 50-70 | MODERATE / GOOD | Standard use |
| 70-100 | STRONG / VERY STRONG | Sensitive data |
| 100+ | EXCEPTIONAL | Quantum-resistant |

### Attack Scenarios

The toolkit estimates crack times based on three threat models:
1. **Online Attack**: 7,200 attempts/day (simulating aggressive rate-limiting). (T = (2^E / 2) / S)
2. **GPU Farm**: 1 PetaFLOPS (10¹⁵ attempts/second). (Futureproof rate calculation.
    Nowadays only state actors do operate such high computing power : ~5000 RTX 5090)  (T = (2^E / 2) / S)
3. **Quantum**: Simulates Grover's algorithm, effectively halving the bit strength. (  T = 2^(E/2) / S)

### Used sources

**Secrets library**: https://docs.python.org/3/library/secrets.html  
**EFF Dice-generated passphrase**: https://www.eff.org/dice  
**OWASP CHEat Sheet**: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html  
**NIST Standard**: https://pages.nist.gov/800-63-3/sp800-63b.html  
**Quantum Computing for dummies**: https://spectrum.ieee.org/quantum-computing-for-dummies  
**Hive System Crack-time tables**: https://www.hivesystems.com/blog/are-your-passwords-in-the-green
 
## 🚀 Usage

```bash  
# Run the main program  
python project.py  

# Run tests  
pytest test_project.py -v  between using the standard `random` library versus `secrets`. I chose `secrets` because it provides access to the operating system's most secure source of randomness, which is critical for cryptographic applications, whereas `random` is deterministic and unsuitable for security.

### `generators/passphrase_gen.py`

Contains the `DicewareGenerator` class. It utilizes the EFF Large Word List (7,776 words) to create passphrases. Each word adds ~12.9 bits of entropy. The Diceware method was selected because it balances high security with memorability; a 6-word passphrase (~77.5 bits) is stronger than complex 12-character passwords but significantly easier for humans to recall.

### `generators/password_checker.py`

This module handles the analysis of existing credentials loaded from `passwords.csv`. It calculates local entropy metrics and integrates with the **Have I Been Pwned (HIBP)** API.

**Design Decision:** Privacy was a priority. I implemented the **k-Anonymity** model for the API integration. The tool hashes passwords using SHA-1 and sends only the first 5 characters of the hash to the API. This ensures the user's actual passwords are never transmitted over the network.

### `tests/test_project.py`

A comprehensive test suite using `pytest`. It includes unit tests for all mathematical functions, boundary checks for entropy ratings (e.g., ensuring 49.9 bits is treated differently than 50.0), and mock-based integration tests for user input and API responses.

## 🔧 Technical Implementation

### Entropy Calculation

Password entropy is calculated as:

$$E = L \times \log_2(C)$$

Where **E** is entropy in bits, **L** is length, and **C** is the pool of unique characters available.

### Strength Classification

| Entropy (bits) | Rating | Recommendation |
|---|---|---|
| < 32 | CRITICAL | Change immediately |
| 32-50 | VERY WEAK / WEAK | Low-value accounts only |
| 50-70 | MODERATE / GOOD | Standard use |
| 70-100 | STRONG / VERY STRONG | Sensitive data |
| 100+ | EXCEPTIONAL | Quantum-resistant |

### Attack Scenarios

The toolkit estimates crack times based on three threat models:
1. **Online Attack**: 7,200 attempts/day (simulating aggressive rate-limiting).
2. **GPU Farm**: 1 PetaFLOPS (10¹⁵ attempts/second). (Futureproof rate calculation.
    Nowadays only state actors do operate such high computing power : ~5000 RTX 5090)
3. **Quantum**: Simulates Grover's algorithm, effectively halving the bit strength.

### Used sources

**Secrets library**: https://docs.python.org/3/library/secrets.html  
**EFF Dice-generated passphrase**: https://www.eff.org/dice  
**OWASP CHEat Sheet**: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html  
**NIST Standard**: https://pages.nist.gov/800-63-3/sp800-63b.html
 
## 🚀 Usage

```bash  
# Run the main program  
python project.py  

# Run tests  
pytest test_project.py -v  

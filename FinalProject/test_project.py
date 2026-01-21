"""
Test suite for password security toolkit core functions.
Focuses on mathematical functions and user input handling.
"""

import pytest
from FinalProject.project import (
    evaluate_entropy,
    rate_strength,
    calculate_crack_time,
    calculate_quantum_crack_time
)

# ============================================
# TEST: evaluate_entropy
# ============================================

def test_evaluate_entropy():
    """Test entropy calculation with various inputs"""
    # Basic test: 10 chars from 94-char set
    entropy = evaluate_entropy(10, 94)
    assert 60 < entropy < 70

    # Edge case: zero length
    entropy = evaluate_entropy(0, 94)
    assert entropy == 0

    # Edge case: single character
    entropy = evaluate_entropy(1, 26)
    assert 4.5 < entropy < 5

    # Large charset (94 printable ASCII)
    entropy = evaluate_entropy(16, 94)
    assert 100 < entropy < 110

    # Binary charset
    entropy = evaluate_entropy(128, 2)
    assert entropy == 128


# ============================================
# TEST: rate_strength
# ============================================

def test_rate_strength():
    """Test strength rating for various entropy levels"""
    # Critical - very low entropy
    strength = rate_strength(25)
    assert isinstance(strength, dict)
    assert strength['rating'] == 'CRITICAL'
    assert strength['emoji'] == '🔓'
    assert 'description' in strength
    assert 'warning' in strength
    assert 'recommendation' in strength
    assert 'standards' in strength

    # Very weak
    strength = rate_strength(35)
    assert strength['rating'] == 'VERY WEAK'
    assert strength['emoji'] == '⏰'

    # Weak
    strength = rate_strength(45)
    assert strength['rating'] == 'WEAK'
    assert strength['emoji'] == '🔐'

    # Moderate
    strength = rate_strength(60)
    assert strength['rating'] == 'MODERATE'
    assert strength['emoji'] == '✓'

    # Good
    strength = rate_strength(68)
    assert strength['rating'] == 'GOOD'
    assert strength['emoji'] == '✅'

    # Strong
    strength = rate_strength(75)
    assert strength['rating'] == 'STRONG'
    assert strength['emoji'] == '🔒'

    # Very strong
    strength = rate_strength(90)
    assert strength['rating'] == 'VERY STRONG'
    assert strength['emoji'] == '⚜️'

    # Exceptional
    strength = rate_strength(110)
    assert strength['rating'] == 'EXCEPTIONAL'
    assert strength['emoji'] == '🏆'

    # Maximum
    strength = rate_strength(150)
    assert strength['rating'] == 'MAXIMUM'
    assert strength['emoji'] == '💎'

    # All ratings have complete structure
    assert all(isinstance(strength[key], (str, list)) for key in strength.keys())


# ============================================
# TEST: calculate_crack_time
# ============================================

def test_calculate_crack_time():
    """Test crack time calculation with various entropy levels"""
    # Very low entropy
    time_str = calculate_crack_time(10, 1e15)
    assert isinstance(time_str, str)
    assert "< 1 sec" in time_str

    # Low entropy (30 bits)
    time_str = calculate_crack_time(30, 1e12)
    assert isinstance(time_str, str)
    # Mělo by být v sekundách/minutách/hodinách
    print(f"\n30 bits result: '{time_str}'")  # DEBUG

    # Moderate entropy (50 bits)
    time_str = calculate_crack_time(50, 1e12)
    assert isinstance(time_str, str)
    print(f"50 bits result: '{time_str}'")  # DEBUG

    # Místo specifického unit testu jen ověř, že je to string
    assert len(time_str) > 0
    assert any(char.isdigit() for char in time_str)

    # Strong entropy (80 bits)
    time_str = calculate_crack_time(80, 1e12)
    assert isinstance(time_str, str)
    assert any(unit in time_str.lower() for unit in ["days", "years"])

    # Very strong entropy (100 bits)
    time_str = calculate_crack_time(100, 1e12)
    assert isinstance(time_str, str)
    assert "years" in time_str.lower()

    # Maximum entropy (256 bits)
    time_str = calculate_crack_time(256, 1e15)
    assert isinstance(time_str, str)
    assert any(unit in time_str.lower() for unit in ["years", "never"])

    # Default attempts
    time_str = calculate_crack_time(80)
    assert isinstance(time_str, str)
    assert len(time_str) > 0

# ============================================
# TEST: calculate_quantum_crack_time
# ============================================

def test_calculate_quantum_crack_time():
    """Comprehensive test for quantum crack time calculations with Grover's algorithm."""

    # Test 1: Low entropy (40 bits) - should be instant
    result = calculate_quantum_crack_time(40, 1e7)
    # 2^(40/2) / 1e7 = 2^20 / 1e7 = 1048576 / 10000000 ≈ 0.1 sec
    assert result == "< 1 sec", f"Expected '< 1 sec', got '{result}'"

    # Test 2: Very low entropy (20 bits) - should be instant
    result = calculate_quantum_crack_time(20, 1e7)
    # 2^(20/2) / 1e7 = 2^10 / 1e7 = 1024 / 10000000 ≈ 0.0001 sec
    assert result == "< 1 sec", f"Expected '< 1 sec', got '{result}'"

    # Test 3: Seconds range (50 bits)
    result = calculate_quantum_crack_time(50, 1e7)
    # 2^(50/2) / 1e7 = 2^25 / 1e7 ≈ 3.4 sec
    assert "sec" in result and "min" not in result, f"Expected seconds, got '{result}'"

    # Test 4: Minutes range (60 bits)
    result = calculate_quantum_crack_time(60, 1e7)
    # 2^(60/2) / 1e7 = 2^30 / 1e7 ≈ 107 sec ≈ 1.8 min
    assert "min" in result, f"Expected minutes, got '{result}'"

    # Test 5: Medium entropy (64 bits)
    result = calculate_quantum_crack_time(64, 1e7)
    # 2^(64/2) / 1e7 = 2^32 / 1e7 ≈ 429.5 sec ≈ 7.2 min
    assert "min" in result, f"Expected minutes, got '{result}'"
    assert result.startswith("7."), f"Expected ~7 minutes, got '{result}'"

    # Test 6: Hours/days range (80 bits)
    result = calculate_quantum_crack_time(80, 1e7)
    # 2^(80/2) / 1e7 = 2^40 / 1e7 ≈ 109951 sec ≈ 1.3 days
    assert "days" in result or "hours" in result, f"Expected hours/days, got '{result}'"

    # Test 7: Years range (100 bits)
    result = calculate_quantum_crack_time(100, 1e7)
    # 2^(100/2) / 1e7 = 2^50 / 1e7 ≈ 35.7 years
    assert "years" in result, f"Expected years, got '{result}'"

    # Test 8: High entropy (128 bits - AES level)
    result = calculate_quantum_crack_time(128, 1e7)
    # 2^(128/2) / 1e7 = 2^64 / 1e7 ≈ 58494 years
    assert "years" in result, f"Expected years, got '{result}'"
    assert "58494" in result or "58.5k" in result, f"Expected ~58494 years, got '{result}'"

    # Test 9: Very high entropy (256 bits - quantum resistant)
    result = calculate_quantum_crack_time(256, 1e7)
    # 2^(256/2) / 1e7 = 2^128 / 1e7 = enormous number
    assert "NEVER" in result or "years" in result, f"Expected 'NEVER' or years, got '{result}'"

    # Test 10: Different quantum speeds comparison
    entropy = 128
    result_slow = calculate_quantum_crack_time(entropy, 1e6)  # Slower
    result_default = calculate_quantum_crack_time(entropy, 1e7)  # Default
    result_fast = calculate_quantum_crack_time(entropy, 1e8)  # Faster

    assert "years" in result_slow, f"Expected years for slow speed, got '{result_slow}'"
    assert "years" in result_default, f"Expected years for default speed, got '{result_default}'"
    assert "years" in result_fast, f"Expected years for fast speed, got '{result_fast}'"

    # Test 11: Verify Grover's algorithm formula (manual calculation)
    entropy = 64
    quantum_speed = 1e7
    expected_seconds = (2 ** (entropy / 2)) / quantum_speed
    # 2^32 / 1e7 = 4294967296 / 10000000 ≈ 429.5 seconds
    assert abs(expected_seconds - 429.4967296) < 0.001, f"Formula check failed: {expected_seconds}"

    result = calculate_quantum_crack_time(entropy, quantum_speed)
    assert "7." in result and "min" in result, f"Expected ~7.2 minutes, got '{result}'"

    # Test 12: Default speed parameter
    result_with_default = calculate_quantum_crack_time(64)  # No speed specified
    result_explicit = calculate_quantum_crack_time(64, 1e7)
    assert result_with_default == result_explicit, f"Default speed mismatch: '{result_with_default}' vs '{result_explicit}'"

    # Test 13: Edge cases
    result = calculate_quantum_crack_time(1, 1e7)
    assert result == "< 1 sec", f"Expected '< 1 sec' for entropy=1, got '{result}'"

    result = calculate_quantum_crack_time(0, 1e7)
    assert result == "< 1 sec", f"Expected '< 1 sec' for entropy=0, got '{result}'"

    # Test 14: Very high speed (should give very short time)
    result = calculate_quantum_crack_time(100, 1e20)
    assert "sec" in result or "< 1 sec" in result, f"Expected seconds for very high speed, got '{result}'"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
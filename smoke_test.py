#!/usr/bin/env python3
"""Comprehensive smoke test script for GM Chatbot."""
import sys
import subprocess
import time
import unittest
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from test_game_engine import (
    TestDiceRoller,
    TestShadowdarkRules,
    TestCombatTracker,
    TestSpellManager,
)
from test_command_parser import TestCommandParser
from test_gm_handler import TestGMHandler


def run_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("GM Chatbot Smoke Tests")
    print("=" * 70)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDiceRoller))
    suite.addTests(loader.loadTestsFromTestCase(TestShadowdarkRules))
    suite.addTests(loader.loadTestsFromTestCase(TestCombatTracker))
    suite.addTests(loader.loadTestsFromTestCase(TestSpellManager))
    suite.addTests(loader.loadTestsFromTestCase(TestCommandParser))
    suite.addTests(loader.loadTestsFromTestCase(TestGMHandler))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("✓ All smoke tests passed!")
        return 0
    else:
        print(f"✗ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        return 1


def test_imports():
    """Test that all modules can be imported."""
    print("Testing module imports...")
    try:
        import game_engine
        import command_parser
        import ai_handler
        import gm_handler
        import config
        import shadowdark_rules

        print("✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_basic_functionality():
    """Test basic functionality without full test suite."""
    print("\nTesting basic functionality...")
    try:
        from game_engine import DiceRoller, ShadowdarkRules, CombatTracker

        # Test dice rolling
        result, _ = DiceRoller.roll("1d20")
        assert 1 <= result <= 20, f"Dice roll out of range: {result}"
        print("✓ Dice rolling works")

        # Test rules
        success, _ = ShadowdarkRules.ability_check(15, 3, 15)
        assert success, "Ability check should succeed"
        print("✓ Rule calculations work")

        # Test combat tracker
        tracker = CombatTracker()
        tracker.start_combat()
        assert tracker.is_in_combat(), "Combat should be active"
        print("✓ Combat tracking works")

        return True
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False


if __name__ == "__main__":
    print()
    success = True

    # Test imports
    if not test_imports():
        success = False

    # Test basic functionality
    if not test_basic_functionality():
        success = False

    # Run full test suite
    exit_code = run_tests()
    if exit_code != 0:
        success = False

    print()
    if success:
        print("=" * 70)
        print("✓ All smoke tests completed successfully!")
        print("=" * 70)
        sys.exit(0)
    else:
        print("=" * 70)
        print("✗ Some smoke tests failed. Please review the output above.")
        print("=" * 70)
        sys.exit(1)

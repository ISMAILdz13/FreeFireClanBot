#!/usr/bin/env python3
"""
Test runner for ClanGloryBot test suite.
Run all tests and print a summary.
"""
import sys
import os
import unittest
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "OB54-TCP-BOT"))
sys.path.insert(0, os.path.join(BASE_DIR, "OB54-TCP-BOT", "Pb2"))

# Discover and run all tests
def run_all_tests():
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.dirname(os.path.abspath(__file__)), pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    start = time.time()
    result = runner.run(suite)
    elapsed = time.time() - start

    print("\n" + "=" * 60)
    print(f"  TEST SUITE SUMMARY")
    print(f"  Tests run:    {result.testsRun}")
    print(f"  Failures:     {len(result.failures)}")
    print(f"  Errors:       {len(result.errors)}")
    print(f"  Skipped:      {len(result.skipped)}")
    print(f"  Time:         {elapsed:.1f}s")
    print("=" * 60)

    if result.wasSuccessful():
        print("  ✅ ALL TESTS PASSED")
    else:
        print("  ❌ SOME TESTS FAILED")
        if result.failures:
            print("\n  FAILURES:")
            for test, traceback in result.failures:
                print(f"    - {test}")
        if result.errors:
            print("\n  ERRORS:")
            for test, traceback in result.errors:
                print(f"    - {test}")
    print()

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())

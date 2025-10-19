"""
Run all Phase 1 bug fix tests
"""
import sys
import os

# Test results tracking
tests_run = 0
tests_passed = 0
tests_failed = 0
failed_tests = []

def run_test_file(filename, description):
    global tests_run, tests_passed, tests_failed, failed_tests
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print('='*60)

    result = os.system(f"python tests/{filename} 2>&1")
    tests_run += 1

    if result == 0:
        tests_passed += 1
        print(f"✅ {description} PASSED")
    else:
        tests_failed += 1
        failed_tests.append(description)
        print(f"❌ {description} FAILED")

    return result == 0

# Run all tests
print("="*60)
print("PHASE 1 BUG FIX TEST SUITE")
print("="*60)

run_test_file("test_turn_order.py", "Bug #1: Turn Order Enforcement")
run_test_file("test_fold_resolution.py", "Bug #2: Hand Resolution After Fold")

# Summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)
print(f"Total tests: {tests_run}")
print(f"Passed: ✅ {tests_passed}")
print(f"Failed: ❌ {tests_failed}")

if failed_tests:
    print("\nFailed tests:")
    for test in failed_tests:
        print(f"  - {test}")

if tests_failed == 0:
    print("\n🎉 ALL TESTS PASSED! Phase 1 bug fixes verified.")
    sys.exit(0)
else:
    print(f"\n⚠️  {tests_failed} test(s) failed. Review and fix before proceeding.")
    sys.exit(1)

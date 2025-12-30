#!/usr/bin/env python3
"""
Test runner for DriftGuard
"""

import unittest
import sys
import os

# Add the agent directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent'))

def run_all_tests():
    """Run all tests in the tests directory"""
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Add specific test files if needed
    # This ensures all test files are included in the discovery
    additional_tests = [
        'test_diff_analyzer',
        'test_config_loader_extended',
        'test_aws_detector',
        'test_k8s_detector'
    ]
    
    for test_module in additional_tests:
        try:
            test_suite = loader.loadTestsFromName(f'tests.{test_module}')
            suite.addTests(test_suite)
        except AttributeError:
            # Module might not exist, continue
            pass
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
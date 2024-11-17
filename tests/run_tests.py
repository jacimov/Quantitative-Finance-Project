"""
Test Runner Module

This module discovers and runs all unit tests in the tests directory.
"""

import unittest
import sys
import os


def run_tests():
    """
    Discover and run all unit tests.

    Returns:
        bool: True if all tests pass, False otherwise
    """
    # Add the parent directory to sys.path to import modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)

    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')

    # Run tests with verbosity=2 for detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

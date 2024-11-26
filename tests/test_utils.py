"""
Unit tests for the utils module.

This module contains test cases for the utility functions used in
performance metric calculations.
"""

import unittest
import numpy as np
import pandas as pd
from utils import (
    calculate_annualized_return,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_sortino_ratio
)


class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""

    def setUp(self):
        """Set up test data."""
        # Create sample equity curves for testing
        # 1. Steady upward trend
        self.up_trend = pd.Series([100, 102, 104, 106, 108])

        # 2. Downward trend
        self.down_trend = pd.Series([100, 98, 96, 94, 92])

        # 3. Volatile series
        self.volatile = pd.Series([100, 105, 95, 110, 90])

        # 4. Flat series
        self.flat = pd.Series([100, 100, 100, 100, 100])

        # 5. Series with drawdown and recovery
        self.drawdown = pd.Series([100, 90, 80, 95, 110])

    def test_calculate_annualized_return(self):
        """Test annualized return calculation."""
        # Test upward trend
        up_return = calculate_annualized_return(self.up_trend)
        self.assertGreater(up_return, 0)

        # Test downward trend
        down_return = calculate_annualized_return(self.down_trend)
        self.assertLess(down_return, 0)

        # Test flat trend
        flat_return = calculate_annualized_return(self.flat)
        self.assertAlmostEqual(flat_return, 0)

        # Test with numpy array
        np_return = calculate_annualized_return(np.array(self.up_trend))
        self.assertGreater(np_return, 0)

    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation."""
        # Test upward trend (should have minimal drawdown)
        up_dd = calculate_max_drawdown(self.up_trend)
        self.assertGreaterEqual(up_dd, -0.0001)  # Small negative value or zero

        # Test downward trend
        down_dd = calculate_max_drawdown(self.down_trend)
        self.assertAlmostEqual(down_dd, -0.08)  # (92-100)/100

        # Test volatile series
        volatile_dd = calculate_max_drawdown(self.volatile)
        self.assertLess(volatile_dd, 0)

        # Test series with known drawdown
        known_dd = calculate_max_drawdown(self.drawdown)
        self.assertAlmostEqual(known_dd, -0.2)  # (80-100)/100

    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        risk_free_rate = 0.02  # 2% annual risk-free rate

        # Test upward trend (should have positive Sharpe)
        up_sharpe = calculate_sharpe_ratio(self.up_trend, risk_free_rate)
        self.assertGreater(up_sharpe, 0)

        # Test downward trend (should have negative Sharpe)
        down_sharpe = calculate_sharpe_ratio(self.down_trend, risk_free_rate)
        self.assertLess(down_sharpe, 0)

        # Test flat trend (should have zero or negative Sharpe due to risk-free
        # rate)
        flat_sharpe = calculate_sharpe_ratio(self.flat, risk_free_rate)
        self.assertLess(flat_sharpe, 0)

    def test_calculate_sortino_ratio(self):
        """Test Sortino ratio calculation."""
        risk_free_rate = 0.02  # 2% annual risk-free rate

        # Test upward trend (should have positive Sortino)
        up_sortino = calculate_sortino_ratio(self.up_trend, risk_free_rate)
        self.assertGreater(up_sortino, 0)

        # Test downward trend (should have negative Sortino)
        down_sortino = calculate_sortino_ratio(self.down_trend, risk_free_rate)
        self.assertLess(down_sortino, 0)

        # Test flat trend
        flat_sortino = calculate_sortino_ratio(self.flat, risk_free_rate)
        # Should return 0 as specified in the function for no volatility
        self.assertEqual(flat_sortino, 0)

        # Test volatile series
        volatile_sortino = calculate_sortino_ratio(
            self.volatile, risk_free_rate)
        self.assertIsInstance(volatile_sortino, float)


if __name__ == '__main__':
    unittest.main()

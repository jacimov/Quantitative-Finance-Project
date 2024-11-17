"""
Unit tests for the backtesting runner module.

This module contains test cases for backtesting functionality using the
OptimizedLongShortStrategy.
"""

import unittest
import pandas as pd
import numpy as np
from backtesting_runner import run_single_backtest


class TestBacktestingRunner(unittest.TestCase):
    """Test cases for backtesting runner functions."""

    def setUp(self):
        """Set up test data."""
        # Set random seed for reproducibility
        np.random.seed(42)
        
        # Create sample OHLCV data with strong trend
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        trend = np.linspace(0, 10, 100)  # Strong upward trend
        noise = np.random.randn(100) * 0.5
        price = 100 + trend + noise
        
        self.sample_data = pd.DataFrame({
            'Open': price + np.random.randn(100) * 0.1,
            'High': price + np.abs(np.random.randn(100)) * 0.2,
            'Low': price - np.abs(np.random.randn(100)) * 0.2,
            'Close': price + np.random.randn(100) * 0.1,
            'Volume': np.random.randint(1000, 10000, 100)
        }, index=dates)

        # Sample strategy parameters
        self.sample_params = {
            'position_size': 0.95,
            'atr_period': 5,
            'high_period': 5,
            'low_period': 5,
            'lower_band_multiplier': 2.25,
            'upper_band_multiplier': 2.25,
            'long_size': 1.0,
            'short_size': 1.0
        }

    def test_basic_backtest(self):
        """Test basic backtesting functionality."""
        result = run_single_backtest(self.sample_data, self.sample_params)
        
        # Check that result contains essential metrics
        self.assertIsInstance(result, pd.Series)
        self.assertIn('_equity_curve', result.index)
        
        # Check that equity starts at initial cash
        equity_curve = result['_equity_curve']
        self.assertAlmostEqual(
            equity_curve['Equity'].iloc[0],
            100000,  # Default initial cash
            delta=1  # Allow for small rounding differences
        )

    def test_custom_cash_and_commission(self):
        """Test backtesting with custom initial cash and commission."""
        result = run_single_backtest(
            self.sample_data,
            self.sample_params,
            cash=50000,
            commission=0.002
        )
        
        # Check that equity starts at custom initial cash
        equity_curve = result['_equity_curve']
        self.assertAlmostEqual(
            equity_curve['Equity'].iloc[0],
            50000,
            delta=1
        )

    def test_parameter_sensitivity(self):
        """Test sensitivity to different parameter values."""
        # Test with more aggressive position sizing
        aggressive_params = self.sample_params.copy()
        aggressive_params.update({
            'position_size': 0.95,  # Maximum allowed size
            'long_size': 2.0,      # Significantly increased multiplier
            'short_size': 2.0,     # Significantly increased multiplier
            'lower_band_multiplier': 1.5,  # More sensitive bands
            'upper_band_multiplier': 1.5   # More sensitive bands
        })
        aggressive_result = run_single_backtest(
            self.sample_data,
            aggressive_params
        )
        
        # Test with more conservative position sizing
        conservative_params = self.sample_params.copy()
        conservative_params.update({
            'position_size': 0.5,   # Reduced position size
            'long_size': 0.5,      # Reduced multiplier
            'short_size': 0.5,     # Reduced multiplier
            'lower_band_multiplier': 3.0,  # Less sensitive bands
            'upper_band_multiplier': 3.0   # Less sensitive bands
        })
        conservative_result = run_single_backtest(
            self.sample_data,
            conservative_params
        )
        
        # Compare results
        aggressive_equity = aggressive_result['_equity_curve']['Equity']
        conservative_equity = conservative_result['_equity_curve']['Equity']
        
        # Aggressive strategy should have higher volatility
        self.assertGreater(
            aggressive_equity.std() / aggressive_equity.mean(),  # Normalized volatility
            conservative_equity.std() / conservative_equity.mean()
        )

    def test_error_handling(self):
        """Test error handling with invalid inputs."""
        # Test with missing required parameters
        invalid_params = {}  # No parameters at all
        with self.assertRaises(Exception):
            run_single_backtest(self.sample_data, invalid_params)
        
        # Test with invalid data format
        invalid_data = pd.DataFrame({'A': [1, 2, 3]})  # Missing required columns
        with self.assertRaises(Exception):
            run_single_backtest(invalid_data, self.sample_params)

    def test_strategy_constraints(self):
        """Test that strategy respects position size constraints."""
        # Run backtest with maximum allowed position size
        max_params = self.sample_params.copy()
        max_params.update({
            'position_size': 0.95,
            'long_size': 2.0,
            'short_size': 2.0
        })
        result = run_single_backtest(self.sample_data, max_params)
        
        # Get trades and equity data
        trades_df = result['_trades']
        equity_curve = result['_equity_curve']
        
        # Calculate position values and leverage for each trade
        position_values = trades_df['Size'].astype(float).abs() * trades_df['EntryPrice'].astype(float)
        leverage = position_values / equity_curve['Equity'].iloc[0]
        
        # Check leverage constraint (5x)
        self.assertTrue(all(leverage <= 5.0))
        
        # Check that position sizes are whole numbers
        sizes = trades_df['Size'].astype(float).abs()
        self.assertTrue(all(sizes == sizes.round()))
        
        # Check that no position exceeds 95% of equity
        self.assertTrue(all(position_values <= 0.95 * equity_curve['Equity'].iloc[0]))

if __name__ == '__main__':
    unittest.main()

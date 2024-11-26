"""
Unit tests for the data processing module.

This module contains test cases for forex data loading and processing
functions.
"""

import unittest
import os
import pandas as pd
import tempfile
from data_processing import load_forex_data, get_currency_pairs


class TestDataProcessing(unittest.TestCase):
    """Test cases for data processing functions."""

    def setUp(self):
        """Set up test data and temporary directory."""
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()

        # Create sample forex data
        self.sample_data = pd.DataFrame({
            'Open': [1.1000, 1.1010, 1.1020],
            'High': [1.1020, 1.1030, 1.1040],
            'Low': [1.0990, 1.1000, 1.1010],
            'Close': [1.1010, 1.1020, 1.1030],
            'Datetime': ['2023-01-01', '2023-01-02', '2023-01-03']
        })

        # Save sample data
        self.sample_data.to_csv(
            os.path.join(self.test_dir, 'EURUSD.csv'),
            index=False
        )

        # Create another sample file
        pd.DataFrame(self.sample_data).to_csv(
            os.path.join(self.test_dir, 'GBPUSD.csv'),
            index=False
        )

    def tearDown(self):
        """Clean up temporary files."""
        for file in os.listdir(self.test_dir):
            os.remove(os.path.join(self.test_dir, file))
        os.rmdir(self.test_dir)

    def test_load_forex_data_basic(self):
        """Test basic forex data loading functionality."""
        data = load_forex_data(self.test_dir, 'EURUSD')

        # Check if all required columns are present
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            self.assertIn(col, data.columns)

        # Check data types
        self.assertIsInstance(data.index, pd.DatetimeIndex)
        self.assertEqual(len(data), 3)

    def test_load_forex_data_column_mapping(self):
        """Test column name mapping functionality."""
        # Create data with different column names
        data_diff_cols = pd.DataFrame({
            'open_price': [1.1000, 1.1010],
            'high_price': [1.1020, 1.1030],
            'low_price': [1.0990, 1.1000],
            'close_price': [1.1010, 1.1020],
            'Datetime': ['2023-01-01', '2023-01-02']
        })

        # Save with different column names
        data_diff_cols.to_csv(
            os.path.join(self.test_dir, 'JPYUSD.csv'),
            index=False
        )

        # Load and verify column mapping
        data = load_forex_data(self.test_dir, 'JPYUSD')
        required_cols = ['Open', 'High', 'Low', 'Close']
        for col in required_cols:
            self.assertIn(col, data.columns)

    def test_load_forex_data_missing_columns(self):
        """Test handling of missing columns."""
        # Create data with missing columns
        invalid_data = pd.DataFrame({
            'Open': [1.1000],
            'Close': [1.1010]  # Missing High and Low
        })
        invalid_data.to_csv(
            os.path.join(self.test_dir, 'INVALID.csv'),
            index=False
        )

        # Check if ValueError is raised
        with self.assertRaises(ValueError):
            load_forex_data(self.test_dir, 'INVALID')

    def test_get_currency_pairs(self):
        """Test currency pair listing functionality."""
        # Test with default limit
        pairs = get_currency_pairs(self.test_dir)
        self.assertEqual(len(pairs), 2)  # EURUSD and GBPUSD
        self.assertIn('EURUSD', pairs)
        self.assertIn('GBPUSD', pairs)

        # Test with custom limit
        pairs_limited = get_currency_pairs(self.test_dir, limit=1)
        self.assertEqual(len(pairs_limited), 1)

        # Test with higher limit than available files
        pairs_high_limit = get_currency_pairs(self.test_dir, limit=100)
        self.assertEqual(len(pairs_high_limit), 2)


if __name__ == '__main__':
    unittest.main()

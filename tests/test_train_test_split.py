"""
Unit tests for the train-test split module.

This module contains test cases for time series data splitting functionality.
"""

import unittest
import pandas as pd
import numpy as np
from train_test_split import split_data


class TestTrainTestSplit(unittest.TestCase):
    """Test cases for train-test split function."""

    def setUp(self):
        """Set up test data."""
        # Create sample time series data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        self.sample_data = pd.DataFrame({
            'Close': np.random.randn(100).cumsum(),
            'Volume': np.random.randint(1000, 10000, 100)
        }, index=dates)

    def test_default_split_ratio(self):
        """Test splitting with default ratio (3/4)."""
        train, test = split_data(self.sample_data)
        
        # Check sizes
        self.assertEqual(len(train), 75)  # 75% of 100
        self.assertEqual(len(test), 25)   # 25% of 100
        
        # Check that all data is preserved
        self.assertEqual(len(train) + len(test), len(self.sample_data))
        
        # Check chronological order
        self.assertTrue(train.index[-1] < test.index[0])

    def test_custom_split_ratio(self):
        """Test splitting with custom ratio."""
        train, test = split_data(self.sample_data, train_ratio=0.8)
        
        # Check sizes
        self.assertEqual(len(train), 80)  # 80% of 100
        self.assertEqual(len(test), 20)   # 20% of 100
        
        # Check that all data is preserved
        self.assertEqual(len(train) + len(test), len(self.sample_data))

    def test_small_dataset(self):
        """Test splitting with small dataset."""
        small_data = self.sample_data.iloc[:5]
        train, test = split_data(small_data)
        
        # Check minimum sizes
        self.assertGreater(len(train), 0)
        self.assertGreater(len(test), 0)
        
        # Check that all data is preserved
        self.assertEqual(len(train) + len(test), len(small_data))

    def test_data_integrity(self):
        """Test that data content is preserved after splitting."""
        train, test = split_data(self.sample_data)
        
        # Check that data values are preserved
        pd.testing.assert_frame_equal(
            pd.concat([train, test]),
            self.sample_data
        )
        
        # Check that column structure is preserved
        self.assertEqual(train.columns.tolist(), self.sample_data.columns.tolist())
        self.assertEqual(test.columns.tolist(), self.sample_data.columns.tolist())

    def test_index_continuity(self):
        """Test that datetime index continuity is maintained."""
        train, test = split_data(self.sample_data)
        
        # Check that index types are preserved
        self.assertIsInstance(train.index, pd.DatetimeIndex)
        self.assertIsInstance(test.index, pd.DatetimeIndex)
        
        # Check that there are no gaps between train and test
        self.assertEqual(
            train.index[-1] + pd.Timedelta(days=1),
            test.index[0]
        )


if __name__ == '__main__':
    unittest.main()

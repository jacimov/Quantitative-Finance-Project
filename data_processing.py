"""
Forex Data Processing Module

This module provides functions for loading and processing forex data from CSV
files. It handles:
- Loading forex price data with proper column naming
- Datetime index management
- Volume data handling
- Currency pair identification

The module expects CSV files with OHLCV (Open, High, Low, Close, Volume) data
and handles various common data format variations.
"""

import glob
import os
import pandas as pd


def load_forex_data(data_folder, currency_pair):
    """
    Load and process forex data for a specific currency pair.

    This function loads forex data from a CSV file and ensures it meets the
    required format for backtesting:
    - Contains OHLCV columns (Volume added if missing)
    - Proper datetime index
    - Standardized column names

    Args:
        data_folder (str): Path to the folder containing forex data CSV files
        currency_pair (str): Name of the currency pair (e.g., "EURUSD")

    Returns:
        pd.DataFrame: DataFrame with forex data, indexed by datetime,
            containing columns:
            - Open: Opening price
            - High: Highest price
            - Low: Lowest price
            - Close: Closing price
            - Volume: Trading volume (1 if not available)

    Raises:
        ValueError: If required columns are missing or data format is invalid
    """
    csv_file = os.path.join(data_folder, f"{currency_pair}.csv")
    data = pd.read_csv(csv_file)

    # Ensure required columns are present and named correctly
    required_columns = ['Open', 'High', 'Low', 'Close']
    column_mapping = {}
    for col in required_columns:
        matching_cols = [
            c for c in data.columns if col.lower() in c.lower()
        ]
        if matching_cols:
            column_mapping[matching_cols[0]] = col
        else:
            raise ValueError(
                f"Required column '{col}' not found in the CSV file "
                f"for {currency_pair}."
            )

    # Rename columns
    data = data.rename(columns=column_mapping)

    # Add 'Volume' column if not present (set to 1 as a placeholder)
    if 'Volume' not in data.columns:
        data['Volume'] = 1

    # Store original datetime index
    if 'Datetime' in data.columns:
        data['Datetime'] = pd.to_datetime(data['Datetime'], utc=True)
        original_index = data['Datetime']
        data = data.set_index('Datetime')
    else:
        original_index = pd.date_range(
            start='2000-01-01',
            periods=len(data),
            freq='H'
        )
        data = data.set_index(original_index)

    # Ensure all required columns are present
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in data.columns for col in required_cols):
        raise ValueError(
            f"Data for {currency_pair} must have 'Open', 'High', 'Low', "
            f"'Close', and 'Volume' columns"
        )

    return data


def get_currency_pairs(data_folder, limit=10):
    """
    Get a list of available currency pairs from CSV files.

    This function scans a folder for CSV files and extracts currency pair
    names from the filenames. It assumes each CSV file is named after its
    currency pair (e.g., "EURUSD.csv").

    Args:
        data_folder (str): Path to the folder containing forex data CSV files
        limit (int, optional): Maximum number of currency pairs to return.
            Defaults to 10.

    Returns:
        list[str]: List of currency pair names (e.g., ["EURUSD", "GBPUSD"])
    """
    csv_files = glob.glob(os.path.join(data_folder, "*.csv"))[:limit]
    return [os.path.basename(file).replace(".csv", "") for file in csv_files]

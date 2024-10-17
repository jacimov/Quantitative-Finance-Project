# data_processing.py
import pandas as pd
import os
import glob


def load_forex_data(data_folder, currency_pair):
    csv_file = os.path.join(data_folder, f"{currency_pair}.csv")
    data = pd.read_csv(csv_file)
    # Ensure required columns are present and named correctly
    required_columns = ['Open', 'High', 'Low', 'Close']
    column_mapping = {}
    for col in required_columns:
        matching_cols = [c for c in data.columns if col.lower() in c.lower()]
        if matching_cols:
            column_mapping[matching_cols[0]] = col
        else:
            raise ValueError(f"Required column '{col}' not found in the CSV file for {currency_pair}.")
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
            freq='H')
        data = data.set_index(original_index)

    # Ensure all required columns are present
    if not all(col in data.columns for col in ['Open',
                                               'High',
                                               'Low',
                                               'Close',
                                               'Volume']):
        raise ValueError(f"Data for {currency_pair} must have 'Open', 'High', 'Low', 'Close', and 'Volume' columns")

    return data


def get_currency_pairs(data_folder, limit=10):
    csv_files = glob.glob(os.path.join(data_folder, "*.csv"))[:limit]
    return [os.path.join(file).replace(".csv", "") for file in csv_files]

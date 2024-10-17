# daily_currency_updater.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import os

def fetch_hourly_data(symbol, start_date, end_date):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval="1h")
        if df.empty:
            print(f"No hourly data available for {symbol}")
            return None
        df = df[['Open', 'High', 'Low', 'Close']]
        df.columns = ['open', 'high', 'low', 'close']
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {str(e)}")
        return None

def fetch_and_update_currency_data(currency_pairs):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2)  # Fetch last 2 days of data to ensure we don't miss any

    for from_currency, to_currency in currency_pairs:
        symbol = f"{from_currency}{to_currency}=X"
        pair = f"{from_currency}/{to_currency}"
        filename = f"{pair.replace('/', '_')}_hourly_data_yahoo.csv"
        
        print(f"Updating data for {pair}")
        
        # Fetch new data
        new_data = fetch_hourly_data(symbol, start_date, end_date)
        if new_data is None or new_data.empty:
            continue
        
        # If file exists, read it and append new data, otherwise create new file
        if os.path.exists(filename):
            existing_data = pd.read_csv(filename, index_col=0, parse_dates=True)
            existing_data = existing_data[~existing_data.index.isin(new_data.index)]  # Remove any overlapping dates
            updated_data = pd.concat([existing_data, new_data]).sort_index()
        else:
            updated_data = new_data
        
        # Save updated data
        updated_data.to_csv(filename)
        print(f"Updated {filename} with {len(new_data)} new rows")
        
        time.sleep(1)  # Small delay to be kind to the server

# Extended list of currency pairs
currency_pairs = [
    ('EUR', 'USD'), ('GBP', 'USD'), ('JPY', 'USD'), ('AUD', 'USD'),
    ('CAD', 'USD'), ('CHF', 'USD'), ('NZD', 'USD'), ('SEK', 'USD'),
    ('NOK', 'USD'), ('DKK', 'USD'), ('SGD', 'USD'), ('HKD', 'USD'),
    ('MXN', 'USD'), ('ZAR', 'USD'), ('THB', 'USD'), ('INR', 'USD'),
    ('KRW', 'USD'), ('BRL', 'USD'), ('MYR', 'USD'), ('RUB', 'USD'),
    ('PLN', 'USD'), ('TRY', 'USD'), ('CNY', 'USD'), ('CZK', 'USD'),
    ('HUF', 'USD'), ('ILS', 'USD'), ('CLP', 'USD'), ('PHP', 'USD'),
    ('AED', 'USD'), ('COP', 'USD'), ('SAR', 'USD'), ('IDR', 'USD'),
    ('EUR', 'GBP'), ('EUR', 'JPY'), ('GBP', 'JPY'), ('AUD', 'JPY'),
    ('EUR', 'CHF'), ('GBP', 'CHF'), ('EUR', 'AUD'), ('EUR', 'CAD')
]

if __name__ == "__main__":
    fetch_and_update_currency_data(currency_pairs)
    print("Daily update completed.")
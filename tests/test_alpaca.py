"""Test Alpaca API connection and credentials."""

import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi


def test_alpaca_connection():
    # Load credentials
    load_dotenv()
    api_key = os.getenv('ALPACA_API_KEY')
    api_secret = os.getenv('ALPACA_API_SECRET')

    print("\nTesting Alpaca API Connection:")
    print("=" * 50)

    # Print first and last 4 characters of credentials (safely)
    print(f"\nAPI Key: {api_key[:4]}...{api_key[-4:]}")
    print(f"API Secret: {api_secret[:4]}...{api_secret[-4:]}")

    # Try to initialize API
    try:
        print("\nTrying to initialize Alpaca API...")
        api = tradeapi.REST(
            key_id=api_key,
            secret_key=api_secret,
            base_url='https://paper-api.alpaca.markets',
            api_version='v2'
        )
        print("✓ API initialized successfully")

        # Try to get account info
        print("\nTrying to get account info...")
        account = api.get_account()
        print("✓ Successfully retrieved account info:")
        print(f"Account ID: {account.id}")
        print(f"Account Status: {account.status}")
        print(f"Cash Balance: ${float(account.cash):.2f}")
        print(f"Portfolio Value: ${float(account.portfolio_value):.2f}")

        # Get clock info
        print("\nChecking market clock...")
        clock = api.get_clock()
        print(f"Market is {'open' if clock.is_open else 'closed'}")
        print(f"Next market open: {clock.next_open}")
        print(f"Next market close: {clock.next_close}")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Verify your API key and secret are correct")
        print("2. Check your internet connection")
        print("3. Ensure you're using the paper trading URL")
        print("4. Verify your account is approved for paper trading")


if __name__ == "__main__":
    test_alpaca_connection()

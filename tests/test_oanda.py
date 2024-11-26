"""Test OANDA API connection and credentials."""

import os
from dotenv import load_dotenv
import oandapyV20
from oandapyV20 import API
from oandapyV20.endpoints.accounts import AccountDetails, AccountSummary
from oandapyV20.endpoints.pricing import PricingInfo


def test_oanda_connection():
    # Load credentials
    load_dotenv()
    access_token = os.getenv('OANDA_ACCESS_TOKEN')
    account_id = os.getenv('OANDA_ACCOUNT_ID')

    print("\nTesting OANDA API Connection:")
    print("=" * 50)

    # Print first and last 4 characters of credentials (safely)
    print(f"\nAccess Token: {access_token[:4]}...{access_token[-4:]}")
    print(f"Account ID: {account_id}")

    try:
        print("\nTrying to initialize OANDA API...")
        api = API(access_token=access_token)
        print("✓ API initialized successfully")

        # Try to get account info
        print("\nTrying to get account info...")
        r = AccountSummary(account_id)
        api.request(r)
        account_summary = r.response

        print("✓ Successfully retrieved account info:")
        print(f"Account ID: {account_summary['account']['id']}")
        print(f"Account Name: {account_summary['account']['alias']}")
        print(f"Account Currency: {account_summary['account']['currency']}")
        print(f"Balance: {float(account_summary['account']['balance']):.2f}")

        # Get more detailed account info
        print("\nRetrieving detailed account information...")
        r = AccountDetails(account_id)
        api.request(r)
        account_details = r.response
        print("✓ Successfully retrieved account details")
        print(f"Margin Rate: {account_details['account']['marginRate']}")

        # Get some current prices
        print("\nChecking current EUR/USD price...")
        params = {"instruments": "EUR_USD"}
        r = PricingInfo(accountID=account_id, params=params)
        api.request(r)
        prices = r.response
        current_price = prices['prices'][0]
        print(f"EUR/USD Ask: {current_price['closeoutAsk']}")
        print(f"EUR/USD Bid: {current_price['closeoutBid']}")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Verify your access token is correct")
        print("2. Check your internet connection")
        print("3. Ensure your account ID is correct")
        print("4. Verify your account has proper permissions")


if __name__ == "__main__":
    test_oanda_connection()

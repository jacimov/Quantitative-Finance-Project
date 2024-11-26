"""Test Kalshi API connection and credentials."""

import os
import time
import jwt
import requests
from dotenv import load_dotenv


class KalshiAPI:
    def __init__(self, api_key_id, private_key_path, use_demo=False):
        self.base_url = (
            "https://trading-api.kalshi.com/trade-api/v2"
            if not use_demo
            else "https://demo-api.kalshi.co/trade-api/v2"
        )
        self.api_key_id = api_key_id

        # Read private key
        with open(private_key_path, 'r') as f:
            self.private_key = f.read()

        # Generate JWT token
        self.token = self._generate_token()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def _generate_token(self):
        """Generate JWT token for authentication."""
        now = int(time.time())
        payload = {
            "sub": self.api_key_id,
            "iat": now,
            "exp": now + 3600  # Token expires in 1 hour
        }
        return jwt.encode(payload, self.private_key, algorithm="RS256")

    def get_account(self):
        """Get account information."""
        response = requests.get(
            f"{self.base_url}/account",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_markets(self):
        """Get available markets."""
        response = requests.get(
            f"{self.base_url}/markets",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()


def test_kalshi_connection():
    # Load credentials
    load_dotenv()
    api_key_id = os.getenv('KALSHI_API_KEY_ID')
    private_key_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'kalshi_private_key.pem'
    )

    print("\nTesting Kalshi API Connection:")
    print("=" * 50)

    # Print API key ID (safely)
    if api_key_id:
        print(f"\nAPI Key ID: {api_key_id[:4]}...{api_key_id[-4:]}")
    else:
        print("\nAPI Key ID not found in .env file")

    try:
        print("\nTrying to initialize Kalshi API...")
        client = KalshiAPI(
            api_key_id=api_key_id,
            private_key_path=private_key_path,
            use_demo=False
        )
        print("✓ API initialized and JWT token generated")

        # Get account information
        print("\nTrying to get account info...")
        account_info = client.get_account()
        print("✓ Successfully retrieved account info:")
        print(f"Account ID: {account_info.get('id', 'N/A')}")
        print(f"Email: {account_info.get('email', 'N/A')}")
        balance = float(account_info.get('balance', 0)) / 100
        print(f"Balance: ${balance:.2f}")  # Balance is in cents

        # Get markets information
        print("\nFetching available markets...")
        markets_data = client.get_markets()
        active_markets = [
            m for m in markets_data.get('markets', [])
            if m.get('status') == 'active'
        ]
        print(f"✓ Found {len(active_markets)} active markets")

        # Display some example markets
        if active_markets:
            print("\nSample of active markets:")
            for market in active_markets[:3]:  # Show first 3 markets
                print(f"- {market.get('title', 'N/A')}")
                print(f"  Ticker: {market.get('ticker', 'N/A')}")
                print(f"  Status: {market.get('status', 'N/A')}")
                print(f"  Volume: {market.get('volume', 'N/A')}")

    except requests.exceptions.RequestException as e:
        print(f"\n✗ Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"Error details: {error_detail}")
            except BaseException:
                print(f"Status code: {e.response.status_code}")
                print(f"Response text: {e.response.text}")
        print("\nTroubleshooting tips:")
        print("1. Verify your API key ID is correct")
        print("2. Check that your private key file exists and is valid")
        print("3. Check your internet connection")
        print("4. Ensure your API key has the necessary permissions")
        print("5. Verify that you're using the correct API environment "
              "(demo/production)")
        print("6. Check if your API key has been activated")
        print("7. Visit https://kalshi.com/docs/api for the latest API "
              "documentation")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Verify your API key ID is correct")
        print("2. Check that your private key file exists and is valid")
        print("3. Check your internet connection")
        print("4. Ensure your API key has the necessary permissions")
        print("5. Verify that you're using the correct API environment "
              "(demo/production)")
        print("6. Check if your API key has been activated")
        print("7. Visit https://kalshi.com/docs/api for the latest API "
              "documentation")


if __name__ == "__main__":
    test_kalshi_connection()

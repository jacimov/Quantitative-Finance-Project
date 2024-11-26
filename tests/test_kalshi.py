"""Test Kalshi API connection and credentials."""

import os
from dotenv import load_dotenv
from kalshi import KalshiClient

def test_kalshi_connection():
    # Load credentials
    load_dotenv()
    email = os.getenv('KALSHI_EMAIL')
    password = os.getenv('KALSHI_PASSWORD')
    
    print("\nTesting Kalshi API Connection:")
    print("=" * 50)
    
    # Print email (safely)
    print(f"\nEmail: {email}")
    
    try:
        print("\nTrying to initialize Kalshi API...")
        # Initialize client (defaults to demo if no exchange_url provided)
        client = KalshiClient(email=email, password=password)
        print("✓ API initialized successfully")
        
        # Get user information
        print("\nTrying to get user info...")
        user = client.get_user()
        print("✓ Successfully retrieved user info:")
        print(f"User ID: {user['id']}")
        print(f"Username: {user['username']}")
        print(f"Balance: ${float(user['balance'])/100:.2f}")  # Balance is in cents
        
        # Get markets information
        print("\nFetching available markets...")
        markets = client.get_markets()
        active_markets = [m for m in markets if m['status'] == 'active']
        print(f"✓ Found {len(active_markets)} active markets")
        
        # Display some example markets
        if active_markets:
            print("\nSample of active markets:")
            for market in active_markets[:3]:  # Show first 3 markets
                print(f"- {market['title']}")
                print(f"  Ticker: {market['ticker']}")
                print(f"  Yes Price: ${float(market['yes_bid'])/100:.2f}")
                print(f"  Volume: {market['volume']}")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Verify your email and password are correct")
        print("2. Check your internet connection")
        print("3. Make sure you have a Kalshi account")
        print("4. Try using the demo environment first")

if __name__ == "__main__":
    test_kalshi_connection()

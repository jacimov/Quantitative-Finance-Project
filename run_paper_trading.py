"""
Paper Trading Runner

This script executes the OptimizedLongShortStrategy in paper trading mode
using Alpaca for paper trading.
"""

import os
import time
import logging
from typing import Dict, Optional
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
import alpaca_trade_api as tradeapi

from paper_trader import create_paper_trader
from trading_strategy import OptimizedLongShortStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaperTradingRunner:
    def __init__(
        self,
        symbols: list,
        check_interval: int = 1,  # 1 second
        **broker_credentials
    ):
        """Initialize paper trading runner.

        Args:
            symbols: List of symbols to trade
            check_interval: Seconds between strategy checks
            **broker_credentials: Broker credentials
        """
        self.symbols = symbols
        self.check_interval = check_interval
        self.trader = create_paper_trader('alpaca', **broker_credentials)
        
        # Initialize Alpaca API for real-time data
        self.api = tradeapi.REST(
            key_id=broker_credentials['api_key'],
            secret_key=broker_credentials['api_secret'],
            base_url='https://paper-api.alpaca.markets',
            api_version='v2'
        )
        
        print(f"\n{'='*50}")
        print(f"Paper Trading Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Monitoring markets: {', '.join(symbols)}")
        print(f"Checking for signals every {check_interval} second(s)")
        print(f"{'='*50}\n")
        
        # Initialize strategy parameters
        self.strategy_params = {
            'position_size': 0.95,
            'atr_period': 5,
            'high_period': 10,
            'low_period': 10,
            'lower_band_multiplier': 2.0,
            'upper_band_multiplier': 2.0,
            'long_size': 1.0,
            'short_size': 1.0
        }
        
        # Keep track of positions and orders
        self.positions: Dict[str, Dict] = {}
        
    def get_market_data(self, symbol: str) -> pd.DataFrame:
        """Fetch recent market data for analysis.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Get last 100 bars of 1-minute data
            bars = self.api.get_bars(
                symbol,
                '1Min',
                limit=100,
            ).df
            
            if not bars.empty:
                # Rename columns to match strategy expectations
                bars = bars.rename(columns={
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                })
                return bars
            
            return pd.DataFrame()
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    def check_strategy(self, symbol: str) -> Optional[Dict]:
        """Check if strategy generates any signals.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dict with trade details if signal generated, None otherwise
        """
        # Get market data
        data = self.get_market_data(symbol)
        if data.empty:
            logger.warning(f"No data available for {symbol}")
            return None
            
        # Initialize strategy
        strategy = OptimizedLongShortStrategy()
        for param, value in self.strategy_params.items():
            setattr(strategy, param, value)
            
        # Generate signals
        last_close = data['Close'].iloc[-1]
        last_high = data['High'].iloc[-1]
        last_low = data['Low'].iloc[-1]
        
        # Get current position
        positions = self.trader.get_positions()
        current_position = next(
            (pos for pos in positions if pos['symbol'] == symbol),
            None
        )
        
        # Check for entry/exit signals
        signal = strategy.next_signal(data)  # You'll need to implement this in your strategy class
        
        if signal:
            return {
                'symbol': symbol,
                'action': signal['action'],  # 'buy' or 'sell'
                'qty': signal['size'],
                'price': last_close,
                'type': 'market'
            }
        
        return None
        
    def execute_trades(self):
        """Main trading loop."""
        while True:
            try:
                current_positions = {pos['symbol']: pos for pos in self.trader.get_positions()}
                
                for symbol in self.symbols:
                    print(f"\nChecking {symbol} at {datetime.now().strftime('%H:%M:%S')}")
                    signal = self.check_strategy(symbol)
                    
                    if signal:
                        action = signal['action']
                        size = signal['size']
                        current_price = self.get_market_data(symbol)['Close'].iloc[-1]
                        
                        # Determine if this is an entry or exit
                        is_entry = symbol not in current_positions
                        position_type = "entry" if is_entry else "exit"
                        
                        print(f"\n🔔 SIGNAL for {symbol}:")
                        print(f"  {'Opening' if is_entry else 'Closing'} {action.upper()} position")
                        print(f"  Size: {size} units")
                        print(f"  Price: ${current_price:.2f}")
                        
                        try:
                            order = self.trader.place_order(
                                symbol=signal['symbol'],
                                qty=signal['qty'],
                                side=signal['action'],
                                order_type=signal['type']
                            )
                            print(f"  ✅ Order placed successfully")
                        except Exception as e:
                            print(f"  ❌ Error placing order: {e}")
                    else:
                        # If we have a position in this symbol, show its current status
                        if symbol in current_positions:
                            pos = current_positions[symbol]
                            current_price = self.get_market_data(symbol)['Close'].iloc[-1]
                            unrealized_pl = (current_price - float(pos['avg_entry_price'])) * float(pos['qty'])
                            if pos['side'] == 'short':
                                unrealized_pl = -unrealized_pl
                            
                            print(f"  Current {pos['side'].upper()} position:")
                            print(f"  Size: {pos['qty']} units")
                            print(f"  Entry: ${float(pos['avg_entry_price']):.2f}")
                            print(f"  Current: ${current_price:.2f}")
                            print(f"  P&L: ${unrealized_pl:.2f}")
                            
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\n\nStopping paper trading...")
                print("Final positions:")
                for pos in self.trader.get_positions():
                    print(f"  {pos['symbol']}: {pos['qty']} units ({pos['side']})")
                break
            except Exception as e:
                print(f"\n❌ Error in trading loop: {e}")
                time.sleep(self.check_interval)

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # List of stocks to monitor (you can modify this list)
    symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',  # Tech giants
        'NVDA', 'AMD', 'INTC',                     # Semiconductors
        'JPM', 'BAC', 'GS',                        # Banks
        'TSLA', 'F', 'GM',                         # Automotive
        'DIS', 'NFLX', 'ROKU',                     # Entertainment
        'WMT', 'TGT', 'COST',                      # Retail
        'XOM', 'CVX'                               # Energy
    ]
    
    # Initialize with Alpaca credentials
    runner = PaperTradingRunner(
        symbols=symbols,
        api_key=os.getenv('ALPACA_API_KEY'),
        api_secret=os.getenv('ALPACA_API_SECRET')
    )
    
    # Start paper trading
    runner.execute_trades()
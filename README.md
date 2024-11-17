# Quantitative Trading Strategy Framework

A Python-based quantitative trading framework that implements an optimized long-short trading strategy with comprehensive backtesting capabilities.

## Overview

This project provides a robust implementation of a technical analysis-based trading strategy that utilizes:
- ATR (Average True Range) for volatility measurement
- Dynamic price bands for entry signals
- Trailing high/low values for exit signals
- Position sizing optimization
- Comprehensive backtesting framework

## Project Structure

```
BlackBoxes/
├── trading_strategy.py     # Core trading strategy implementation
├── backtesting_runner.py   # Backtesting execution and configuration
├── utils.py               # Utility functions
└── tests/                 # Test suite
    ├── test_backtesting_runner.py
    └── run_tests.py
```

## Features

- **Optimized Long-Short Strategy**
  - Dynamic volatility-based entry points
  - Separate long and short position sizing
  - Trailing stop-loss mechanism
  - Customizable strategy parameters

- **Backtesting Framework**
  - Easy-to-use interface for strategy testing
  - Configurable initial capital and commission rates
  - Comprehensive performance metrics
  - Trade history and equity curve analysis

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/BlackBoxes.git
cd BlackBoxes
```

2. Install required dependencies:
```bash
pip install backtesting numpy pandas
```

## Usage

### Running a Backtest

```python
from backtesting_runner import run_single_backtest
import pandas as pd

# Prepare your OHLCV data
data = pd.DataFrame(...)  # Your market data

# Define strategy parameters
params = {
    'position_size': 0.95,
    'atr_period': 5,
    'high_period': 10,
    'low_period': 10,
    'lower_band_multiplier': 2.0,
    'upper_band_multiplier': 2.0,
    'long_size': 1.0,
    'short_size': 1.0
}

# Run backtest
results = run_single_backtest(
    data=data,
    params=params,
    cash=100000,
    commission=0.0001
)

# Access performance metrics
print(results.metrics)
```

### Running Tests

```bash
python tests/run_tests.py
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

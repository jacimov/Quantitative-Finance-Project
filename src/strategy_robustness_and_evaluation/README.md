# Strategy Robustness and Evaluation

This directory contains scripts for evaluating and testing the robustness of trading strategies across different timeframes.

## Files

- `strategy_comparison.py`: Base implementation of trading strategies (Keltner Channel and Long-Short)
- `strategy_evaluation_hourly.py`: Evaluates strategies on 1-hour data
- `strategy_evaluation_minute.py`: Evaluates strategies on 1-minute data

## Strategy Details

### Optimization Parameters
- Keltner Channel Strategy:
  - n (period): [10, 20, 30]
  - atr_period: [10, 14, 20]
  - multiplier: [1.5, 2.0, 2.5]

- Long-Short Strategy:
  - n (period): [10, 20, 30]
  - multiplier: [1.5, 2.0, 2.5]

### Evaluation Process
1. Optimize strategies using 1-year of historical 1-hour data
2. Evaluate performance on recent data (last week) using both 1-hour and 1-minute timeframes
3. Generate comprehensive performance visualizations

## Usage

Run either evaluation script to optimize and evaluate strategies:

```bash
# For hourly evaluation
python strategy_evaluation_hourly.py

# For minute evaluation
python strategy_evaluation_minute.py
```

## Output

The scripts generate plots saved to the desktop with:
- Strategy signals
- Equity curves
- Performance metrics
- Timestamp in filename for tracking

# backtesting.py
from backtesting import Backtest
from trading_strategy import OptimizedLongShortStrategy

def run_single_backtest(data, params, cash=100000, commission=0.0001):
    bt = Backtest(data, OptimizedLongShortStrategy, cash=cash, commission=commission)
    return bt.run(**params)
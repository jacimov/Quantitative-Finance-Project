# trading_strategy.py
from backtesting import Strategy
import numpy as np

class OptimizedLongShortStrategy(Strategy):
    position_size = 0.95
    atr_period = 5
    high_period = 5
    low_period = 5
    lower_band_multiplier = 2.25
    upper_band_multiplier = 2.25
    long_size = 1.0
    short_size = 1.0

    def init(self):
        self.atr_period = int(self.atr_period)
        self.high_period = int(self.high_period)
        self.low_period = int(self.low_period)
        
        self.atr = self.I(self.calculate_atr, self.atr_period)
        self.high = self.I(self.calculate_high, self.high_period)
        self.low = self.I(self.calculate_low, self.low_period)
        self.lower_band = self.I(self.calculate_lower_band)
        self.upper_band = self.I(self.calculate_upper_band)

    def calculate_atr(self, period):
        high = self.data.High
        low = self.data.Low
        close = self.data.Close
        tr = np.maximum(high - low, np.abs(high - np.roll(close, 1)), np.abs(low - np.roll(close, 1)))
        atr = np.zeros_like(tr)
        atr[:period] = np.nan
        for i in range(period, len(tr)):
            atr[i] = np.mean(tr[i-period+1:i+1])
        return atr

    def calculate_high(self, period):
        high = self.data.High
        result = np.zeros_like(high)
        for i in range(len(high)):
            result[i] = np.max(high[max(0, i-period+1):i+1])
        return result

    def calculate_low(self, period):
        low = self.data.Low
        result = np.zeros_like(low)
        for i in range(len(low)):
            result[i] = np.min(low[max(0, i-period+1):i+1])
        return result

    def calculate_lower_band(self):
        return self.high - self.lower_band_multiplier * self.atr

    def calculate_upper_band(self):
        return self.low + self.upper_band_multiplier * self.atr

    def next(self):
        if not self.position:
            if self.data.Close[-1] < self.lower_band[-1]:
                size = min(self.position_size * self.long_size, 0.99)
                self.buy(size=size)
            elif self.data.Close[-1] > self.upper_band[-1]:
                size = min(self.position_size * self.short_size, 0.99)
                self.sell(size=size)
        elif self.position.is_long and self.data.Close[-1] > self.data.High[-2]:
            self.position.close()
        elif self.position.is_short and self.data.Close[-1] < self.data.Low[-2]:
            self.position.close()

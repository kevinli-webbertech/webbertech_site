import pandas as pd
import yfinance as yf
import talib
import backtrader as bt

# ✅ Step 1: Download Data
ticker = "TSLA"
df = yf.download(ticker, start="2020-01-01", end="2025-03-14", auto_adjust=False)

# ✅ Step 2: Fix MultiIndex Column Issue
if isinstance(df.columns, pd.MultiIndex):
    df.columns = ['_'.join(col) if isinstance(col, tuple) else col for col in df.columns]

df.rename(columns={'Close_TSLA': 'Close'}, inplace=True)

print("Updated Columns in DataFrame:", df.columns.tolist())  # Debugging

if 'Close' not in df.columns:
    print("❌ 'Close' column not found! Exiting.")
    exit()

df['Close'] = df['Close'].ffill()
df.dropna(subset=['Close'], inplace=True)

# ✅ Step 3: Compute EMA
df['ema_20'] = talib.EMA(df['Close'].astype(float).values.ravel(), timeperiod=20)

# ✅ Step 4: Define Backtrader Data Feed (Now Includes `ema_20`)
class PandasDataEMA(bt.feeds.PandasData):
    lines = ('ema_20',)  # Add EMA-20 as a new line
    params = (('ema_20', -1),)

# ✅ Step 5: Define EMA Strategy with Fixed 20-Share Trades
class EMAStrategy(bt.Strategy):
    initial_cash = 10000
    cash = initial_cash
    shares = 0
    trade_size = 20

    def __init__(self):
        self.ema_cross = bt.indicators.CrossOver(self.data.close, self.data.ema_20)

    def next(self):
        price = self.data.close[0]

        if self.ema_cross > 0:  # BUY SIGNAL
            if self.cash >= price * self.trade_size:
                self.shares += self.trade_size
                self.cash -= price * self.trade_size
                print(f"✅ BUY on {self.data.datetime.date(0)}, Price: {price:.2f}, Cash Left: ${self.cash:.2f}, Shares: {self.shares}")

        elif self.ema_cross < 0:  # SELL SIGNAL
            if self.shares >= self.trade_size:
                self.shares -= self.trade_size
                self.cash += price * self.trade_size
                print(f"❌ SELL on {self.data.datetime.date(0)}, Price: {price:.2f}, Cash After Sale: ${self.cash:.2f}, Shares Left: {self.shares}")

    def stop(self):
        final_value = self.cash + (self.shares * self.data.close[0])
        print(f"🔹 Final Portfolio Value (EMA Strategy) on 2025-03-14: ${final_value:.2f}")

# ✅ Step 6: Run Backtrader Simulation
cerebro = bt.Cerebro()
cerebro.addstrategy(EMAStrategy)
data = PandasDataEMA(dataname=df)  # ✅ Use Custom Data Feed with `ema_20`
cerebro.adddata(data)
cerebro.run()

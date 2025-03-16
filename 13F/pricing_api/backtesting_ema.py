import pandas as pd
import yfinance as yf
import talib
import backtrader as bt

# ✅ Step 1: Download Data (2020-01-01 to 2024-03-15)
ticker = "AAPL"
df = yf.download(ticker, start="2020-01-01", end="2024-03-15", auto_adjust=False)

# ✅ Step 2: Fix MultiIndex Column Issue
if isinstance(df.columns, pd.MultiIndex):
    df.columns = ['_'.join(col) if isinstance(col, tuple) else col for col in df.columns]

df.rename(columns={
    'Close_AAPL': 'Close',
    'Open_AAPL': 'Open',
    'High_AAPL': 'High',
    'Low_AAPL': 'Low',
    'Adj Close_AAPL': 'Adj Close',
    'Volume_AAPL': 'Volume'
}, inplace=True)

print("Updated Columns in DataFrame:", df.columns.tolist())  # Debugging

# ✅ Step 3: Ensure 'Close' Column Exists
if 'Close' not in df.columns:
    print("❌ 'Close' column not found! Exiting.")
    exit()

df['Close'] = df['Close'].ffill()  # Fill missing values
df.dropna(subset=['Close'], inplace=True)

# ✅ Step 4: Convert 'Close' to a NumPy Array & Compute EMA
df['ema_20'] = talib.EMA(df['Close'].astype(float).values.ravel(), timeperiod=20)

# ✅ Step 5: Define Backtrader Data Feed
class PandasDataEMA(bt.feeds.PandasData):
    lines = ('ema_20',)
    params = (('ema_20', -1),)

# ✅ Step 6: Define EMA-Only Strategy
class EMAOnlyStrategy(bt.Strategy):
    def __init__(self):
        self.ema_cross = bt.indicators.CrossOver(self.data.close, self.data.ema_20)

    def next(self):
        print(f"📌 Date: {self.data.datetime.date(0)} | Price: {self.data.close[0]:.2f} | EMA-20: {self.data.ema_20[0]:.2f}")
        if not self.position and self.ema_cross > 0:
            self.buy(size=100)
            print(f"✅ BUY on {self.data.datetime.date(0)}, Price: {self.data.close[0]:.2f}")
        elif self.position and self.ema_cross < 0:
            self.sell(size=100)
            print(f"❌ SELL on {self.data.datetime.date(0)}, Price: {self.data.close[0]:.2f}")

# ✅ Step 7: Run Backtrader
cerebro = bt.Cerebro()
cerebro.addstrategy(EMAOnlyStrategy)
data = PandasDataEMA(dataname=df)
cerebro.adddata(data)
cerebro.broker.setcash(100000.0)
cerebro.run()
cerebro.plot(style='candlestick', volume=False)

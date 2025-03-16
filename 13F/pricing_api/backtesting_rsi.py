import pandas as pd
import yfinance as yf
import talib
import backtrader as bt

# ✅ Step 1: Download Data
ticker = "AAPL"
df = yf.download(ticker, start="2020-01-01", end="2022-10-31", auto_adjust=False)

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

# ✅ Step 4: Convert 'Close' to a NumPy Array & Calculate RSI
df['rsi'] = talib.RSI(df['Close'].astype(float).values.ravel(), timeperiod=14)

# ✅ Step 5: Define Backtrader Data Feed
class PandasDataExtended(bt.feeds.PandasData):
    lines = ('rsi',)
    params = (('rsi', -1),)

# ✅ Step 6: Define RSI-Only Strategy
class RSIOnlyStrategy(bt.Strategy):
    def next(self):
        print(f"📌 Date: {self.data.datetime.date(0)} | RSI: {self.data.rsi[0]:.2f} | Price: {self.data.close[0]:.2f}")
        if not self.position and self.data.rsi[0] < 30:
            self.buy(size=100)
            print(f"✅ BUY on {self.data.datetime.date(0)}, Price: {self.data.close[0]:.2f}")
        elif self.position and self.data.rsi[0] > 70:
            self.sell(size=100)
            print(f"❌ SELL on {self.data.datetime.date(0)}, Price: {self.data.close[0]:.2f}")

# ✅ Step 7: Run Backtrader
cerebro = bt.Cerebro()
cerebro.addstrategy(RSIOnlyStrategy)
data = PandasDataExtended(dataname=df)
cerebro.adddata(data)
cerebro.broker.setcash(100000.0)
cerebro.run()
cerebro.plot(style='candlestick', volume=False)

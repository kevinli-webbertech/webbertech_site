import pandas as pd
import yfinance as yf
import talib
import backtrader as bt

# ✅ Step 1: Download Data
ticker = "TSLA"
df = yf.download(ticker, start="2020-01-01", end="2025-03-14", auto_adjust=False)

# ✅ Step 2: Ensure 'Close' Column Exists
if isinstance(df.columns, pd.MultiIndex):
    df.columns = ['_'.join(col) if isinstance(col, tuple) else col for col in df.columns]

df.rename(columns={'Close_TSLA': 'Close'}, inplace=True)

print("Updated Columns in DataFrame:", df.columns.tolist())  # Debugging

if 'Close' not in df.columns:
    print("❌ 'Close' column not found! Exiting.")
    exit()

df['Close'] = df['Close'].ffill()
df.dropna(subset=['Close'], inplace=True)

# ✅ Step 3: Compute MACD
df['macd'], df['signal'], df['hist'] = talib.MACD(df['Close'].astype(float).values.ravel(), fastperiod=12, slowperiod=26, signalperiod=9)

# ✅ Step 4: Define Backtrader Data Feed
class PandasDataMACD(bt.feeds.PandasData):
    lines = ('macd', 'signal', 'hist')
    params = (('macd', -1), ('signal', -1), ('hist', -1))

# ✅ Step 5: Define MACD Strategy with Fixed 20-Share Trades
class MACDStrategy(bt.Strategy):
    initial_cash = 10000  # Start with $10,000
    cash = initial_cash
    shares = 0
    trade_size = 20  # Always trade 20 shares

    def __init__(self):
        self.macd_cross = bt.indicators.CrossOver(self.data.macd, self.data.signal)

    def next(self):
        price = self.data.close[0]

        if self.macd_cross > 0:  # BUY SIGNAL
            if self.cash >= price * self.trade_size:
                self.shares += self.trade_size
                self.cash -= price * self.trade_size
                print(f"✅ BUY on {self.data.datetime.date(0)}, Price: {price:.2f}, Cash Left: ${self.cash:.2f}, Shares: {self.shares}")

        elif self.macd_cross < 0:  # SELL SIGNAL
            if self.shares >= self.trade_size:
                self.shares -= self.trade_size
                self.cash += price * self.trade_size
                print(f"❌ SELL on {self.data.datetime.date(0)}, Price: {price:.2f}, Cash After Sale: ${self.cash:.2f}, Shares Left: {self.shares}")

    def stop(self):
        final_value = self.cash + (self.shares * self.data.close[0])
        print(f"🔹 Final Portfolio Value (MACD Strategy) on 2025-03-14: ${final_value:.2f}")

# ✅ Step 6: Run Backtrader Simulation
cerebro = bt.Cerebro()
cerebro.addstrategy(MACDStrategy)
data = PandasDataMACD(dataname=df)
cerebro.adddata(data)
cerebro.run()

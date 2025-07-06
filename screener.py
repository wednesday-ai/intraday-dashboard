import yfinance as yf
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from datetime import datetime

STOCKS = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "TATAMOTORS.NS", "INFY.NS", "ICICIBANK.NS"]
INTERVAL = "5m"
LOOKBACK_DAYS = 3
RSI_THRESHOLD = 55
VOLUME_MULTIPLIER = 2

def rsi_vwap_strategy(df):
    df['RSI'] = RSIIndicator(df['Close'], window=14).rsi()
    df['VWAP'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()
    latest = df.iloc[-1]
    if latest['Close'] > latest['VWAP'] and latest['RSI'] > RSI_THRESHOLD:
        return True, f"RSI: {latest['RSI']:.2f}, VWAP: {latest['VWAP']:.2f}"
    return False, ""

def ema_crossover_strategy(df):
    df['EMA5'] = EMAIndicator(df['Close'], window=5).ema_indicator()
    df['EMA20'] = EMAIndicator(df['Close'], window=20).ema_indicator()
    if df['EMA5'].iloc[-2] < df['EMA20'].iloc[-2] and df['EMA5'].iloc[-1] > df['EMA20'].iloc[-1]:
        return True, "EMA crossover detected"
    return False, ""

def fetch_data(ticker):
    try:
        df = yf.download(ticker, period=f"{LOOKBACK_DAYS}d", interval=INTERVAL, progress=False)
        return df.dropna()
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def scan():
    print(f"\nScan started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    for ticker in STOCKS:
        df = fetch_data(ticker)
        if df is None or len(df) < 20:
            continue
        signals = []
        res, note = rsi_vwap_strategy(df)
        if res:
            signals.append(f"[RSI+VWAP] {note}")
        res, note = ema_crossover_strategy(df)
        if res:
            signals.append(f"[EMA Crossover] {note}")
        if signals:
            print(f"🔔 {ticker}: {' | '.join(signals)}")
        else:
            print(f"❌ {ticker}: No setup")

if __name__ == "__main__":
    scan()

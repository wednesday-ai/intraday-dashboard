import streamlit as st
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volume import VolumeWeightedAveragePrice
from datetime import datetime, timedelta

st.set_page_config(page_title="Intraday Screener", layout="wide")
st.title("📱 Intraday Screener (Mobile View)")

# Input UI
symbols_input = st.text_input("🔍 Enter Stock Symbols (comma separated)", "RELIANCE.NS, INFY.NS")
interval = st.selectbox("⏱ Time Interval", ["5m", "15m", "30m"], index=0)
lookback_days = st.slider("🙈 Lookback Days", 1, 10, 3)
symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]

# Signal generator
def generate_signals(df):
    try:
        df = df.copy()

        # Ensure all columns are 1D Series
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']

        # Indicators
        df['RSI'] = RSIIndicator(close=close).rsi()
        macd = MACD(close=close)
        df['MACD'] = macd.macd()
        df['MACD_SIGNAL'] = macd.macd_signal()
        vwap = VolumeWeightedAveragePrice(high=high, low=low, close=close, volume=volume)
        df['VWAP'] = vwap.vwap

        df.dropna(inplace=True)

        if df.empty:
            return "⚠️ Not enough data after indicators"

        latest = df.iloc[-1]

        if (
            latest['RSI'] > 55 and
            latest['MACD'] > latest['MACD_SIGNAL'] and
            latest['Close'] > latest['VWAP']
        ):
            return "📈 BUY"
        elif (
            latest['RSI'] < 45 and
            latest['MACD'] < latest['MACD_SIGNAL'] and
            latest['Close'] < latest['VWAP']
        ):
            return "📉 SELL"
        else:
            return "⏸️ Neutral"

    except Exception as e:
        return f"❌ Error: {str(e)}"

# Button logic
if st.button("▶️ Scan"):
    results = []
    end = datetime.now()
    start = end - timedelta(days=lookback_days)

    for symbol in symbols:
        try:
            df = yf.download(symbol, start=start, end=end, interval=interval)
            if df.empty:
                results.append((symbol, "⚠️ No data"))
                continue

            signal = generate_signals(df)
            results.append((symbol, signal))
        except Exception as e:
            results.append((symbol, f"❌ Error: {str(e)}"))

    st.dataframe(pd.DataFrame(results, columns=["Stock", "Signals"]), use_container_width=True)
    st.success("✅ Scan Complete")




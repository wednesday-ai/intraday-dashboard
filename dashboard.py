import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from datetime import datetime, timedelta

st.set_page_config(page_title="Intraday Screener", layout="wide")
st.title("📱 Intraday Screener (Mobile View)")

# --- Input
symbols_input = st.text_input("🔍 Enter Stock Symbols (comma separated)", "RELIANCE.NS, INFY.NS")
interval = st.selectbox("⏱ Time Interval", ["5m", "15m", "30m"], index=0)
lookback_days = st.slider("🙈 Lookback Days", 1, 10, 3)

symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]

# --- Signal Generator
def generate_signals(df):
    try:
        df = df.copy()

        # Make sure close is a 1D Series
        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        # Technical Indicators
        df['RSI'] = ta.momentum.RSIIndicator(close=close).rsi()

        macd_obj = ta.trend.MACD(close=close)
        df['MACD'] = macd_obj.macd()
        df['MACD_SIGNAL'] = macd_obj.macd_signal()

        vwap_obj = ta.volume.VolumeWeightedAveragePrice(
            high=high, low=low, close=close, volume=volume
        )
        df['VWAP'] = vwap_obj.vwap

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
        return f"⚠️ {str(e)}"

# --- Scanning
if st.button("▶️ Scan"):
    results = []
    end = datetime.now()
    start = end - timedelta(days=lookback_days)

    for symbol in symbols:
        try:
            data = yf.download(symbol, start=start, end=end, interval=interval)
            if data.empty:
                results.append((symbol, "⚠️ No data"))
                continue

            signal = generate_signals(data)
            results.append((symbol, signal))
        except Exception as e:
            results.append((symbol, f"⚠️ {str(e)}"))

    df_results = pd.DataFrame(results, columns=["Stock", "Signals"])
    st.dataframe(df_results, use_container_width=True)
    st.success("✅ Scan Complete")



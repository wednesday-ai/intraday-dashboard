import streamlit as st
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volume import VolumeWeightedAveragePrice
from datetime import datetime, timedelta

# Streamlit UI Setup
st.set_page_config(page_title="Intraday Screener", layout="wide")
st.title("📱 Intraday Screener (Mobile View)")

# --- User Inputs ---
symbols_input = st.text_input("🔍 Enter Stock Symbols (comma separated)", "RELIANCE.NS, INFY.NS")
interval = st.selectbox("⏱ Time Interval", ["5m", "15m", "30m"], index=0)
lookback_days = st.slider("📅 Lookback Days", 1, 10, 3)
symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]

# --- Signal Generator ---
def generate_signals(df):
    try:
        df = df.copy()

        # Technical Indicators (must be 1D Series)
        df["RSI"] = RSIIndicator(close=df["Close"]).rsi()
        macd = MACD(close=df["Close"])
        df["MACD"] = macd.macd()
        df["MACD_SIGNAL"] = macd.macd_signal()

        vwap = VolumeWeightedAveragePrice(
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            volume=df["Volume"]
        )
        df["VWAP"] = vwap.vwap

        # Remove NaN values caused by indicator initialization
        df.dropna(inplace=True)

        if df.empty:
            return "⚠️ Not enough data"

        latest = df.iloc[-1]

        # Signal Logic on Latest Candle
        if (
            latest["RSI"] > 55 and
            latest["MACD"] > latest["MACD_SIGNAL"] and
            latest["Close"] > latest["VWAP"]
        ):
            return "📈 BUY"
        elif (
            latest["RSI"] < 45 and
            latest["MACD"] < latest["MACD_SIGNAL"] and
            latest["Close"] < latest["VWAP"]
        ):
            return "📉 SELL"
        else:
            return "⏸️ NEUTRAL"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# --- Main Scan Logic ---
if st.button("▶️ Scan"):
    results = []
    end = datetime.now()
    start = end - timedelta(days=lookback_days)

    for symbol in symbols:
        try:
            df = yf.download(symbol, start=start, end=end, interval=interval)
            if df.empty:
                results.append((symbol, "⚠️ No Data"))
                continue

            signal = generate_signals(df)
            results.append((symbol, signal))
        except Exception as e:
            results.append((symbol, f"❌ Error: {str(e)}"))

    result_df = pd.DataFrame(results, columns=["Stock", "Signals"])
    st.dataframe(result_df, use_container_width=True)
    st.success("✅ Scan Complete")





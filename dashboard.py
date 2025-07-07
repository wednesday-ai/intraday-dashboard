import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from datetime import datetime, timedelta

st.set_page_config(page_title="Intraday Screener", layout="wide")

st.title("📱 Intraday Screener (Mobile View)")

# --- Input Section ---
symbols_input = st.text_input("🔍 Enter Stock Symbols (comma separated)", "RELIANCE.NS, INFY.NS")
interval = st.selectbox("⏱ Time Interval", ["5m", "15m", "30m"], index=0)
lookback_days = st.slider("🙈 Lookback Days", 1, 10, 3)

symbols = [symbol.strip().upper() for symbol in symbols_input.split(',') if symbol.strip()]

# --- Signal Logic ---
def generate_signals(df):
    try:
        df['RSI'] = ta.momentum.RSIIndicator(close=df['Close']).rsi()
        macd = ta.trend.MACD(close=df['Close'])
        df['MACD'] = macd.macd()
        df['Signal'] = macd.macd_signal()

        vwap = ta.volume.VolumeWeightedAveragePrice(
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            volume=df['Volume']
        )
        df['VWAP'] = vwap.vwap

        latest = df.dropna().iloc[-1]

        # Signal logic on latest candle
        if (
            latest['RSI'] > 55 and
            latest['MACD'] > latest['Signal'] and
            latest['Close'] > latest['VWAP']
        ):
            return "📈 BUY Signal"
        elif (
            latest['RSI'] < 45 and
            latest['MACD'] < latest['Signal'] and
            latest['Close'] < latest['VWAP']
        ):
            return "📉 SELL Signal"
        else:
            return "🔍 No Clear Signal"
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# --- Scan Logic ---
if st.button("▶️ Scan"):
    results = []
    end = datetime.now()
    start = end - timedelta(days=lookback_days)

    for symbol in symbols:
        try:
            data = yf.download(symbol, start=start, end=end, interval=interval)
            if data.empty:
                results.append((symbol, "⚠️ No Data"))
                continue

            signal = generate_signals(data)
            results.append((symbol, signal))
        except Exception as e:
            results.append((symbol, f"⚠️ Error: {str(e)}"))

    # --- Display Results ---
    df_result = pd.DataFrame(results, columns=["Stock", "Signals"])
    st.dataframe(df_result, use_container_width=True)
    st.success("✅ Scan Complete")

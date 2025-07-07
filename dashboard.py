import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from datetime import datetime, timedelta

st.set_page_config(page_title="Intraday Screener", layout="wide")
st.title("📱 Intraday Screener (Mobile View)")

symbols_input = st.text_input("🔍 Enter Stock Symbols (comma separated)", "RELIANCE.NS, INFY.NS")
interval = st.selectbox("⏱ Time Interval", ["5m", "15m", "30m"], index=0)
lookback_days = st.slider("🙈 Lookback Days", 1, 10, 3)

symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]

def generate_signals(df):
    try:
        df = df.copy()
        
        # Calculate indicators
        df['RSI'] = ta.momentum.RSIIndicator(close=df['Close']).rsi()
        macd = ta.trend.MACD(close=df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_SIGNAL'] = macd.macd_signal()
        vwap = ta.volume.VolumeWeightedAveragePrice(
            high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume']
        )
        df['VWAP'] = vwap.vwap

        # Drop all rows with NaNs
        df = df.dropna()

        if len(df) == 0:
            return "⚠️ Not enough data after indicators"

        # Use only the latest row
        latest = df.iloc[-1]

        rsi = latest['RSI']
        macd_line = latest['MACD']
        macd_signal = latest['MACD_SIGNAL']
        close = latest['Close']
        vwap_val = latest['VWAP']

        if rsi > 55 and macd_line > macd_signal and close > vwap_val:
            return "📈 BUY"
        elif rsi < 45 and macd_line < macd_signal and close < vwap_val:
            return "📉 SELL"
        else:
            return "🔍 Neutral"
    except Exception as e:
        return f"⚠️ {str(e)}"

if st.button("▶️ Scan"):
    st.write("Scanning stocks...")
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

    result_df = pd.DataFrame(results, columns=["Stock", "Signals"])
    st.dataframe(result_df, use_container_width=True)
    st.success("✅ Scan Complete")


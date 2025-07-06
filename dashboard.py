import streamlit as st
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

# ========== STRATEGY FUNCTION ==========
def apply_strategies(df):
    if df.empty or len(df) < 20:
        return ["⚠️ Not enough data"]

    if 'Close' not in df or df['Close'].isnull().any() or df['Close'].ndim != 1:
        return ["⚠️ Invalid Close price"]

    try:
        df['RSI'] = RSIIndicator(df['Close'], window=14).rsi()
        df['EMA5'] = EMAIndicator(df['Close'], window=5).ema_indicator()
        df['EMA20'] = EMAIndicator(df['Close'], window=20).ema_indicator()
        df['VWAP'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()
    except Exception as e:
        return [f"⚠️ TA Error: {str(e)}"]

    latest = df.iloc[-1]
    signals = []

    # Strategy 1: RSI + VWAP
    if latest['Close'] > latest['VWAP'] and latest['RSI'] > 55:
        signals.append("RSI+VWAP")

    # Strategy 2: EMA Crossover
    if df['EMA5'].iloc[-2] < df['EMA20'].iloc[-2] and df['EMA5'].iloc[-1] > df['EMA20'].iloc[-1]:
        signals.append("EMA Crossover")

    # Strategy 3: ORB
    opening_range = df.between_time("09:15", "09:30")
    if not opening_range.empty:
        high = opening_range['High'].max()
        low = opening_range['Low'].min()
        if latest['Close'] > high:
            signals.append("ORB Breakout")
        elif latest['Close'] < low:
            signals.append("ORB Breakdown")

    # Strategy 4: Gap and Go
    if len(df) >= 2:
        gap = (df['Open'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100
        if abs(gap) >= 2:
            if gap > 0 and df['Close'].iloc[-1] > df['Open'].iloc[-1]:
                signals.append("Gap Up & Go")
            elif gap < 0 and df['Close'].iloc[-1] < df['Open'].iloc[-1]:
                signals.append("Gap Down & Go")

    # Strategy 5: Volume Breakout
    avg_vol = df['Volume'].rolling(window=10).mean().iloc[-1]
    if df['Volume'].iloc[-1] > 2 * avg_vol:
        signals.append("Volume Breakout")

    # Strategy 6: Reversal @ Support/Resistance
    support = df['Low'].rolling(window=20).min().iloc[-1]
    resistance = df['High'].rolling(window=20).max().iloc[-1]
    if abs(latest['Close'] - support) <= 0.5:
        signals.append("Reversal @ Support")
    elif abs(latest['Close'] - resistance) <= 0.5:
        signals.append("Reversal @ Resistance")

    return signals if signals else ["No setup"]

# ========== STREAMLIT UI ==========
st.set_page_config(page_title="📱 Intraday Screener", layout="centered")
st.markdown("<h2 style='text-align: center;'>📈 Intraday Screener (Mobile View)</h2>", unsafe_allow_html=True)

# User input: Search Stocks
stock_input = st.text_input("🔍 Enter Stock Symbols (comma separated)", value="RELIANCE.NS, INFY.NS")
stocks = [s.strip().upper() for s in stock_input.split(",") if s.strip()]

interval = st.selectbox("⏱️ Time Interval", ["5m", "15m"], index=0)
lookback = st.slider("🕰️ Lookback Days", 1, 5, 3)

results = []

# ========== SCANNING ==========
with st.spinner("📡 Scanning the market..."):
    for stock in stocks:
        try:
            df = yf.download(stock, period=f"{lookback}d", interval=interval, progress=False)
            df.dropna(inplace=True)
            df.index = pd.to_datetime(df.index)
            df = df.between_time("09:15", "15:30")
            signals = apply_strategies(df)
            results.append({"Stock": stock, "Signals": ", ".join(signals)})
        except Exception as e:
            results.append({"Stock": stock, "Signals": f"⚠️ Error: {str(e)}"})

# ========== DISPLAY ==========
result_df = pd.DataFrame(results)
if not result_df.empty:
    st.dataframe(result_df, use_container_width=True)
    st.success("✅ Scan Complete")
else:
    st.warning("⚠️ No signals found.")

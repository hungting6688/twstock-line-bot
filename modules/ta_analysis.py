print("[ta_analysis] ✅ 最新修正版 v2.0（含加權分數與白話建議）")

import pandas as pd
import numpy as np

def analyze_technical_indicators(df, stock_id, strategy):
    score = 0
    signals = []
    suggestions = []

    def safe_append(condition, text, weight):
        nonlocal score
        if condition is None:
            return
        if condition:
            score += weight
            signals.append(f"✔️ {text}")
        else:
            signals.append(f"✖️ {text}")

    try:
        df["MA5"] = df["Close"].rolling(window=5).mean()
        df["MA20"] = df["Close"].rolling(window=20).mean()
        ma_signal = df["MA5"].iloc[-1] > df["MA20"].iloc[-1]
        safe_append(ma_signal, "MA5 > MA20", strategy.get("ma", 0.5))
    except Exception as e:
        signals.append(f"❌ 均線錯誤: {e}")

    try:
        df["EMA12"] = df["Close"].ewm(span=12, adjust=False).mean()
        df["EMA26"] = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = df["EMA12"] - df["EMA26"]
        df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        macd_signal = df["MACD"].iloc[-1] > df["Signal"].iloc[-1]
        safe_append(macd_signal, "MACD 黃金交叉", strategy.get("macd", 1.5))
    except Exception as e:
        signals.append(f"❌ MACD 錯誤: {e}")

    try:
        low_min = df["Low"].rolling(window=9).min()
        high_max = df["High"].rolling(window=9).max()
        rsv = (df["Close"] - low_min) / (high_max - low_min) * 100
        df["K"] = rsv.ewm(com=2).mean()
        df["D"] = df["K"].ewm(com=2).mean()
        kd_signal = df["K"].iloc[-1] > df["D"].iloc[-1] and df["K"].iloc[-1] < 80
        safe_append(kd_signal, "KD 黃金交叉", strategy.get("kd", 1.0))
    except Exception as e:
        signals.append(f"❌ KD 錯誤: {e}")

    try:
        df["RSI"] = compute_rsi(df["Close"], period=14)
        rsi_signal = df["RSI"].iloc[-1] < 30
        safe_append(rsi_signal, "RSI < 30", strategy.get("rsi", 1.0))
    except Exception as e:
        signals.append(f"❌ RSI 錯誤: {e}")

    try:
        if strategy.get("eps_data"):
            eps_info = strategy["eps_data"].get(stock_id)
            if eps_info and eps_info.get("eps", 0) >= 1.5:
                safe_append(True, f"EPS {eps_info['eps']} > 1.5", strategy.get("eps", 1.5))
    except Exception as e:
        signals.append(f"❌ EPS 錯誤: {e}")

    try:
        if strategy.get("eps_data"):
            eps_info = strategy["eps_data"].get(stock_id)
            if eps_info and eps_info.get("dividend", 0) >= 2.0:
                safe_append(True, f"股利 {eps_info['dividend']} > 2", strategy.get("dividend", 1.5))
    except Exception as e:
        signals.append(f"❌ 股利錯誤: {e}")

    suggestion = generate_suggestion(score)
    return {
        "score": round(score, 2),
        "signals": signals,
        "suggestion": suggestion
    }

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def generate_suggestion(score):
    if score >= 5:
        return f"⭐ 分數：{score}（建議列入觀察名單，可積極關注）"
    elif score >= 3:
        return f"⭕ 分數：{score}（可關注，訊號尚可）"
    elif score > 1:
        return f"⚠️ 分數：{score}（訊號偏弱，建議保守）"
    else:
        return f"❌ 分數：{score}（不建議操作）"
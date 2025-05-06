# modules/ta_analysis.py

print("[ta_analysis] ✅ 最新整合版 v2.0（含資料抓取、指標分析、白話建議）")

import pandas as pd
import yfinance as yf
import numpy as np

def get_price_data(stock_id: str, days: int = 60):
    try:
        df = yf.download(f"{stock_id}.TW", period=f"{days}d", progress=False)
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df.dropna(inplace=True)
        return df
    except Exception as e:
        print(f"[get_price_data] {stock_id} 下載失敗：{e}")
        return None

def calculate_indicators(df: pd.DataFrame):
    df["MA5"] = df["Close"].rolling(window=5).mean()
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["RSI"] = compute_rsi(df["Close"], window=14)
    df["MACD_diff"] = compute_macd(df["Close"])
    df["KD_J"] = compute_kd(df)["J"]
    return df

def compute_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_macd(series):
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd - signal

def compute_kd(df):
    low_min = df['Low'].rolling(window=9).min()
    high_max = df['High'].rolling(window=9).max()
    rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
    df['K'] = rsv.ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    return df[["K", "D", "J"]]

def analyze_technical_indicators(stock_id: str):
    df = get_price_data(stock_id)
    if df is None or df.empty or len(df) < 30:
        return None

    try:
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        score = 0
        tags = []
        suggestion = []

        if latest["MA5"] > latest["MA20"]:
            score += 1
            tags.append("短均上穿")
            suggestion.append("短期均線上穿，趨勢偏多。")
        if latest["RSI"] < 30:
            score += 1
            tags.append("RSI低檔")
            suggestion.append("RSI低於30，可能超賣反彈。")
        if latest["RSI"] > 70:
            tags.append("RSI過熱")
            suggestion.append("RSI高於70，可能短期回檔。")
        if latest["MACD_diff"] > 0:
            score += 1
            tags.append("MACD正乖離")
            suggestion.append("MACD柱狀體轉正，動能偏多。")
        if latest["KD_J"] > latest["K"] > latest["D"]:
            score += 1
            tags.append("KD黃金交叉")
            suggestion.append("KD黃金交叉，可能進入上漲趨勢。")

        final_suggestion = " ".join(suggestion)
        return {
            "stock_id": stock_id,
            "score": round(score, 1),
            "tags": tags,
            "summary": final_suggestion
        }
    except Exception as e:
        print(f"[ta_analysis] {stock_id} 分析失敗：{e}")
        return None

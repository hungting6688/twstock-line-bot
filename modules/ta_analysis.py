print("[ta_analysis] ✅ 最新修正版 v1.4")

import yfinance as yf
import pandas as pd
import numpy as np

def generate_suggestion_text(score, comments):
    if score >= 6:
        return "技術面偏多：" + " + ".join(comments) + "，建議可考慮分批佈局或短線進場。"
    elif score >= 4:
        return "技術面轉強：" + " + ".join(comments) + "，建議可觀察是否有突破走勢再做進場。"
    elif score >= 2:
        return "技術面普通：" + " + ".join(comments) + "，建議暫不進場，可保守觀望。"
    else:
        return "多數技術指標偏弱：" + " + ".join(comments) + "，建議避開或保守等待轉強訊號。"

def analyze_technical_indicators(stock_ids: list[str]) -> dict:
    results = {}

    for sid in stock_ids:
        try:
            print(f"[ta_analysis] 🔍 分析 {sid}")
            df = yf.download(f"{sid}.TW", period="3mo", interval="1d", progress=False)
            if df.empty or len(df) < 30:
                continue

            df = df.dropna()
            close = df["Close"]
            low = df["Low"]
            high = df["High"]

            # --- MACD ---
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            dif = ema12 - ema26
            dea = dif.ewm(span=9, adjust=False).mean()
            macd_hist = dif - dea

            # --- KD ---
            low_min = low.rolling(window=9).min()
            high_max = high.rolling(window=9).max()
            denominator = (high_max - low_min).replace(0, np.nan)
            rsv = ((close - low_min) / denominator * 100).fillna(0)
            k = rsv.ewm(com=2).mean()
            d = k.ewm(com=2).mean()

            # --- RSI ---
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            rsi = rsi.fillna(50)

            # --- MA ---
            ma5 = close.rolling(window=5).mean()
            ma20 = close.rolling(window=20).mean()
            ma60 = close.rolling(window=60).mean()

            score = 0
            comments = []

            if macd_hist.iloc[-1] > 0 and dif.iloc[-1] > dea.iloc[-1]:
                score += 2
                comments.append("MACD 剛翻多")

            if k.iloc[-1] > d.iloc[-1] and k.iloc[-1] < 60:
                score += 1.5
                comments.append("KD 黃金交叉")

            if rsi.iloc[-1] < 30:
                score += 1
                comments.append("RSI 超跌")

            if close.iloc[-1] > ma5.iloc[-1]:
                score += 1
                comments.append("站上 5 日均線")

            if close.iloc[-1] > ma20.iloc[-1]:
                score += 1
                comments.append("站上 20 日均線")

            if close.iloc[-1] < ma20.iloc[-1] and rsi.iloc[-1] < 40:
                comments.append("中期偏弱")

            is_weak = (
                rsi.iloc[-1] < 30 and
                close.iloc[-1] < ma5.iloc[-1] and
                close.iloc[-1] < ma20.iloc[-1] and
                close.iloc[-1] < ma60.iloc[-1]
            )

            suggestion = generate_suggestion_text(score, comments)

            results[sid] = {
                "score": round(score, 2),
                "suggestion": suggestion,
                "is_weak": is_weak
            }

        except Exception as e:
            print(f"[ta_analysis] ❌ {sid} 分析失敗：{e}")
            continue

    return results

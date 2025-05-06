# modules/ta_analysis.py

import pandas as pd
import numpy as np

def analyze_technical_indicators(df, stock_id=None, weights=None):
    print(f"[ta_analysis] 分析中：{stock_id}")
    score = 0
    signals = []
    suggestions = []

    try:
        # 移動平均線
        ma5 = df['Close'].rolling(window=5).mean()
        ma20 = df['Close'].rolling(window=20).mean()
        if ma5.iloc[-1] > ma20.iloc[-1]:
            score += weights.get("ma", 0)
            signals.append("短期均線多頭")
        else:
            suggestions.append("短期均線未上穿")

        # MACD
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        if macd.iloc[-1] > signal.iloc[-1]:
            score += weights.get("macd", 0)
            signals.append("MACD 黃金交叉")
        else:
            suggestions.append("MACD 尚未交叉")

        # KD 指標
        low_min = df['Low'].rolling(window=9).min()
        high_max = df['High'].rolling(window=9).max()
        rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
        k = rsv.ewm(com=2).mean()
        d = k.ewm(com=2).mean()
        if k.iloc[-1] > d.iloc[-1] and k.iloc[-1] < 80:
            score += weights.get("kd", 0)
            signals.append("KD 黃金交叉")
        else:
            suggestions.append("KD 未交叉或過熱")

        # RSI
        delta = df['Close'].diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        avg_gain = up.rolling(window=14).mean()
        avg_loss = down.rolling(window=14).mean()
        rs = avg_gain / (avg_loss + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        if rsi.iloc[-1] < 30:
            suggestions.append("RSI 過低，可能超跌")
        elif rsi.iloc[-1] > 70:
            suggestions.append("RSI 過高，可能超買")
        else:
            score += weights.get("rsi", 0)
            signals.append("RSI 穩定區間")

        # 布林通道
        mid = df['Close'].rolling(window=20).mean()
        std = df['Close'].rolling(window=20).std()
        upper = mid + 2 * std
        lower = mid - 2 * std
        if df['Close'].iloc[-1] < lower.iloc[-1]:
            suggestions.append("跌破布林下緣，可能反彈")
        elif df['Close'].iloc[-1] > upper.iloc[-1]:
            suggestions.append("突破布林上緣，注意拉回")
        else:
            score += weights.get("boll", 0)
            signals.append("布林通道穩定")

        # 白話建議邏輯
        if score >= 5:
            advice = "建議立即列入關注清單"
        elif score >= 3.5:
            advice = "建議密切觀察"
        elif score >= 2:
            advice = "建議暫不進場"
        else:
            advice = "不建議操作"

        return {
            "stock_id": stock_id,
            "score": round(score, 2),
            "signals": signals,
            "suggestions": suggestions,
            "advice": advice
        }

    except Exception as e:
        print(f"[ta_analysis] {stock_id} 分析失敗：{e}")
        return None
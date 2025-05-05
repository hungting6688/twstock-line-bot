import pandas as pd

def analyze_signals(df: pd.DataFrame):
    score = 0
    signals = []
    weak_signals = []

    # RSI 超跌區
    if df["RSI_6"] < 30:
        score += 1.0
        signals.append("🟢 RSI < 30 超跌區（反彈機會）")
    elif df["RSI_6"] > 70:
        score -= 1.0
        weak_signals.append("🔴 RSI > 70 過熱區（短線留意高檔）")

    # KD 黃金交叉
    if df["K"] > df["D"]:
        score += 0.8
        signals.append("🟢 KD 黃金交叉（技術轉強）")
    elif df["K"] < 20 and df["D"] < 20:
        weak_signals.append("🔴 KD 低檔盤整（暫無明確趨勢）")

    # 均線突破
    if df["MA_5"] > df["MA_20"]:
        score += 1.0
        signals.append("🟢 MA5 > MA20（短線翻多）")
    elif df["MA_5"] < df["MA_20"]:
        score -= 0.8
        weak_signals.append("🔴 MA5 < MA20（空頭排列）")

    # MACD 多頭動能
    if df["MACD"] > 0 and df["DIF"] > df["MACD"]:
        score += 1.2
        signals.append("🟢 MACD 多頭動能（上升趨勢）")
    elif df["MACD"] < 0 and df["DIF"] < df["MACD"]:
        score -= 1.2
        weak_signals.append("🔴 MACD 空頭動能（下跌趨勢）")

    # 布林通道低檔
    if df["Close"] < df["BB_lower"]:
        score += 0.8
        signals.append("🟢 跌破布林下緣（反彈機會）")
    elif df["Close"] > df["BB_upper"]:
        weak_signals.append("🔴 站上布林上緣（偏熱須觀察）")

    # 收盤價分析
    if df["Close"] > df["MA_20"]:
        score += 0.5
        signals.append("🟢 收盤價 > MA20（中線偏多）")
    elif df["Close"] < df["MA_60"]:
        score -= 0.5
        weak_signals.append("🔴 收盤價 < MA60（偏空）")

    return {
        "score": round(score, 2),
        "signals": signals,
        "weak_signals": weak_signals,
    }

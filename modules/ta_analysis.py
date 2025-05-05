# modules/ta_analysis.py

import pandas as pd

def analyze_signals(df: pd.DataFrame) -> dict:
    signals = {}
    scores = 0
    explanations = []
    weak_flags = []

    close = df["Close"].values
    high = df["High"].values
    low = df["Low"].values

    # RSI6
    delta = pd.Series(close).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=6).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=6).mean()
    rs = gain / loss
    rsi6 = 100 - (100 / (1 + rs))
    latest_rsi = rsi6.iloc[-1]

    if latest_rsi < 30:
        scores += 1.0
        explanations.append("🟢 RSI < 30 超跌區（技術面反彈機會）")
    elif latest_rsi > 70:
        explanations.append("🔴 RSI > 70 過熱區（短線漲多風險）")
        weak_flags.append("RSI")

    # KD
    low_k = pd.Series(low).rolling(window=9).min()
    high_k = pd.Series(high).rolling(window=9).max()
    rsv = (pd.Series(close) - low_k) / (high_k - low_k) * 100
    k = rsv.ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    if k.iloc[-1] > d.iloc[-1]:
        scores += 0.7
        explanations.append("🟢 KD 黃金交叉（短期轉強）")
    elif k.iloc[-1] < d.iloc[-1]:
        explanations.append("🔴 KD 死亡交叉（技術轉弱）")
        weak_flags.append("KD")

    # MA5 vs MA20
    ma5 = pd.Series(close).rolling(window=5).mean()
    ma20 = pd.Series(close).rolling(window=20).mean()
    if ma5.iloc[-1] > ma20.iloc[-1]:
        scores += 0.5
        explanations.append("🟢 MA5 > MA20（短期趨勢翻多）")
    else:
        explanations.append("🔴 MA5 < MA20（短期仍偏弱）")

    # MACD
    ema12 = pd.Series(close).ewm(span=12).mean()
    ema26 = pd.Series(close).ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    if macd.iloc[-1] > signal.iloc[-1]:
        scores += 0.7
        explanations.append("🟢 MACD 黃金交叉（中期轉強）")
    elif macd.iloc[-1] < signal.iloc[-1]:
        explanations.append("🔴 MACD 死亡交叉（中期走弱）")
        weak_flags.append("MACD")

    # 布林通道
    ma20 = pd.Series(close).rolling(window=20).mean()
    std20 = pd.Series(close).rolling(window=20).std()
    upper = ma20 + 2 * std20
    lower = ma20 - 2 * std20
    if close[-1] < lower.iloc[-1]:
        scores += 0.5
        explanations.append("🟢 跌破布林下軌（可能超跌反彈）")
    elif close[-1] > upper.iloc[-1]:
        explanations.append("🔴 突破布林上軌（短期可能漲多）")
        weak_flags.append("Bollinger")

    return {
        "score": round(scores, 2),
        "suggestions": explanations,
        "is_weak": len(weak_flags) >= 2
    }

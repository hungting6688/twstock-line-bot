# modules/ta_analysis.py

import pandas as pd

def analyze_technical_indicators(df: pd.DataFrame):
    score = 0
    signals = []

    df = df.copy()
    df["close"] = df["close"].astype(float)

    # RSI6
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(6).mean()
    avg_loss = loss.rolling(6).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df["RSI6"] = 100 - (100 / (1 + rs))
    latest_rsi = df["RSI6"].iloc[-1]
    if latest_rsi < 30:
        score += 1
        signals.append("🟢 RSI < 30 超跌區，留意反彈")
    elif latest_rsi > 70:
        score -= 1
        signals.append("🔻 RSI > 70 過熱區，提防拉回")

    # KD (9, 3)
    low_min = df["low"].rolling(window=9).min()
    high_max = df["high"].rolling(window=9).max()
    rsv = (df["close"] - low_min) / (high_max - low_min + 1e-9) * 100
    df["K"] = rsv.ewm(com=2).mean()
    df["D"] = df["K"].ewm(com=2).mean()
    if df["K"].iloc[-2] < df["D"].iloc[-2] and df["K"].iloc[-1] > df["D"].iloc[-1]:
        score += 1
        signals.append("🟢 KD 黃金交叉，技術轉強")
    elif df["K"].iloc[-2] > df["D"].iloc[-2] and df["K"].iloc[-1] < df["D"].iloc[-1]:
        score -= 1
        signals.append("🔻 KD 死亡交叉，趨勢轉弱")

    # MACD
    ema12 = df["close"].ewm(span=12).mean()
    ema26 = df["close"].ewm(span=26).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9).mean()
    if macd_line.iloc[-2] < signal_line.iloc[-2] and macd_line.iloc[-1] > signal_line.iloc[-1]:
        score += 1
        signals.append("🟢 MACD 黃金交叉，趨勢轉強")
    elif macd_line.iloc[-2] > signal_line.iloc[-2] and macd_line.iloc[-1] < signal_line.iloc[-1]:
        score -= 1
        signals.append("🔻 MACD 死亡交叉，趨勢轉弱")

    # MA5 vs MA20
    df["MA5"] = df["close"].rolling(window=5).mean()
    df["MA20"] = df["close"].rolling(window=20).mean()
    if df["MA5"].iloc[-2] < df["MA20"].iloc[-2] and df["MA5"].iloc[-1] > df["MA20"].iloc[-1]:
        score += 1
        signals.append("🟢 短均穿越長均，趨勢翻多")
    elif df["MA5"].iloc[-2] > df["MA20"].iloc[-2] and df["MA5"].iloc[-1] < df["MA20"].iloc[-1]:
        score -= 1
        signals.append("🔻 均線跌破，趨勢轉弱")

    # Bollinger Band
    df["MB"] = df["close"].rolling(20).mean()
    df["STD"] = df["close"].rolling(20).std()
    df["UB"] = df["MB"] + 2 * df["STD"]
    df["LB"] = df["MB"] - 2 * df["STD"]
    if df["close"].iloc[-1] > df["UB"].iloc[-1]:
        score -= 1
        signals.append("🔻 股價突破上緣，短期過熱")
    elif df["close"].iloc[-1] < df["LB"].iloc[-1]:
        score += 1
        signals.append("🟢 股價跌破下緣，可能反彈")

    return signals, score

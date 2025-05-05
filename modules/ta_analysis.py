import pandas as pd

def analyze_signals(price_df: pd.DataFrame) -> dict:
    result = {
        "score": 0,
        "reasons": [],
        "warnings": []
    }

    # 計算技術指標
    price_df['MA5'] = price_df['close'].rolling(window=5).mean()
    price_df['MA20'] = price_df['close'].rolling(window=20).mean()
    price_df['RSI6'] = compute_rsi(price_df['close'], window=6)
    price_df['RSI14'] = compute_rsi(price_df['close'], window=14)
    price_df['K'], price_df['D'] = compute_kd(price_df)
    price_df['MACD'], price_df['MACD_signal'] = compute_macd(price_df['close'])

    latest = price_df.iloc[-1]

    # RSI 判斷
    if latest['RSI6'] < 30:
        result["score"] += 1.0
        result["reasons"].append("🟢 RSI < 30 超跌區（短期可能反彈）")
    elif latest['RSI6'] > 70:
        result["warnings"].append("🔴 RSI > 70 超買區（短線有壓）")

    # KD 黃金交叉
    if latest['K'] > latest['D']:
        result["score"] += 1.0
        result["reasons"].append("🟢 KD 黃金交叉（轉強訊號）")
    else:
        result["warnings"].append("🔴 KD 死亡交叉（轉弱訊號）")

    # 均線判斷
    if latest['MA5'] > latest['MA20']:
        result["score"] += 0.5
        result["reasons"].append("🟢 MA5 > MA20（短均穿越長均）")
    else:
        result["warnings"].append("🔴 MA5 < MA20（短線偏弱）")

    # MACD 黃金交叉
    if latest['MACD'] > latest['MACD_signal']:
        result["score"] += 1.0
        result["reasons"].append("🟢 MACD 黃金交叉（中線偏多）")
    else:
        result["warnings"].append("🔴 MACD 死亡交叉（中線轉弱）")

    # 判斷極弱股（附加提示）
    if latest['RSI6'] < 20 and latest['MACD'] < latest['MACD_signal']:
        result["warnings"].append("⚠️ RSI 過低 + MACD 死亡交叉，留意極弱走勢")

    return result


def compute_rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_kd(df: pd.DataFrame, n=9) -> tuple:
    low_min = df['low'].rolling(window=n).min()
    high_max = df['high'].rolling(window=n).max()
    rsv = (df['close'] - low_min) / (high_max - low_min + 1e-9) * 100
    k = rsv.ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    return k, d


def compute_macd(series: pd.Series, short=12, long=26, signal=9) -> tuple:
    ema_short = series.ewm(span=short).mean()
    ema_long = series.ewm(span=long).mean()
    macd = ema_short - ema_long
    macd_signal = macd.ewm(span=signal).mean()
    return macd, macd_signal

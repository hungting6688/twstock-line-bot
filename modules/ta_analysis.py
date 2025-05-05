import pandas as pd

def calculate_rsi(df, period=6):
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    df[f"RSI{period}"] = rsi
    return df

def calculate_kd(df, period=9):
    low_min = df['low'].rolling(window=period).min()
    high_max = df['high'].rolling(window=period).max()
    rsv = 100 * (df['close'] - low_min) / (high_max - low_min)
    df['K'] = rsv.ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    return df

def calculate_macd(df, fast=12, slow=26, signal=9):
    df["EMA_fast"] = df["close"].ewm(span=fast, adjust=False).mean()
    df["EMA_slow"] = df["close"].ewm(span=slow, adjust=False).mean()
    df["MACD"] = df["EMA_fast"] - df["EMA_slow"]
    df["MACD_signal"] = df["MACD"].ewm(span=signal, adjust=False).mean()
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]
    return df

def calculate_ma(df, periods=[5, 20]):
    for p in periods:
        df[f"MA{p}"] = df["close"].rolling(window=p).mean()
    return df

def calculate_bollinger_bands(df, window=20, num_std=2):
    rolling_mean = df["close"].rolling(window=window).mean()
    rolling_std = df["close"].rolling(window=window).std()
    df["BOLL_upper"] = rolling_mean + (rolling_std * num_std)
    df["BOLL_lower"] = rolling_mean - (rolling_std * num_std)
    return df

def apply_all_indicators(df):
    df = calculate_rsi(df, period=6)
    df = calculate_kd(df)
    df = calculate_macd(df)
    df = calculate_ma(df)
    df = calculate_bollinger_bands(df)
    return df

import pandas as pd
import numpy as np

def generate_ta_signals(df):
    df = df.copy()

    # MACD
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_signal'] = df['macd'] > df['signal']

    # KD
    low_min = df['low'].rolling(window=9).min()
    high_max = df['high'].rolling(window=9).max()
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    df['kdj_k'] = rsv.ewm(com=2).mean()
    df['kdj_d'] = df['kdj_k'].ewm(com=2).mean()
    df['kdj_signal'] = (df['kdj_k'] > df['kdj_d']) & (df['kdj_k'] < 40)

    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df['rsi_14'] = 100 - (100 / (1 + rs))
    df['rsi_signal'] = df['rsi_14'] > 50

    # MA
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma60'] = df['close'].rolling(window=60).mean()
    df['ma_signal'] = (df['close'] > df['ma5']) & (df['close'] > df['ma20']) & (df['close'] > df['ma60'])

    # Bollinger Bands
    ma20 = df['close'].rolling(window=20).mean()
    std = df['close'].rolling(window=20).std()
    df['bb_upper'] = ma20 + 2 * std
    df['bb_middle'] = ma20
    df['bb_lower'] = ma20 - 2 * std
    df['bollinger_signal'] = df['close'] > df['bb_middle']

    return df

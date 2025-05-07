import pandas as pd
import numpy as np

def generate_technical_indicators(df):
    print("[ta_generator] ✅ 計算技術指標中...")

    df = df.copy()

    # MACD 計算
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_signal'] = df['macd'] > df['signal']

    # KD 計算
    low_min = df['low'].rolling(window=9).min()
    high_max = df['high'].rolling(window=9).max()
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    df['kdj_k'] = rsv.ewm(com=2).mean()
    df['kdj_d'] = df['kdj_k'].ewm(com=2).mean()
    df['kdj_signal'] = df['kdj_k'] > df['kdj_d']

    # RSI 計算
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df['rsi_14'] = 100 - (100 / (1 + rs))
    df['rsi_signal'] = df['rsi_14'] > 50

    # 均線站上
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma60'] = df['close'].rolling(window=60).mean()
    df['ma_signal'] = (df['close'] > df['ma5']) & (df['close'] > df['ma20']) & (df['close'] > df['ma60'])

    # 布林通道
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    df['bb_std'] = df['close'].rolling(window=20).std()
    df['bollinger_signal'] = df['close'] > df['bb_middle']

    # 只保留最新一筆資料
    latest_row = df.iloc[-1:]
    return latest_row.reset_index(drop=True)

def batch_generate_indicators(price_data_dict):
    print("[ta_generator] ⏳ 批次生成所有股票技術指標...")
    all_results = []
    for stock_id, df in price_data_dict.items():
        try:
            if df is None or df.empty or len(df) < 60:
                continue
            latest = generate_technical_indicators(df)
            latest['stock_id'] = stock_id
            all_results.append(latest)
        except Exception as e:
            print(f"[ta_generator] ⚠️ {stock_id} 技術指標處理失敗: {e}")

    if all_results:
        return pd.concat(all_results, ignore_index=True)
    else:
        return pd.DataFrame()

import pandas as pd

def generate_technical_signals(df: pd.DataFrame) -> pd.DataFrame:
    print("[ta_generator] ✅ 產生技術指標欄位")

    # 確保所需欄位存在
    required_cols = ["macd", "macd_signal", "kdj_k", "kdj_d", "rsi", "close", "ma_5", "ma_20", "ma_60", "ma_240"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0

    # 強勢技術指標訊號
    df["macd_signal"] = df["macd"] > df["macd_signal"]
    df["kdj_signal"] = df["kdj_k"] > df["kdj_d"]
    df["rsi_signal"] = df["rsi"] > 50
    df["ma_signal"] = df["close"] > df["ma_20"]
    df["bollinger_signal"] = df["close"] > df["ma_20"]  # 可視為站上中軌

    # 弱勢訊號
    df["weak_macd"] = df["macd"] < df["macd_signal"]  # MACD 死亡交叉
    df["rsi_oversold"] = df["rsi"] < 30
    df["ma_breakdown"] = df["close"] < df["ma_240"]  # 跌破年線
    df["kd_dead_cross"] = (df["kdj_k"] < df["kdj_d"]) & (df["kdj_k"].shift(1) > df["kdj_d"].shift(1))

    # 弱勢信號計數
    df["weak_signal"] = (
        df["weak_macd"].astype(int) +
        df["rsi_oversold"].astype(int) +
        df["ma_breakdown"].astype(int) +
        df["kd_dead_cross"].astype(int)
    )

    return df

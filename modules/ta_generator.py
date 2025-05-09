import pandas as pd
import numpy as np

def generate_technical_signals(df):
    print("[ta_generator] ✅ 產生技術指標欄位")

    df = df.copy()
    df["ma_signal"] = df["close"] > df["ma20"]
    df["bollinger_signal"] = df["close"] > df["bollinger_mid"]
    df["macd_signal"] = df["macd"] > df["macd_signal_line"]
    df["kdj_signal"] = df["kdj_k"] > df["kdj_d"]
    df["rsi_signal"] = df["rsi"] > 50

    # 加入走弱訊號
    df["weak_signal"] = 0
    df.loc[df["close"] < df["ma20"], "weak_signal"] += 1
    df.loc[df["kdj_k"] < df["kdj_d"], "weak_signal"] += 1
    df.loc[df["macd"] < df["macd_signal_line"], "weak_signal"] += 1

    return df

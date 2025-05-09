# ✅ ta_generator.py（包含弱勢訊號欄位）
def generate_technical_signals(df):
    print("[ta_generator] ✅ 產生技術指標欄位")
    df = df.copy()

    # MACD 黃金交叉
    df["macd_signal"] = df["macd"] > df["macd_signal_line"]
    df["macd_weak"] = df["macd"] < df["macd_signal_line"]

    # KD 黃金交叉
    df["kdj_signal"] = df["kdj_k"] > df["kdj_d"]
    df["kdj_weak"] = df["kdj_k"] < df["kdj_d"]

    # RSI 強勢區（>50）
    df["rsi_signal"] = df["rsi"] > 50
    df["rsi_weak"] = df["rsi"] < 30

    # 均線判斷（使用 ma20 為基準）
    if "ma20" in df.columns:
        df["ma_signal"] = df["close"] > df["ma20"]
        df["ma_weak"] = df["close"] < df["ma20"]
    elif "ma10" in df.columns:
        df["ma_signal"] = df["close"] > df["ma10"]
        df["ma_weak"] = df["close"] < df["ma10"]
    else:
        df["ma_signal"] = False
        df["ma_weak"] = False

    # 布林通道偏多（收盤 > 中軌）
    if "bollinger_mid" in df.columns:
        df["bollinger_signal"] = df["close"] > df["bollinger_mid"]
        df["bollinger_weak"] = df["close"] < df["bollinger_mid"]
    else:
        df["bollinger_signal"] = False
        df["bollinger_weak"] = False

    # 弱勢統計欄位
    df["weak_signal"] = (
        df[["macd_weak", "kdj_weak", "rsi_weak", "ma_weak", "bollinger_weak"]]
        .sum(axis=1)
    )

    return df

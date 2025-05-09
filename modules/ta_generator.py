import pandas as pd
import numpy as np

def generate_technical_signals(df):
    print("[ta_generator] ✅ 產生技術指標欄位")

    try:
        # 檢查必要欄位
        if not all(col in df.columns for col in ["close"]):
            raise ValueError("缺少必要欄位：close")

        # MACD 指標
        exp12 = df["close"].ewm(span=12, adjust=False).mean()
        exp26 = df["close"].ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        signal = macd.ewm(span=9, adjust=False).mean()
        df["macd_signal"] = (macd > signal)

        # KD 指標
        low_min = df["close"].rolling(window=9).min()
        high_max = df["close"].rolling(window=9).max()
        rsv = (df["close"] - low_min) / (high_max - low_min) * 100
        k = rsv.ewm(com=2).mean()
        d = k.ewm(com=2).mean()
        df["kdj_signal"] = (k > d) & (k < 40)

        # RSI 指標
        delta = df["close"].diff()
        gain = np.where(delta > 0, delta, 0.0)
        loss = np.where(delta < 0, -delta, 0.0)
        avg_gain = pd.Series(gain).rolling(window=14).mean()
        avg_loss = pd.Series(loss).rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        df["rsi_signal"] = rsi > 50

        # 均線（MA）
        ma5 = df["close"].rolling(window=5).mean()
        ma20 = df["close"].rolling(window=20).mean()
        ma60 = df["close"].rolling(window=60).mean()
        df["ma_signal"] = (df["close"] > ma5) & (df["close"] > ma20) & (df["close"] > ma60)

        # 布林通道
        ma20_bb = df["close"].rolling(window=20).mean()
        std_bb = df["close"].rolling(window=20).std()
        upper = ma20_bb + 2 * std_bb
        lower = ma20_bb - 2 * std_bb
        df["bollinger_signal"] = df["close"] > ma20_bb

        return df

    except Exception as e:
        print(f"[ta_generator] ⚠️ 技術指標處理失敗: {e}")
        raise

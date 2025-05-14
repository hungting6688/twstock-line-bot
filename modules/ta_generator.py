# modules/ta_generator.py
print("[ta_generator] ✅ 已載入最新版 (修正 KD 錯誤)")

import yfinance as yf
import pandas as pd
from tqdm import tqdm

def generate_ta_signals(stock_ids: list) -> pd.DataFrame:
    result = []

    for stock_id in tqdm(stock_ids, desc="[ta_generator] 計算技術指標"):
        try:
            df = yf.download(f"{stock_id}.TW", period="60d", progress=False)
            if df.empty or len(df) < 30:
                continue

            df["Close"] = df["Close"].astype(float)
            close = df["Close"]

            # 移動平均線
            ma5 = close.rolling(window=5).mean()
            ma20 = close.rolling(window=20).mean()
            ma60 = close.rolling(window=60).mean()

            # RSI (14)
            delta = close.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            # KD 指標
            low_min = df['Low'].rolling(window=9).min()
            high_max = df['High'].rolling(window=9).max()
            rsv = (close - low_min) / (high_max - low_min) * 100
            k = rsv.copy()
            d = rsv.copy()
            k.iloc[0] = 50
            d.iloc[0] = 50
            for i in range(1, len(rsv)):
                k.iloc[i] = k.iloc[i - 1] * 2/3 + rsv.iloc[i] * 1/3
                d.iloc[i] = d.iloc[i - 1] * 2/3 + k.iloc[i] * 1/3

            # MACD
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()

            latest = {
                "證券代號": stock_id,
                "RSI": round(rsi.iloc[-1], 2),
                "K": round(k.iloc[-1], 2),
                "D": round(d.iloc[-1], 2),
                "MACD": round(macd_line.iloc[-1] - signal_line.iloc[-1], 2),
                "收盤價": close.iloc[-1],
                "均線": 1 if close.iloc[-1] > ma20.iloc[-1] else 0,
                "布林通道": 1 if close.iloc[-1] > ma20.iloc[-1] + 2 * close.rolling(window=20).std().iloc[-1] else 0,
            }
            result.append(latest)
        except Exception as e:
            print(f"[ta_generator] ⚠️ 技術指標失敗：{stock_id} - {e}")
            continue

    return pd.DataFrame(result)

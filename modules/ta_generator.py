print("[ta_generator] ✅ 已載入最新版（含 safe_last 修正）")

import yfinance as yf
import pandas as pd
from tqdm import tqdm

def safe_last(series):
    try:
        return float(series.iloc[-1])
    except Exception:
        return None

def generate_ta_signals(stock_ids):
    print("[ta_generator] ⏳ 開始計算技術指標...")
    results = []

    for stock_id in tqdm(stock_ids, desc="[ta_generator] 計算技術指標"):
        try:
            clean_id = str(stock_id).replace("=\"", "").replace("\"", "").strip()
            df = yf.download(f"{clean_id}.TW", period="60d", progress=False)

            if df.empty or len(df) < 30:
                continue
            df = df.dropna().copy()
            df.reset_index(inplace=True)

            # MACD
            df["EMA12"] = df["Close"].ewm(span=12).mean()
            df["EMA26"] = df["Close"].ewm(span=26).mean()
            df["MACD"] = df["EMA12"] - df["EMA26"]
            df["Signal"] = df["MACD"].ewm(span=9).mean()
            macd_signal = int(safe_last(df["MACD"]) > safe_last(df["Signal"]))

            # KD
            low_min = df["Low"].rolling(window=9).min()
            high_max = df["High"].rolling(window=9).max()
            rsv = (df["Close"] - low_min) / (high_max - low_min) * 100
            df["K"] = rsv.ewm(com=2).mean()
            df["D"] = df["K"].ewm(com=2).mean()
            k = safe_last(df["K"]) or 0
            d = safe_last(df["D"]) or 0

            # RSI
            delta = df["Close"].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_val = safe_last(rsi) or 0

            # 均線
            ma5 = df["Close"].rolling(window=5).mean()
            ma20 = df["Close"].rolling(window=20).mean()
            ma_score = int((safe_last(ma5) or 0) > (safe_last(ma20) or 0))

            # 布林通道
            mavg = df["Close"].rolling(window=20).mean()
            std = df["Close"].rolling(window=20).std()
            upper = mavg + 2 * std
            bb_signal = int((safe_last(df["Close"]) or 0) > (safe_last(upper) or 0))

            results.append({
                "證券代號": clean_id,
                "MACD": macd_signal,
                "K": k,
                "D": d,
                "RSI": rsi_val,
                "均線": ma_score,
                "布林通道": bb_signal,
            })

        except Exception as e:
            print(f"[ta_generator] ⚠️ 技術指標失敗：{stock_id} - {e}")

    return pd.DataFrame(results)
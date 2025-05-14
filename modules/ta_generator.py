print("[ta_generator] ✅ 已載入最新版（修正 ambiguous 與 float warning）")

import yfinance as yf
import pandas as pd
from tqdm import tqdm

def safe_float(series):
    try:
        return float(series.iloc[-1])
    except:
        return 0.0

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
            macd_signal = 0
            if not df["MACD"].isna().all() and not df["Signal"].isna().all():
                macd_signal = int(safe_float(df["MACD"]) > safe_float(df["Signal"]))

            # KD
            low_min = df["Low"].rolling(window=9).min()
            high_max = df["High"].rolling(window=9).max()
            rsv = (df["Close"] - low_min) / (high_max - low_min) * 100
            df["K"] = rsv.ewm(com=2).mean()
            df["D"] = df["K"].ewm(com=2).mean()
            k = safe_float(df["K"])
            d = safe_float(df["D"])

            # RSI
            delta = df["Close"].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_val = safe_float(rsi)

            # MA
            ma5 = df["Close"].rolling(window=5).mean()
            ma20 = df["Close"].rolling(window=20).mean()
            ma_score = int(safe_float(ma5) > safe_float(ma20))

            # Bollinger Band
            mavg = df["Close"].rolling(window=20).mean()
            std = df["Close"].rolling(window=20).std()
            upper = mavg + 2 * std
            bb_signal = int(df["Close"].iloc[-1] > upper.iloc[-1]) if not upper.isna().all() else 0

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
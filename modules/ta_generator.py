print("[ta_generator] ✅ 已載入最新版（加速與清洗修正）")

import yfinance as yf
import pandas as pd
from tqdm import tqdm

def generate_technical_indicators(stock_ids):
    print("[ta_generator] ⏳ 開始計算技術指標...")
    results = []

    for stock_id in tqdm(stock_ids, desc="[ta_generator] 計算技術指標"):
        try:
            stock_id = str(stock_id).replace("=\"", "").replace("\"", "").strip()
            df = yf.download(f"{stock_id}.TW", period="60d", progress=False, threads=False)

            if df.empty or len(df) < 30:
                continue

            df = df.dropna().copy()
            df.reset_index(inplace=True)

            # MACD
            df["EMA12"] = df["Close"].ewm(span=12).mean()
            df["EMA26"] = df["Close"].ewm(span=26).mean()
            df["MACD"] = df["EMA12"] - df["EMA26"]
            df["Signal"] = df["MACD"].ewm(span=9).mean()
            macd_signal = int(df["MACD"].iloc[-1] > df["Signal"].iloc[-1])

            # KD
            low_min = df["Low"].rolling(window=9).min()
            high_max = df["High"].rolling(window=9).max()
            rsv = (df["Close"] - low_min) / (high_max - low_min) * 100
            df["K"] = rsv.ewm(com=2).mean()
            df["D"] = df["K"].ewm(com=2).mean()
            k_val = float(df["K"].iloc[-1])
            d_val = float(df["D"].iloc[-1])
            kd_cross = int(k_val > d_val and k_val < 80)

            # RSI
            delta = df["Close"].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_val = float(rsi.iloc[-1]) if not rsi.isna().all() else 0
            rsi_score = int(rsi_val > 50)

            # MA
            ma5 = df["Close"].rolling(window=5).mean()
            ma20 = df["Close"].rolling(window=20).mean()
            ma_signal = int(ma5.iloc[-1] > ma20.iloc[-1]) if not ma5.isna().all() and not ma20.isna().all() else 0

            # Bollinger Band
            mavg = df["Close"].rolling(window=20).mean()
            std = df["Close"].rolling(window=20).std()
            upper = mavg + 2 * std
            bb_signal = int(df["Close"].iloc[-1] > upper.iloc[-1]) if not mavg.isna().all() else 0

            score = macd_signal + kd_cross + rsi_score + ma_signal + bb_signal

            results.append({
                "stock_id": stock_id,
                "MACD": macd_signal,
                "K": k_val,
                "D": d_val,
                "RSI": rsi_val,
                "MA": ma_signal,
                "Bollinger": bb_signal,
                "score": score,
                "is_weak": rsi_val < 30 and ma_signal == 0,
            })

        except Exception as e:
            print(f"[ta_generator] ⚠️ 技術指標失敗：{stock_id} - {e}")

    return pd.DataFrame(results)

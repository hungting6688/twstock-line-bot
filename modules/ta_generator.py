print("[ta_generator] ✅ 已載入最新版 (修正 KD 錯誤)")

import yfinance as yf
import pandas as pd

def generate_technical_indicators(stock_ids):
    results = []

    for stock_id in stock_ids:
        try:
            symbol = f"{stock_id}.TW"
            df = yf.download(symbol, period="3mo", interval="1d", progress=False)

            if df is None or df.empty or len(df) < 20:
                continue

            df["MA20"] = df["Close"].rolling(window=20).mean()
            df["STD"] = df["Close"].rolling(window=20).std()
            df["Upper"] = df["MA20"] + 2 * df["STD"]
            df["Lower"] = df["MA20"] - 2 * df["STD"]

            df["EMA12"] = df["Close"].ewm(span=12, adjust=False).mean()
            df["EMA26"] = df["Close"].ewm(span=26, adjust=False).mean()
            df["MACD"] = df["EMA12"] - df["EMA26"]
            df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

            df["RSI"] = compute_rsi(df["Close"], 14)

            # 修正 KD 這段邏輯：防止除以 0
            low_min = df["Low"].rolling(window=9).min()
            high_max = df["High"].rolling(window=9).max()
            denom = (high_max - low_min).replace(0, 1)

            df["K"] = 100 * (df["Close"] - low_min) / denom
            df["D"] = df["K"].rolling(window=3).mean()

            latest = df.iloc[-1]

            result = {
                "stock_id": stock_id,
                "macd_golden": int(latest["MACD"] > latest["Signal"]),
                "kd_golden": int(latest["K"] > latest["D"]),
                "rsi_strong": int(latest["RSI"] > 50),
                "ma_up": int(latest["Close"] > latest["MA20"]),
                "bb_breakout": int(latest["Close"] > latest["Upper"]),
            }

            results.append(result)

        except Exception as e:
            print(f"[ta_generator] ⚠️ 技術指標失敗：{stock_id} - {e}")
            continue

    return pd.DataFrame(results)

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

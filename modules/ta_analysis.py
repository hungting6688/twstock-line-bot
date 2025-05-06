print("[ta_analysis] ✅ 最新修正版 v1.8（含白話建議）")

import pandas as pd

def analyze_technical_indicators(df: pd.DataFrame) -> dict:
    try:
        df = df.sort_index()
        signals = {}
        suggestion = []

        # MA (5日 > 20日)
        df["MA5"] = df["Close"].rolling(window=5).mean()
        df["MA20"] = df["Close"].rolling(window=20).mean()
        if df["MA5"].iloc[-1] > df["MA20"].iloc[-1]:
            signals["ma"] = True
            suggestion.append("短中期趨勢向上，可考慮分批佈局")
        else:
            signals["ma"] = False

        # RSI (>70 過熱)
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        signals["rsi"] = current_rsi
        if current_rsi > 70:
            suggestion.append("RSI > 70：價格偏高，建議觀望或分批出場")
        elif current_rsi < 30:
            suggestion.append("RSI < 30：超跌反彈機會，可留意進場時機")

        # KD (K > D 為黃金交叉)
        low_min = df["Low"].rolling(window=9).min()
        high_max = df["High"].rolling(window=9).max()
        rsv = (df["Close"] - low_min) / (high_max - low_min) * 100
        df["K"] = rsv.ewm(com=2).mean()
        df["D"] = df["K"].ewm(com=2).mean()
        if df["K"].iloc[-1] > df["D"].iloc[-1]:
            signals["kd"] = True
            suggestion.append("KD 黃金交叉，短線轉強，可考慮進場")
        else:
            signals["kd"] = False

        # MACD (黃金交叉訊號)
        ema12 = df["Close"].ewm(span=12).mean()
        ema26 = df["Close"].ewm(span=26).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9).mean()
        if macd_line.iloc[-1] > signal_line.iloc[-1]:
            signals["macd"] = True
            suggestion.append("MACD 黃金交叉，多頭動能啟動，可考慮短期進場")
        else:
            signals["macd"] = False

        signals["suggestions"] = suggestion
        return signals
    except Exception as e:
        print(f"[ta_analysis] 技術指標計算錯誤：{e}")
        return {}

"""
技術分析模組 - 整合 ta_analysis.py 和 ta_generator.py
"""
print("[technical] ✅ 已載入最新版")

import yfinance as yf
import pandas as pd
import numpy as np
from tqdm import tqdm
from modules.analysis.sentiment import get_market_sentiment_adjustments


def analyze_technical_indicators(stock_ids):
    """
    對多檔股票進行技術指標分析
    
    參數:
    - stock_ids: 股票代碼列表
    
    返回:
    - 分析結果字典 {stock_id: {"score": score, "desc": desc, "label": label, "suggestion": suggestion, "is_weak": bool}}
    """
    # 首先產生技術指標
    raw_df = generate_ta_signals(stock_ids)
    if raw_df.empty:
        return {}

    # 取得市場情緒調整因子
    weights = get_market_sentiment_adjustments()
    results = {}

    # 為每檔股票計算指標得分
    for _, row in raw_df.iterrows():
        sid = row["證券代號"]
        score = 0
        desc = []

        # MACD
        if row["MACD"] == 1:
            score += 1 * weights.get("MACD", 1.0)
            desc.append("MACD黃金交叉")

        # KD
        if row["K"] < 80 and row["K"] > row["D"]:
            score += 1 * weights.get("KD", 1.0)
            desc.append("KD黃金交叉")

        # RSI
        if row["RSI"] > 50:
            score += 1 * weights.get("RSI", 1.0)
            desc.append("RSI走強")

        # 均線
        if row["均線"] == 1:
            score += 1 * weights.get("MA", 1.0)
            desc.append("站上均線")

        # 布林通道
        if row["布林通道"] == 1:
            score += 1 * weights.get("BB", 1.0)
            desc.append("布林通道偏多")

        # 根據綜合得分決定標籤和建議
        label = "📌 觀察"
        suggestion = "建議密切觀察"
        
        if score >= 7:
            label = "✅ 推薦"
            suggestion = "建議立即列入關注清單"
        elif row["RSI"] < 30 and row["均線"] == 0:
            label = "⚠️ 走弱"
            suggestion = "不建議操作，短線偏空"

        # 記錄分析結果
        results[sid] = {
            "score": round(score, 1),
            "desc": "、".join(desc) if desc else "無明顯技術特徵",
            "label": label,
            "suggestion": suggestion,
            "is_weak": (label == "⚠️ 走弱")
        }

    return results


def generate_ta_signals(stock_ids):
    """
    產生多檔股票的技術指標資料
    
    參數:
    - stock_ids: 股票代碼列表
    
    返回:
    - 包含技術指標的 DataFrame
    """
    print("[technical] ⏳ 開始計算技術指標...")
    results = []

    for stock_id in tqdm(stock_ids, desc="[technical] 計算技術指標"):
        try:
            # 清理股票代碼
            clean_id = str(stock_id).replace("=\"", "").replace("\"", "").strip()
            
            # 下載股價數據
            df = yf.download(f"{clean_id}.TW", period="60d", progress=False)
            if df.empty or len(df) < 30:
                continue
                
            df = df.dropna().copy()
            df.reset_index(inplace=True)

            # 計算 MACD
            df["EMA12"] = df["Close"].ewm(span=12).mean()
            df["EMA26"] = df["Close"].ewm(span=26).mean()
            df["MACD"] = df["EMA12"] - df["EMA26"]
            df["Signal"] = df["MACD"].ewm(span=9).mean()
            
            macd_signal = 0
            if not df["MACD"].isna().all() and not df["Signal"].isna().all():
                macd_signal = int(safe_float(df["MACD"]) > safe_float(df["Signal"]))

            # 計算 KD
            low_min = df["Low"].rolling(window=9).min()
            high_max = df["High"].rolling(window=9).max()
            rsv = (df["Close"] - low_min) / (high_max - low_min) * 100
            df["K"] = rsv.ewm(com=2).mean()
            df["D"] = df["K"].ewm(com=2).mean()
            
            k = safe_float(df["K"])
            d = safe_float(df["D"])

            # 計算 RSI
            delta = df["Close"].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            rsi_val = safe_float(rsi)

            # 計算移動平均線
            ma5 = df["Close"].rolling(window=5).mean()
            ma20 = df["Close"].rolling(window=20).mean()
            
            # 短期均線是否突破長期均線
            ma_score = int(safe_float(ma5) > safe_float(ma20))

            # 計算布林通道
            mavg = df["Close"].rolling(window=20).mean()
            std = df["Close"].rolling(window=20).std()
            upper = mavg + 2 * std
            
            # 股價是否突破布林通道上軌
            bb_signal = int(df["Close"].iloc[-1] > upper.iloc[-1]) if not upper.isna().all() else 0

            # 記錄指標結果
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
            print(f"[technical] ⚠️ {stock_id} 技術指標計算失敗：{e}")

    return pd.DataFrame(results)


def safe_float(series):
    """
    安全地從 Series 中獲取最後一個浮點數值
    
    參數:
    - series: Pandas Series
    
    返回:
    - 浮點數值或 0.0
    """
    try:
        return float(series.iloc[-1])
    except:
        return 0.0


def generate_moving_averages(stock_code, periods=[5, 10, 20, 60]):
    """
    計算股票的多個週期移動平均線
    
    參數:
    - stock_code: 股票代碼
    - periods: 移動平均線週期列表
    
    返回:
    - 包含收盤價和各移動平均線的 DataFrame
    """
    try:
        ticker = yf.Ticker(f"{stock_code}.TW")
        history = ticker.history(period="120d")  # 獲取足夠長的歷史數據
        
        if history.empty:
            return pd.DataFrame()
            
        df = history[['Close']].copy()
        
        # 計算各週期的移動平均線
        for period in periods:
            df[f'MA{period}'] = df['Close'].rolling(window=period).mean()
            
        return df
        
    except Exception as e:
        print(f"[technical] ⚠️ {stock_code} 移動平均線計算失敗：{e}")
        return pd.DataFrame()


def calculate_rsi(stock_code, period=14):
    """
    計算股票的相對強弱指標 (RSI)
    
    參數:
    - stock_code: 股票代碼
    - period: RSI 計算週期，默認 14
    
    返回:
    - 包含收盤價和 RSI 的 DataFrame
    """
    try:
        ticker = yf.Ticker(f"{stock_code}.TW")
        history = ticker.history(period="60d")  # 獲取足夠長的歷史數據
        
        if history.empty:
            return pd.DataFrame()
            
        df = history[['Close']].copy()
        
        # 計算價格變化
        delta = df['Close'].diff()
        
        # 分離漲跌
        gain = delta.mask(delta < 0, 0)
        loss = -delta.mask(delta > 0, 0)
        
        # 計算平均漲跌
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # 計算相對強度
        rs = avg_gain / avg_loss
        
        # 計算 RSI
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
        
    except Exception as e:
        print(f"[technical] ⚠️ {stock_code} RSI 計算失敗：{e}")
        return pd.DataFrame()


def calculate_macd(stock_code):
    """
    計算股票的 MACD 指標
    
    參數:
    - stock_code: 股票代碼
    
    返回:
    - 包含收盤價和 MACD 相關指標的 DataFrame
    """
    try:
        ticker = yf.Ticker(f"{stock_code}.TW")
        history = ticker.history(period="120d")  # 獲取足夠長的歷史數據
        
        if history.empty:
            return pd.DataFrame()
            
        df = history[['Close']].copy()
        
        # 計算 EMA
        df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
        
        # 計算 MACD 線和訊號線
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # 計算 Histogram
        df['Histogram'] = df['MACD'] - df['Signal']
        
        return df
        
    except Exception as e:
        print(f"[technical] ⚠️ {stock_code} MACD 計算失敗：{e}")
        return pd.DataFrame()


def is_golden_cross(stock_code, short_period=5, long_period=20):
    """
    檢查股票是否出現黃金交叉
    
    參數:
    - stock_code: 股票代碼
    - short_period: 短期均線週期
    - long_period: 長期均線週期
    
    返回:
    - 是否出現黃金交叉的布爾值
    """
    try:
        ma_df = generate_moving_averages(stock_code, [short_period, long_period])
        
        if ma_df.empty:
            return False
            
        # 至少需要足夠的數據
        if len(ma_df) < long_period + 2:
            return False
            
        short_ma = ma_df[f'MA{short_period}']
        long_ma = ma_df[f'MA{long_period}']
        
        # 檢查今天是否為黃金交叉（今天短期均線在長期均線上方，昨天在下方）
        today_cross = short_ma.iloc[-1] > long_ma.iloc[-1]
        yesterday_cross = short_ma.iloc[-2] <= long_ma.iloc[-2]
        
        return today_cross and yesterday_cross
        
    except Exception as e:
        print(f"[technical] ⚠️ {stock_code} 黃金交叉檢查失敗：{e}")
        return False

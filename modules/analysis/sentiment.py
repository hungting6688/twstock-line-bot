"""
市場情緒分析模組 - 整合 market_sentiment.py
修正版本 - 新增 pandas 導入並修復 FutureWarning
"""
print("[sentiment] ✅ 已載入 sentiment.py 模組")

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_market_sentiment_score():
    """
    獲取整體市場情緒評分
    
    返回:
    - 市場情緒評分 (0-10)
    """
    # 監控的主要指數
    indices = {
        "^TWII": "台股加權",
        "^N225": "日經",
        "^HSI": "恆生",
        "^GSPC": "標普500",
        "^IXIC": "那斯達克",
    }

    today = datetime.today()
    start_date = today - timedelta(days=5)

    score = 0
    max_score = len(indices) * 2  # 每個指數最高可得2分
    valid_indices = 0  # 追踪成功讀取的指數數量

    # 分析每個指數的漲跌
    for symbol, name in indices.items():
        try:
            df = yf.download(symbol, start=start_date.strftime('%Y-%m-%d'), end=today.strftime('%Y-%m-%d'), progress=False)
            
            if df.empty or len(df) < 2:
                print(f"[sentiment] ⚠️ {symbol} 資料不足")
                continue
                
            closes = df["Close"].dropna()
            
            if len(closes) < 2:
                print(f"[sentiment] ⚠️ {symbol} 收盤價資料不足")
                continue
                
            # 修正：安全地取得資料，使用 iloc[0] 而非直接 float() 轉換
            last_close = closes.iloc[-1]
            prev_close = closes.iloc[-2]
            
            # 如果返回的是 Series，取第一個元素
            if isinstance(last_close, pd.Series):
                last_close = last_close.iloc[0]
            if isinstance(prev_close, pd.Series):
                prev_close = prev_close.iloc[0]
            
            pct_change = (last_close - prev_close) / prev_close
            valid_indices += 1  # 成功讀取一個指數

            # 根據漲跌幅度給分
            if pct_change > 0.01:  # 漲幅超過1%
                score += 2
            elif pct_change > 0:   # 小幅上漲
                score += 1

        except Exception as e:
            print(f"[sentiment] ❌ 無法讀取 {symbol}：{e}")
            continue

    # 轉換為0-10的評分，並處理沒有任何有效指數的情況
    if valid_indices > 0:
        normalized_score = round((score / (valid_indices * 2)) * 10, 1)
    else:
        normalized_score = 5.0  # 如果沒有有效指數，給出中性評分
    
    print(f"[sentiment] ✅ 市場情緒評分：{normalized_score}/10")
    
    return normalized_score

def get_market_sentiment_adjustments():
    """
    根據市場情緒提供各指標的權重調整
    
    返回:
    - 權重調整系數字典
    """
    # 獲取當前市場情緒評分
    score = get_market_sentiment_score()

    # 根據情緒分數提供不同的權重調整
    if score >= 8:  # 非常樂觀
        return {
            "MACD": 1.2,   # 強化短期趨勢指標
            "KD": 1.2,
            "RSI": 1.1,
            "MA": 1.2,
            "BB": 1.1,
            "dividend": 1.0,  # 不調整股息指標
            "eps": 1.0,
            "pe": 0.9,     # 弱化估值指標
            "roe": 0.9,
        }
    elif score >= 5:  # 中性
        return {
            "MACD": 1.0,
            "KD": 1.0,
            "RSI": 1.0,
            "MA": 1.0,
            "BB": 1.0,
            "dividend": 1.0,
            "eps": 1.0,
            "pe": 1.0,
            "roe": 1.0,
        }
    else:  # 悲觀
        return {
            "MACD": 0.8,   # 弱化趨勢指標
            "KD": 0.9,
            "RSI": 0.9,
            "MA": 0.8,
            "BB": 0.9,
            "dividend": 1.2,  # 強化價值指標
            "eps": 1.2,
            "pe": 1.1,
            "roe": 1.1,
        }

def analyze_relative_strength(stock_code):
    """
    分析個股相對於大盤的強弱
    
    參數:
    - stock_code: 股票代碼
    
    返回:
    - 相對強度 (百分比), 強度描述
    """
    try:
        # 取得最近20天的股價數據
        ticker = yf.Ticker(f"{stock_code}.TW")
        history = ticker.history(period="30d")
        
        if history.empty or len(history) < 20:
            return 0, "資料不足無法分析相對強度"
            
        # 取得同期台股加權指數數據
        twii = yf.Ticker("^TWII")
        twii_history = twii.history(period="30d")
        
        if twii_history.empty or len(twii_history) < 20:
            return 0, "無法取得台股加權指數數據"
            
        # 修正：安全地取得資料，使用 iloc[0] 處理 Series
        stock_close_20 = history['Close'].iloc[-20]
        stock_close_now = history['Close'].iloc[-1]
        
        twii_close_20 = twii_history['Close'].iloc[-20]
        twii_close_now = twii_history['Close'].iloc[-1]
        
        # 如果返回的是 Series，取第一個元素
        if isinstance(stock_close_20, pd.Series):
            stock_close_20 = stock_close_20.iloc[0]
        if isinstance(stock_close_now, pd.Series):
            stock_close_now = stock_close_now.iloc[0]
        if isinstance(twii_close_20, pd.Series):
            twii_close_20 = twii_close_20.iloc[0]
        if isinstance(twii_close_now, pd.Series):
            twii_close_now = twii_close_now.iloc[0]
        
        # 計算漲跌幅
        stock_change = (stock_close_now / stock_close_20 - 1) * 100
        market_change = (twii_close_now / twii_close_20 - 1) * 100
        
        # 計算相對強度
        relative_strength = stock_change - market_change
        
        # 生成描述
        if relative_strength > 5:
            desc = f"強勢：超越大盤 {relative_strength:.1f}%"
        elif relative_strength > 0:
            desc = f"略強：優於大盤 {relative_strength:.1f}%"
        elif relative_strength > -5:
            desc = f"略弱：低於大盤 {abs(relative_strength):.1f}%"
        else:
            desc = f"弱勢：明顯落後大盤 {abs(relative_strength):.1f}%"
            
        return relative_strength, desc
        
    except Exception as e:
        print(f"[sentiment] ⚠️ {stock_code} 相對強度分析失敗：{e}")
        return 0, "無法分析相對強度"

def analyze_fund_flow(stock_code, days=5):
    """
    分析個股資金流向
    
    參數:
    - stock_code: 股票代碼
    - days: 分析天數
    
    返回:
    - 資金流向強度, 流向描述
    """
    try:
        ticker = yf.Ticker(f"{stock_code}.TW")
        history = ticker.history(period="30d")
        
        if history.empty or len(history) < days + 5:
            return 0, "資料不足無法分析資金流向"
            
        # 確認成交量欄位存在
        if 'Volume' not in history.columns:
            return 0, "無成交量資料"
            
        # 計算最近幾天和之前幾天的平均成交量
        recent_vol = history['Volume'].tail(days).mean()
        prev_vol = history['Volume'].iloc[-2*days:-days].mean()
        
        # 如果返回的是 Series，取第一個元素
        if isinstance(recent_vol, pd.Series):
            recent_vol = recent_vol.iloc[0]
        if isinstance(prev_vol, pd.Series):
            prev_vol = prev_vol.iloc[0]
        
        if prev_vol == 0:
            return 0, "無法計算成交量變化"
            
        # 計算成交量變化比例
        volume_change = (recent_vol / prev_vol - 1) * 100
        
        # 生成描述
        if volume_change > 30:
            desc = f"資金大幅流入 (成交量增加 {volume_change:.1f}%)"
            strength = 2
        elif volume_change > 10:
            desc = f"資金小幅流入 (成交量增加 {volume_change:.1f}%)"
            strength = 1
        elif volume_change > -10:
            desc = "資金流向維持平衡"
            strength = 0
        elif volume_change > -30:
            desc = f"資金小幅流出 (成交量減少 {abs(volume_change):.1f}%)"
            strength = -1
        else:
            desc = f"資金大幅流出 (成交量減少 {abs(volume_change):.1f}%)"
            strength = -2
            
        return strength, desc
        
    except Exception as e:
        print(f"[sentiment] ⚠️ {stock_code} 資金流向分析失敗：{e}")
        return 0, "無法分析資金流向"

def calculate_ema(prices, days):
    """
    計算指數移動平均線，增加更多安全檢查及錯誤處理
    """
    try:
        if not isinstance(prices, np.ndarray):
            prices = np.array(prices, dtype=np.float64)
        
        if len(prices) < days:
            return np.mean(prices)
        
        prices = np.nan_to_num(prices, nan=np.nanmean(prices))
        
        alpha = 2.0 / (days + 1.0)
        ema = np.zeros_like(prices)
        ema[0] = prices[0]
        
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1.0 - alpha) * ema[i-1]
        
        return float(ema[-1])
    except Exception as e:
        print(f"[multi_analysis] ⚠️ EMA 計算錯誤：{e}")
        return 0.0

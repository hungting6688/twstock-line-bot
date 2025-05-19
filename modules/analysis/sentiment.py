import numpy as np

print("[sentiment] ✅ 已載入 sentiment.py 模組")

def get_market_sentiment_adjustments():
    """
    返回靜態市場情緒權重，用於調整技術指標的評分
    可擴充為根據 VIX、融資餘額等市場資料動態調整
    """
    return {
        "MACD": 1.0,
        "KD": 1.0,
        "RSI": 1.0,
        "MA": 1.0,
        "BB": 1.0,
        "eps": 1.0,
        "dividend": 1.0,
        "institutional": 1.0
    }

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

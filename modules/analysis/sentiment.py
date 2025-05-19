import numpy as np

def calculate_ema(prices, days):
    """
    計算指數移動平均線 (EMA)，具備輸入檢查與 NaN 容錯處理。
    
    參數:
    - prices: 可為 list、Series 或 ndarray 的價格序列
    - days: 欲計算的 EMA 週期

    返回:
    - 最新 EMA 值 (float)
    """
    try:
        # 檢查並轉換為 numpy array
        prices = np.asarray(prices, dtype=np.float64)
        
        if len(prices) == 0:
            return 0.0
        
        # 當資料點不足指定天數，回傳均值代替
        if len(prices) < days:
            return float(np.nanmean(prices))

        # 處理 NaN 值（先轉平均值，再處理全部 NaN）
        if np.isnan(prices).all():
            return 0.0  # 全部是 NaN
        prices = np.nan_to_num(prices, nan=np.nanmean(prices))

        # 初始化 EMA
        alpha = 2.0 / (days + 1.0)
        ema = np.zeros_like(prices)
        ema[0] = prices[0]
        
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1.0 - alpha) * ema[i - 1]
        
        return float(ema[-1])

    except Exception as e:
        print(f"[technical] ⚠️ EMA 計算錯誤：{e}")
        return 0.0

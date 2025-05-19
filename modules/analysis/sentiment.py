def calculate_ema(prices, days):
    """
    計算指數移動平均線，增加更多安全檢查及錯誤處理
    """
    try:
        # 確保輸入是 numpy array
        if not isinstance(prices, np.ndarray):
            prices = np.array(prices, dtype=np.float64)
        
        # 檢查數據長度
        if len(prices) < days:
            return np.mean(prices)
        
        # 處理可能的 NaN 值
        prices = np.nan_to_num(prices, nan=np.nanmean(prices))
        
        # 使用更穩健的 EMA 計算方法
        alpha = 2.0 / (days + 1.0)
        ema = np.zeros_like(prices)
        ema[0] = prices[0]  # 初始化第一個值
        
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1.0 - alpha) * ema[i-1]
        
        # 返回最後一個 EMA 值
        return float(ema[-1])  # 明確轉換為 float
    except Exception as e:
        print(f"[multi_analysis] ⚠️ EMA 計算錯誤：{e}")
        return 0.0  # 返回安全的默認值

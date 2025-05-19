"""
處理 Yahoo Finance Rate Limit 問題
"""

def get_eps_data_from_yahoo():
    """
    使用 Yahoo Finance 獲取 EPS 和股息數據 (備用方案)，增加速率限制處理
    """
    import yfinance as yf
    from concurrent.futures import ThreadPoolExecutor
    from tqdm import tqdm
    import time
    import random
    
    print("[scraper] 使用 Yahoo Finance 替代方案獲取財務數據...")
    
    # 獲取股票列表
    stock_list = get_all_valid_twse_stocks()
    # 限制股票數量，避免請求過多
    max_stocks = 50  # 降低同時請求的數量
    stock_list = stock_list[:max_stocks]
    
    result = {}
    
    # 使用隨機延遲避免被視為自動請求機器人
    def fetch_with_retry(stock_id):
        """帶有重試邏輯的抓取函數"""
        max_retries = 3
        for retry in range(max_retries):
            try:
                # 加入隨機延遲，避免請求過於頻繁
                time.sleep(random.uniform(0.5, 2.0))
                data = fetch_stock_finance(stock_id)
                return data
            except Exception as e:
                if "Too Many Requests" in str(e):
                    wait_time = (retry + 1) * 5  # 逐漸增加等待時間
                    print(f"[scraper] ⚠️ Rate limit for {stock_id}, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"[scraper] ⚠️ 處理 {stock_id} 時出錯: {str(e)[:100]}")
                    if retry == max_retries - 1:  # 最後一次重試
                        return None
    
    # 分批處理以避免同時發送過多請求
    batch_size = 10
    for i in range(0, len(stock_list), batch_size):
        batch = stock_list[i:i+batch_size]
        
        with ThreadPoolExecutor(max_workers=5) as executor:  # 減少同時執行的線程數
            futures = {}
            for stock in batch:
                stock_id = stock["stock_id"]
                futures[executor.submit(fetch_with_retry, stock_id)] = stock_id
            
            for future in futures:
                stock_id = futures[future]
                try:
                    data = future.result()
                    if data:
                        result[stock_id] = data
                except Exception as e:
                    print(f"[scraper] ⚠️ 處理 {stock_id} 時出錯: {str(e)[:100]}")
        
        # 每個批次間暫停一下
        time.sleep(2)
    
    print(f"[scraper] ✅ 成功獲取 {len(result)} 檔股票的財務數據 (Yahoo Finance)")
    return result


def fetch_stock_finance(stock_id):
    """
    從 Yahoo Finance 獲取單一股票的財務數據，增加錯誤處理
    """
    try:
        import yfinance as yf
        
        ticker = yf.Ticker(f"{stock_id}.TW")
        info = ticker.info
        
        # 獲取財務數據
        eps = info.get('trailingEPS')
        dividend_yield = info.get('dividendYield', 0)
        
        # 增加檢查，確保獲取到有效數據
        if eps is None or eps == 'N/A':
            eps = None
        else:
            try:
                eps = float(eps)
                eps = round(eps, 2)
            except:
                eps = None
        
        # 轉換股息率為百分比
        if dividend_yield is None or dividend_yield == 'N/A':
            dividend_yield = None
        else:
            try:
                dividend_yield = float(dividend_yield)
                if dividend_yield > 0:
                    dividend_yield = round(dividend_yield * 100, 2)
                else:
                    dividend_yield = None
            except:
                dividend_yield = None
        
        return {
            "eps": eps,
            "dividend": dividend_yield
        }
    except Exception as e:
        if "Too Many Requests" in str(e):
            raise e  # 讓呼叫者知道是 rate limit 問題
        return None

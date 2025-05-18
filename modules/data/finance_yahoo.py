"""
改用 yfinance 獲取 EPS 和股息數據的替代實現
"""

import yfinance as yf
import concurrent.futures
from tqdm import tqdm

def get_eps_data_alternative():
    """
    使用 yfinance 替代方案獲取 EPS 和股息數據
    
    返回:
    - 字典: {stock_id: {"eps": value, "dividend": value}}
    """
    from modules.data.scraper import get_all_valid_twse_stocks
    
    print("[scraper] 使用 yfinance 替代方案獲取 EPS 和股息數據...")
    
    # 獲取所有上市股票列表
    all_stocks = get_all_valid_twse_stocks()
    
    # 限制獲取的股票數量，避免耗時過長
    max_stocks = 300  # 您可以根據需要調整
    stocks_to_process = all_stocks[:max_stocks]
    
    result = {}
    
    # 使用多線程加速處理
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # 提交所有任務
        future_to_stock = {
            executor.submit(fetch_single_stock_data, stock): stock 
            for stock in stocks_to_process
        }
        
        # 處理結果
        for future in tqdm(concurrent.futures.as_completed(future_to_stock), 
                          total=len(stocks_to_process),
                          desc="[scraper] 獲取財務數據"):
            stock = future_to_stock[future]
            try:
                data = future.result()
                if data:
                    result[stock['stock_id']] = data
            except Exception as e:
                print(f"[scraper] ⚠️ 處理 {stock['stock_id']} 時出錯: {e}")
    
    print(f"[scraper] ✅ 成功獲取 {len(result)} 檔股票的財務數據")
    return result

def fetch_single_stock_data(stock):
    """
    獲取單一股票的財務數據
    
    參數:
    - stock: 股票資訊字典
    
    返回:
    - 財務數據字典
    """
    try:
        stock_id = stock['stock_id']
        # 使用 yfinance 獲取股票數據
        ticker = yf.Ticker(f"{stock_id}.TW")
        info = ticker.info
        
        # 獲取 EPS
        eps = info.get('trailingEPS')
        
        # 獲取股息率
        dividend_rate = info.get('dividendRate')
        dividend_yield = info.get('dividendYield', 0)
        
        # 如果有股息率，轉換為百分比
        if dividend_yield:
            dividend_yield = round(dividend_yield * 100, 2)
        
        # 返回數據
        return {
            "eps": round(eps, 2) if eps else None,
            "dividend": dividend_yield
        }
    except Exception as e:
        # 忽略錯誤，跳過此股票
        return None

def get_dividend_data_alternative():
    """
    獲取股息數據的替代實現
    
    返回:
    - 字典: {stock_id: dividend_value}
    """
    eps_data = get_eps_data_alternative()
    return {sid: val["dividend"] for sid, val in eps_data.items() if val["dividend"] is not None}

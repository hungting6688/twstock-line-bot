"""
改用 yfinance 獲取 EPS 和股息數據的替代實現
增強版處理 API 速率限制和連接失敗問題
"""

import yfinance as yf
import concurrent.futures
from tqdm import tqdm
import time
import random
import pandas as pd
import numpy as np
import os
import json
import requests
from datetime import datetime, timedelta

# 緩存目錄設置
CACHE_DIR = os.path.join(os.path.dirname(__file__), '../../cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# 隨機化的 User-Agent 列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
]

def test_yahoo_finance_connection():
    """
    測試 Yahoo Finance API 連接狀態
    
    返回:
    - bool: 連接是否正常
    """
    try:
        # 使用 requests 直接測試連接
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive"
        }
        
        # 直接測試 Yahoo Finance 網站
        response = requests.get("https://finance.yahoo.com/quote/AAPL", 
                              headers=headers, 
                              timeout=10)
        
        if response.status_code == 200:
            print("[finance_yahoo] ✅ Yahoo Finance API 連接測試成功")
            return True
        else:
            print(f"[finance_yahoo] ⚠️ Yahoo Finance API 連接測試失敗: 狀態碼 {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[finance_yahoo] ❌ Yahoo Finance API 連接測試失敗: {e}")
        return False

def get_eps_data_alternative(use_cache=True, cache_expiry_hours=24):
    """
    使用 yfinance 替代方案獲取 EPS 和股息數據，增加緩存和重試機制
    
    參數:
    - use_cache: 是否使用緩存
    - cache_expiry_hours: 緩存有效時間（小時）
    
    返回:
    - 字典: {stock_id: {"eps": value, "dividend": value}}
    """
    # 檢查緩存
    cache_file = os.path.join(CACHE_DIR, 'eps_data_cache.json')
    if use_cache and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                
                # 檢查緩存是否過期
                if datetime.now() - cache_time < timedelta(hours=cache_expiry_hours):
                    print(f"[finance_yahoo] ✅ 使用緩存的 EPS 數據 (更新於 {cache_time.strftime('%Y-%m-%d %H:%M')})")
                    return cache_data['data']
        except Exception as e:
            print(f"[finance_yahoo] ⚠️ 讀取緩存失敗: {e}")
    
    # 首先測試連接
    connection_ok = test_yahoo_finance_connection()
    if not connection_ok:
        print("[finance_yahoo] ⚠️ Yahoo Finance API 連接測試失敗，將使用緩存或備用數據")
        
        # 如果連接測試失敗且存在緩存，則使用緩存即使已過期
        if use_cache and os.path.exists(cache_file):
            try:
                print("[finance_yahoo] 嘗試使用過期緩存...")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    return cache_data['data']
            except Exception as e:
                print(f"[finance_yahoo] ⚠️ 讀取過期緩存失敗: {e}")
    
    # 嘗試使用已有的財務資料緩存而非重新抓取
    try:
        from modules.data.scraper import get_eps_data
        print("[finance_yahoo] 嘗試使用 scraper 模組獲取 EPS 數據...")
        eps_data = get_eps_data()
        if eps_data:
            print(f"[finance_yahoo] ✅ 成功獲取 {len(eps_data)} 檔股票的 EPS 數據")
            
            # 儲存結果到緩存
            if use_cache and eps_data:
                try:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        cache_data = {
                            'timestamp': datetime.now().isoformat(),
                            'data': eps_data
                        }
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                    print(f"[finance_yahoo] ✅ 已更新 EPS 數據緩存")
                except Exception as e:
                    print(f"[finance_yahoo] ⚠️ 寫入緩存失敗: {e}")
                    
            return eps_data
    except Exception as e:
        print(f"[finance_yahoo] ⚠️ scraper 模組獲取數據失敗: {e}")
    
    print("[finance_yahoo] 使用 yfinance 替代方案獲取 EPS 和股息數據...")
    
    # 獲取熱門股票列表而不是全部股票列表
    try:
        from modules.data.fetcher import get_top_stocks
        
        # 根據當前時段決定掃描檔數
        mode = get_current_mode()
        scan_limit = get_scan_limit_for_mode(mode)
        print(f"[finance_yahoo] 當前時段: {mode}, 掃描限制: {scan_limit}檔")
        
        # 獲取前N檔熱門股票
        top_stocks = get_top_stocks(limit=scan_limit)
        print(f"[finance_yahoo] ✅ 成功獲取 {len(top_stocks)} 檔熱門股票")
    except Exception as e:
        print(f"[finance_yahoo] ⚠️ 無法獲取熱門股票列表: {e}，使用備用清單")
        top_stocks = [s['stock_id'] for s in get_backup_stock_list()[:100]]
    
    # 限制獲取的股票數量，避免耗時過長
    stocks_to_process = top_stocks[:min(50, len(top_stocks))]  # 最多處理50檔
    print(f"[finance_yahoo] 限制處理 {len(stocks_to_process)} 檔股票")
    
    result = {}
    
    # 從環境變數獲取配置或使用默認值
    max_retries = 3  # 減少最大重試次數
    
    # 分批處理股票，避免同時發送過多請求
    batch_size = 5  # 從 10 減少到 5
    for i in range(0, len(stocks_to_process), batch_size):
        batch = stocks_to_process[i:i+batch_size]
        print(f"[finance_yahoo] 處理批次 {i//batch_size + 1}/{(len(stocks_to_process)-1)//batch_size + 1} ({len(batch)} 檔股票)")
        
        # 直接串行處理，避免並行導致的錯誤
        for stock_id in batch:
            try:
                data = fetch_single_stock_data_with_retry(stock_id, max_retries)
                if data:
                    result[stock_id] = data
                else:
                    # 設置默認值避免後續處理出錯
                    result[stock_id] = {"eps": None, "dividend": None}
            except Exception as e:
                print(f"[finance_yahoo] ⚠️ 處理 {stock_id} 時出錯: {e}")
                # 設置默認值避免後續處理出錯
                result[stock_id] = {"eps": None, "dividend": None}
        
        # 批次間添加固定延遲，避免 API 限制
        if i + batch_size < len(stocks_to_process):
            delay = 5.0 + random.uniform(0.5, 2.0)
            print(f"[finance_yahoo] 等待 {delay:.1f} 秒後處理下一批...")
            time.sleep(delay)
    
    print(f"[finance_yahoo] ✅ 成功獲取 {len(result)} 檔股票的財務數據")
    
    # 儲存結果到緩存
    if use_cache and result:
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                cache_data = {
                    'timestamp': datetime.now().isoformat(),
                    'data': result
                }
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            print(f"[finance_yahoo] ✅ 已更新 EPS 數據緩存")
        except Exception as e:
            print(f"[finance_yahoo] ⚠️ 寫入緩存失敗: {e}")
    
    return result

def get_current_mode():
    """
    根據當前時間確定執行模式
    
    返回:
    - 'morning', 'noon', 'afternoon', 或 'evening'
    """
    current_hour = (datetime.now() + timedelta(hours=8)).hour  # 台灣時間
    
    if current_hour < 10:
        return 'morning'
    elif current_hour < 12:
        return 'afternoon'
    elif current_hour < 14:
        return 'noon'
    else:
        return 'evening'

def get_scan_limit_for_mode(mode):
    """
    根據模式獲取掃描限制
    
    參數:
    - mode: 模式名稱
    
    返回:
    - 掃描限制數量
    """
    limits = {
        'morning': 50,   # 減少掃描數量
        'afternoon': 50,
        'noon': 50,
        'evening': 100
    }
    return limits.get(mode, 50)  # 默認減少到50

def fetch_single_stock_data_with_retry(stock_id, max_retries=3):
    """
    使用重試機制獲取單一股票的財務數據
    
    參數:
    - stock_id: 股票代碼
    - max_retries: 最大重試次數
    
    返回:
    - 財務數據字典
    """    
    for retry in range(max_retries):
        try:
            # 每次重試增加延遲，且添加隨機抖動以避免請求同步
            if retry > 0:
                # 指數退避：基礎延遲 * (2^重試次數) + 隨機抖動
                delay = (2 ** retry) * 2 + random.uniform(0.5, 2.0)
                print(f"[finance_yahoo] ⏳ {stock_id} 重試 ({retry+1}/{max_retries})，等待 {delay:.1f} 秒...")
                time.sleep(delay)
            
            # 直接使用 yfinance 獲取數據，不再嘗試修改內部屬性
            return fetch_single_stock_data(stock_id)
            
        except Exception as e:
            if "Too Many Requests" in str(e) or "401" in str(e):
                if retry < max_retries - 1:
                    continue  # 繼續重試
            
            if retry == max_retries - 1:
                print(f"[finance_yahoo] ❌ {stock_id} 最終請求失敗: {e}")
            
    # 如果所有重試都失敗，返回默認值
    return {"eps": None, "dividend": None}

def fetch_single_stock_data(stock_id):
    """
    獲取單一股票的財務數據
    
    參數:
    - stock_id: 股票代碼 (字符串)
    
    返回:
    - 財務數據字典
    """
    try:
        # 使用 yfinance 獲取股票數據
        ticker = yf.Ticker(f"{stock_id}.TW")
        info = ticker.info
        
        # 安全地獲取 EPS
        eps = None
        try:
            eps = info.get('trailingEPS')
            if eps is not None and not pd.isna(eps) and not np.isnan(eps):
                eps = round(float(eps), 2)
            else:
                eps = None
        except (ValueError, TypeError):
            eps = None
        
        # 安全地獲取股息率
        dividend_yield = None
        try:
            dividend_yield = info.get('dividendYield')
            if dividend_yield is not None and not pd.isna(dividend_yield) and not np.isnan(dividend_yield):
                dividend_yield = round(float(dividend_yield) * 100, 2)
                if dividend_yield <= 0:
                    dividend_yield = None
            else:
                dividend_yield = None
        except (ValueError, TypeError):
            dividend_yield = None
        
        # 返回數據
        return {
            "eps": eps,
            "dividend": dividend_yield
        }
    except Exception as e:
        # 如果是速率限制或授權錯誤，向上拋出以觸發重試
        if "Too Many Requests" in str(e) or "401" in str(e):
            raise
        
        print(f"[finance_yahoo] ⚠️ {stock_id} 處理失敗: {e}")
        return {"eps": None, "dividend": None}

def get_dividend_data_alternative(use_cache=True, cache_expiry_hours=24):
    """
    獲取股息數據的替代實現
    
    參數:
    - use_cache: 是否使用緩存
    - cache_expiry_hours: 緩存有效時間（小時）
    
    返回:
    - 字典: {stock_id: dividend_value}
    """
    # 檢查緩存
    cache_file = os.path.join(CACHE_DIR, 'dividend_data_cache.json')
    if use_cache and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                
                # 檢查緩存是否過期
                if datetime.now() - cache_time < timedelta(hours=cache_expiry_hours):
                    print(f"[finance_yahoo] ✅ 使用緩存的股息數據 (更新於 {cache_time.strftime('%Y-%m-%d %H:%M')})")
                    return cache_data['data']
        except Exception as e:
            print(f"[finance_yahoo] ⚠️ 讀取股息緩存失敗: {e}")
    
    # 獲取完整數據
    eps_data = get_eps_data_alternative(use_cache, cache_expiry_hours)
    
    # 提取股息數據
    dividend_data = {sid: val["dividend"] for sid, val in eps_data.items() if val["dividend"] is not None}
    
    # 儲存結果到緩存
    if use_cache and dividend_data:
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                cache_data = {
                    'timestamp': datetime.now().isoformat(),
                    'data': dividend_data
                }
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            print(f"[finance_yahoo] ✅ 已更新股息數據緩存")
        except Exception as e:
            print(f"[finance_yahoo] ⚠️ 寫入股息緩存失敗: {e}")
    
    return dividend_data

def get_backup_stock_list():
    """提供備用的上市股票列表"""
    backup_stocks = [
        {"stock_id": "2330", "stock_name": "台積電", "market_type": "上市", "industry": "半導體業"},
        {"stock_id": "2317", "stock_name": "鴻海", "market_type": "上市", "industry": "電子零組件業"},
        {"stock_id": "2303", "stock_name": "聯電", "market_type": "上市", "industry": "半導體業"},
        {"stock_id": "2308", "stock_name": "台達電", "market_type": "上市", "industry": "電子零組件業"},
        {"stock_id": "2454", "stock_name": "聯發科", "market_type": "上市", "industry": "半導體業"},
        {"stock_id": "2412", "stock_name": "中華電", "market_type": "上市", "industry": "電信業"},
        {"stock_id": "2882", "stock_name": "國泰金", "market_type": "上市", "industry": "金融業"},
        {"stock_id": "1301", "stock_name": "台塑", "market_type": "上市", "industry": "塑膠工業"},
        {"stock_id": "1303", "stock_name": "南亞", "market_type": "上市", "industry": "塑膠工業"},
        {"stock_id": "2881", "stock_name": "富邦金", "market_type": "上市", "industry": "金融業"},
        {"stock_id": "1216", "stock_name": "統一", "market_type": "上市", "industry": "食品工業"},
        {"stock_id": "2002", "stock_name": "中鋼", "market_type": "上市", "industry": "鋼鐵工業"},
        {"stock_id": "2886", "stock_name": "兆豐金", "market_type": "上市", "industry": "金融業"},
        {"stock_id": "1101", "stock_name": "台泥", "market_type": "上市", "industry": "水泥工業"},
        {"stock_id": "2891", "stock_name": "中信金", "market_type": "上市", "industry": "金融業"},
        {"stock_id": "3711", "stock_name": "日月光投控", "market_type": "上市", "industry": "半導體業"},
        {"stock_id": "2327", "stock_name": "國巨", "market_type": "上市", "industry": "電子零組件業"},
        {"stock_id": "2912", "stock_name": "統一超", "market_type": "上市", "industry": "貿易百貨"},
        {"stock_id": "2207", "stock_name": "和泰車", "market_type": "上市", "industry": "汽車工業"},
        {"stock_id": "2884", "stock_name": "玉山金", "market_type": "上市", "industry": "金融業"}
    ]
    return backup_stocks

def get_stock_info(stock_id, retry_on_rate_limit=True):
    """
    獲取單一股票的詳細資訊，帶重試機制
    
    參數:
    - stock_id: 股票代碼
    - retry_on_rate_limit: 是否在速率限制時重試
    
    返回:
    - 股票資訊字典
    """
    max_retries = 3 if retry_on_rate_limit else 1
    
    for retry in range(max_retries):
        try:
            # 添加隨機延遲，避免過於頻繁的請求
            if retry > 0:
                delay = (2 ** retry) * 1.5 + random.uniform(0.5, 2.0)
                time.sleep(delay)
            
            ticker = yf.Ticker(f"{stock_id}.TW")
            info = ticker.info
            
            # 檢查是否獲得有效數據
            if not info or len(info) < 5:
                print(f"[finance_yahoo] ⚠️ {stock_id} 獲取的信息不完整")
                if retry < max_retries - 1:
                    continue
                return None
            
            return info
            
        except Exception as e:
            if "Too Many Requests" in str(e) or "401" in str(e) and retry < max_retries - 1:
                wait_time = (2 ** retry) * 3 + random.uniform(0.5, 2.0)
                print(f"[finance_yahoo] ⚠️ {stock_id} 請求失敗: {e}，等待 {wait_time:.1f} 秒後重試...")
                time.sleep(wait_time)
            elif retry < max_retries - 1:
                wait_time = (2 ** retry) * 1.5 + random.uniform(0.2, 1.0)
                print(f"[finance_yahoo] ⚠️ {stock_id} 請求失敗: {e}，等待 {wait_time:.1f} 秒後重試...")
                time.sleep(wait_time)
            else:
                print(f"[finance_yahoo] ❌ {stock_id} 最終請求失敗: {e}")
                return None
    
    return None

def get_stock_price_history(stock_id, period="60d", retry_on_rate_limit=True):
    """
    獲取股票價格歷史數據，帶重試機制
    
    參數:
    - stock_id: 股票代碼
    - period: 歷史時間長度
    - retry_on_rate_limit: 是否在速率限制時重試
    
    返回:
    - 價格歷史 DataFrame
    """
    max_retries = 3 if retry_on_rate_limit else 1
    
    for retry in range(max_retries):
        try:
            # 添加隨機延遲，避免過於頻繁的請求
            if retry > 0:
                delay = (2 ** retry) * 1.5 + random.uniform(0.5, 2.0)
                time.sleep(delay)
            
            ticker = yf.Ticker(f"{stock_id}.TW")
            history = ticker.history(period=period)
            
            # 檢查是否獲得有效數據
            if history.empty:
                print(f"[finance_yahoo] ⚠️ {stock_id} 無法獲取歷史數據")
                if retry < max_retries - 1:
                    continue
                return pd.DataFrame()
            
            return history
                
        except Exception as e:
            if "Too Many Requests" in str(e) or "401" in str(e) and retry < max_retries - 1:
                wait_time = (2 ** retry) * 3 + random.uniform(0.5, 2.0)
                print(f"[finance_yahoo] ⚠️ {stock_id} 請求失敗: {e}，等待 {wait_time:.1f} 秒後重試...")
                time.sleep(wait_time)
            elif retry < max_retries - 1:
                wait_time = (2 ** retry) * 1.5 + random.uniform(0.2, 1.0)
                print(f"[finance_yahoo] ⚠️ {stock_id} 請求失敗: {e}，等待 {wait_time:.1f} 秒後重試...")
                time.sleep(wait_time)
            else:
                print(f"[finance_yahoo] ❌ {stock_id} 最終請求失敗: {e}")
                return pd.DataFrame()
    
    return pd.DataFrame()

# 當模組被直接執行時運行的代碼
if __name__ == "__main__":
    print("測試 Yahoo Finance 替代方案...")
    # 先測試連接
    test_yahoo_finance_connection()
    # 獲取數據
    result = get_eps_data_alternative(use_cache=False)
    print(f"獲取到 {len(result)} 檔股票的 EPS 和股息數據")
    
    # 顯示前 5 筆數據
    count = 0
    for stock_id, data in result.items():
        print(f"{stock_id}: EPS={data.get('eps')}, 股息={data.get('dividend')}%")
        count += 1
        if count >= 5:
            break

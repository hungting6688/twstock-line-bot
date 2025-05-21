"""
modules/data/finance_yahoo.py
改用 yfinance 獲取 EPS 和股息數據的替代實現
增強版處理 API 速率限制和連接失敗問題 (2025版)
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

# 導入連接管理器
try:
    from modules.data.connection_manager import (
        create_robust_session, 
        test_connection, 
        is_service_available,
        wait_for_service, 
        get_random_user_agent,
        log_connection_event
    )
except ImportError:
    # 如果連接管理器不存在，使用簡易版本的功能
    def get_random_user_agent():
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        ]
        return random.choice(agents)
    
    def create_robust_session(**kwargs):
        return requests.Session()
    
    def test_connection(url, **kwargs):
        try:
            response = requests.get(url, timeout=5)
            return response.status_code == 200, f"狀態碼: {response.status_code}"
        except Exception as e:
            return False, str(e)
    
    def is_service_available(service_name):
        return True
    
    def wait_for_service(service_name):
        return True
    
    def log_connection_event(message, level='info'):
        print(f"[yahoo_finance] {message}")

# 緩存目錄設置
CACHE_DIR = os.path.join(os.path.dirname(__file__), '../../cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# 確保日誌目錄存在
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 全局配置參數 - 從環境變量獲取或使用默認值
MAX_RETRIES = int(os.getenv("YAHOO_FINANCE_RETRY_ATTEMPTS", "5"))
CONNECTION_TIMEOUT = int(os.getenv("YAHOO_FINANCE_CONNECTION_TIMEOUT", "10"))
READ_TIMEOUT = int(os.getenv("YAHOO_FINANCE_READ_TIMEOUT", "15"))
BATCH_DELAY = float(os.getenv("YAHOO_FINANCE_BATCH_DELAY", "5"))

# 隨機化的 User-Agent 列表 - 加入更多現代化的選項
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
]

# 關鍵股票清單 - 優先處理這些股票
PRIORITY_STOCKS = [
    "2330", "2317", "2454", "2412", "2303", "2308", "2882", "2881", 
    "1301", "1303", "2002", "2886", "1216", "2891", "3711", "2327"
]

# 等待時間配置 - 添加這些常量以便於調整
MIN_WAIT_TIME = 1.0      # 最小等待時間(秒)
RATE_LIMIT_WAIT = 30.0   # 速率限制後的等待時間(秒)
ERROR_WAIT_BASE = 2.0    # 一般錯誤的基礎等待時間(秒)

def test_yahoo_finance_connection():
    """
    測試 Yahoo Finance API 連接狀態
    
    返回:
    - bool: 連接是否正常
    """
    try:
        # 使用連接管理器測試連接
        if not is_service_available('yahoo_finance'):
            print("[finance_yahoo] ⚠️ Yahoo Finance 服務暫時不可用，等待恢復")
            return False
        
        success, message = test_connection(
            "https://finance.yahoo.com/quote/AAPL", 
            service_name='yahoo_finance',
            timeout=CONNECTION_TIMEOUT
        )
        
        if success:
            print("[finance_yahoo] ✅ Yahoo Finance API 連接測試成功")
            return True
        else:
            print(f"[finance_yahoo] ⚠️ Yahoo Finance API 連接測試失敗: {message}")
            return False
            
    except Exception as e:
        print(f"[finance_yahoo] ❌ Yahoo Finance API 連接測試失敗: {e}")
        return False

def get_eps_data_alternative(use_cache=True, cache_expiry_hours=72, max_stocks=80, timeout=20, batch_size=5, batch_delay=None):
    """
    使用 yfinance 替代方案獲取 EPS 和股息數據，優化超時和並行處理
    
    參數:
    - use_cache: 是否使用緩存
    - cache_expiry_hours: 緩存有效時間（小時）
    - max_stocks: 最多處理的股票數量
    - timeout: 單個股票處理的超時時間(秒)
    - batch_size: 批處理大小
    - batch_delay: 批次間延遲時間(秒)，None表示使用環境變量或默認值
    
    返回:
    - 字典: {stock_id: {"eps": value, "dividend": value}}
    """
    # 如果未指定批次延遲，使用環境變量或默認值
    if batch_delay is None:
        batch_delay = BATCH_DELAY
    
    # 檢查緩存 - 延長緩存有效期至72小時
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
    
    # 如果連接測試失敗，直接使用備用數據
    if not connection_ok:
        print("[finance_yahoo] ⚠️ 使用備用數據...")
        from modules.data.scraper import get_hardcoded_eps_data
        backup_data = get_hardcoded_eps_data()
        return backup_data
    
    print("[finance_yahoo] 使用優化的 yfinance 模組獲取 EPS 和股息數據...")
    
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
        top_stocks = [s for s in get_backup_stock_list()[:100]]
    
    # 使用連接管理器的等待機制
    wait_for_service('yahoo_finance')
    
    # 使用備用數據作為基礎，然後增量更新
    from modules.data.scraper import get_hardcoded_eps_data
    result = get_hardcoded_eps_data()
    print(f"[finance_yahoo] ✅ 載入了 {len(result)} 檔備用股票數據作為基礎")
    
    # 調整批次大小，減少並發，增加間隔
    actual_batch_size = min(3, batch_size)  # 限制最大3個並發
    actual_batch_delay = max(8, batch_delay)  # 至少8秒延遲
    
    # 計算需要優先更新的股票清單
    stocks_to_update = [s for s in top_stocks if s not in result]
    total_to_update = len(stocks_to_update)
    
    if total_to_update > max_stocks:
        stocks_to_update = stocks_to_update[:max_stocks]
        print(f"[finance_yahoo] ⚠️ 限制更新 {max_stocks}/{total_to_update} 檔股票數據")
    
    print(f"[finance_yahoo] 開始更新 {len(stocks_to_update)} 檔股票的財務數據...")
    
    # 分批處理，減小批次大小並增加間隔
    processed_count = 0
    for i in range(0, len(stocks_to_update), actual_batch_size):
        batch = stocks_to_update[i:i+actual_batch_size]
        print(f"[finance_yahoo] 處理批次 {i//actual_batch_size + 1}/{(len(stocks_to_update)-1)//actual_batch_size + 1} ({len(batch)} 檔股票)")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=actual_batch_size) as executor:
            futures = {executor.submit(fetch_single_stock_data_with_retry, stock_id, 2, timeout): stock_id for stock_id in batch}
            
            for future in concurrent.futures.as_completed(futures):
                stock_id = futures[future]
                try:
                    data = future.result()
                    if data and (data["eps"] is not None or data["dividend"] is not None):
                        result[stock_id] = data
                        processed_count += 1
                    else:
                        # 設置默認值避免後續處理出錯
                        if stock_id not in result:
                            result[stock_id] = {"eps": None, "dividend": None}
                except Exception as e:
                    print(f"[finance_yahoo] ⚠️ 處理 {stock_id} 時出錯: {e}")
                    # 設置默認值避免後續處理出錯
                    if stock_id not in result:
                        result[stock_id] = {"eps": None, "dividend": None}
        
        # 批次間添加更長的延遲，避免 API 限制
        if i + actual_batch_size < len(stocks_to_update):
            delay = actual_batch_delay + random.uniform(1.0, 3.0)
            print(f"[finance_yahoo] 等待 {delay:.1f} 秒後處理下一批...")
            time.sleep(delay)
    
    print(f"[finance_yahoo] ✅ 成功更新 {processed_count} 檔股票的財務數據")
    
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
    current_hour = datetime.now().hour  # 直接使用本地時間
    
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
        'morning': 60,   # 降低掃描限制以避免API超載
        'afternoon': 40,
        'noon': 40,
        'evening': 60
    }
    return limits.get(mode, 40)

def fetch_single_stock_data_with_retry(stock_id, max_retries=2, timeout=20):
    """
    使用重試機制獲取單一股票的財務數據
    
    參數:
    - stock_id: 股票代碼
    - max_retries: 最大重試次數
    - timeout: 超時時間(秒)
    
    返回:
    - 財務數據字典
    """    
    # 立即檢查是否為優先股票，調整最大重試次數
    if stock_id in PRIORITY_STOCKS:
        max_retries = max(max_retries, 3)  # 優先股最少3次重試
    
    # 保存已經發生的錯誤類型
    encountered_errors = []
    
    for retry in range(max_retries):
        try:
            # 每次重試增加延遲，且添加隨機抖動以避免請求同步
            if retry > 0:
                # 計算等待時間 - 指數退避
                if "Too Many Requests" in " ".join(encountered_errors) or "429" in " ".join(encountered_errors):
                    # 對於速率限制錯誤，使用更長的等待時間
                    delay = RATE_LIMIT_WAIT + random.uniform(0, 5.0)
                else:
                    # 一般錯誤的指數退避
                    delay = ERROR_WAIT_BASE * (2 ** retry) + random.uniform(0.5, 2.0)
                
                print(f"[finance_yahoo] ⏳ {stock_id} 重試 ({retry+1}/{max_retries})，等待 {delay:.1f} 秒...")
                time.sleep(delay)
            
            # 直接使用 yfinance 獲取數據，使用超時控制
            return fetch_single_stock_data(stock_id, timeout)
            
        except Exception as e:
            error_str = str(e)
            encountered_errors.append(error_str)
            
            if "Too Many Requests" in error_str or "429" in error_str:
                print(f"[finance_yahoo] ⚠️ {stock_id} 遇到速率限制 (429 Too Many Requests)")
            elif "timed out" in error_str.lower():
                print(f"[finance_yahoo] ⚠️ {stock_id} 請求超時")
            else:
                print(f"[finance_yahoo] ⚠️ {stock_id} 請求失敗: {e}")
            
            # 如果還有重試機會，繼續下一次重試
            if retry < max_retries - 1:
                continue
            
            # 已達到最大重試次數
            print(f"[finance_yahoo] ❌ {stock_id} 最終請求失敗，已重試 {max_retries} 次")
            
    # 如果所有重試都失敗，返回默認值
    return {"eps": None, "dividend": None}

def fetch_single_stock_data(stock_id, timeout=20):
    """
    獲取單一股票的財務數據，增加超時控制
    
    參數:
    - stock_id: 股票代碼 (字符串)
    - timeout: 超時時間(秒)
    
    返回:
    - 財務數據字典
    """
    try:
        # 使用 yfinance 獲取股票數據，設置超時
        start_time = time.time()
        ticker = yf.Ticker(f"{stock_id}.TW")
        
        # 使用分階段獲取信息，確保在超時前盡可能取得更多數據
        info = None
        eps = None
        dividend_yield = None
        
        # 第一階段：獲取基本信息
        try:
            # 計算剩餘超時時間
            remaining_timeout = max(1, timeout - (time.time() - start_time))
            
            # 获取基本信息
            info = ticker.info
            
            if info and isinstance(info, dict):
                # 安全地獲取 EPS
                eps = info.get('trailingEPS')
                if eps is not None and not pd.isna(eps) and not np.isnan(eps):
                    eps = round(float(eps), 2)
                else:
                    eps = None
                
                # 安全地獲取股息率
                dividend_yield = info.get('dividendYield')
                if dividend_yield is not None and not pd.isna(dividend_yield) and not np.isnan(dividend_yield):
                    dividend_yield = round(float(dividend_yield) * 100, 2)
                    if dividend_yield <= 0:
                        dividend_yield = None
                else:
                    dividend_yield = None
        except Exception as e:
            print(f"[finance_yahoo] ⚠️ {stock_id} 獲取基本信息失敗: {e}")
        
        # 第二階段：如果仍有足夠時間且沒有獲取到股息，嘗試獲取股息歷史
        if dividend_yield is None and (time.time() - start_time) < timeout * 0.7:
            try:
                dividends = ticker.dividends
                if not dividends.empty:
                    latest_dividend = dividends.iloc[-1]
                    history = ticker.history(period="1mo")
                    if not history.empty:
                        latest_price = history['Close'].iloc[-1]
                        if latest_price > 0:
                            dividend_yield = round((latest_dividend / latest_price) * 100, 2)
            except Exception as e:
                print(f"[finance_yahoo] ⚠️ {stock_id} 獲取股息歷史失敗: {e}")
        
        # 返回數據
        return {
            "eps": eps,
            "dividend": dividend_yield
        }
    except Exception as e:
        # 如果是速率限制或授權錯誤，向上拋出以觸發重試
        if "Too Many Requests" in str(e) or "429" in str(e) or "401" in str(e) or "timed out" in str(e).lower():
            raise
        
        print(f"[finance_yahoo] ⚠️ {stock_id} 處理失敗: {e}")
        return {"eps": None, "dividend": None}

def get_dividend_data_alternative(use_cache=True, cache_expiry_hours=72):
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
    eps_data = get_eps_data_alternative(use_cache, cache_expiry_hours, batch_size=3)
    
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
    """提供備用的上市股票列表 - 2025年更新版"""
    backup_stocks = [
        "2330", "2317", "2303", "2308", "2454", "2412", "2882", "1301", 
        "1303", "2881", "1216", "2002", "2886", "1101", "2891", "3711", 
        "2327", "2912", "2207", "2884", "2382", "2609", "6505", "2892", 
        "2887", "2345", "3008", "2615", "5880", "3045"
    ]
    return backup_stocks

def get_stock_info(stock_id, retry_on_rate_limit=True, timeout=15):
    """
    獲取單一股票的詳細資訊，帶重試機制和超時控制
    
    參數:
    - stock_id: 股票代碼
    - retry_on_rate_limit: 是否在速率限制時重試
    - timeout: 超時時間(秒)
    
    返回:
    - 股票資訊字典
    """
    max_retries = MAX_RETRIES if retry_on_rate_limit else 1
    
    # 保存已經發生的錯誤類型
    encountered_errors = []
    
    for retry in range(max_retries):
        try:
            # 每次重試增加延遲
            if retry > 0:
                # 計算等待時間 - 指數退避
                if "Too Many Requests" in " ".join(encountered_errors) or "429" in " ".join(encountered_errors):
                    # 對於速率限制錯誤，使用更長的等待時間
                    delay = RATE_LIMIT_WAIT + random.uniform(0, 5.0)
                else:
                    # 一般錯誤的指數退避
                    delay = ERROR_WAIT_BASE * (2 ** retry) + random.uniform(0.5, 2.0)
                
                time.sleep(delay)
            
            ticker = yf.Ticker(f"{stock_id}.TW")
            
            # 使用超時設置
            start_time = time.time()
            info = ticker.info
            
            # 檢查是否獲得有效數據
            if not info or len(info) < 5:
                print(f"[finance_yahoo] ⚠️ {stock_id} 獲取的信息不完整")
                encountered_errors.append("Incomplete info")
                if retry < max_retries - 1:
                    continue
                return None
            
            return info
            
        except Exception as e:
            error_str = str(e)
            encountered_errors.append(error_str)
            
            if "Too Many Requests" in error_str or "429" in error_str:
                print(f"[finance_yahoo] ⚠️ {stock_id} 遇到速率限制 (429 Too Many Requests)")
            else:
                print(f"[finance_yahoo] ⚠️ {stock_id} 請求失敗: {e}")
            
            # 如果還有重試機會，繼續下一次重試
            if retry < max_retries - 1:
                continue
                
            print(f"[finance_yahoo] ❌ {stock_id} 最終請求失敗，已重試 {max_retries} 次")
    
    return None

def get_stock_price_history(stock_id, period="60d", retry_on_rate_limit=True, timeout=15):
    """
    獲取股票價格歷史數據，帶重試機制和超時控制
    
    參數:
    - stock_id: 股票代碼
    - period: 歷史時間長度
    - retry_on_rate_limit: 是否在速率限制時重試
    - timeout: 超時時間(秒)
    
    返回:
    - 價格歷史 DataFrame
    """
    max_retries = MAX_RETRIES if retry_on_rate_limit else 1
    
    # 保存已經發生的錯誤類型
    encountered_errors = []
    
    for retry in range(max_retries):
        try:
            # 每次重試增加延遲
            if retry > 0:
                # 計算等待時間 - 指數退避
                if "Too Many Requests" in " ".join(encountered_errors) or "429" in " ".join(encountered_errors):
                    # 對於速率限制錯誤，使用更長的等待時間
                    delay = RATE_LIMIT_WAIT + random.uniform(0, 5.0)
                else:
                    # 一般錯誤的指數退避
                    delay = ERROR_WAIT_BASE * (2 ** retry) + random.uniform(0.5, 2.0)
                
                time.sleep(delay)
            
            ticker = yf.Ticker(f"{stock_id}.TW")
            
            # 使用超時設置
            start_time = time.time()
            history = ticker.history(period=period)
            
            # 檢查是否獲得有效數據
            if history.empty:
                print(f"[finance_yahoo] ⚠️ {stock_id} 無法獲取歷史數據")
                encountered_errors.append("Empty history")
                if retry < max_retries - 1:
                    continue
                return pd.DataFrame()
            
            return history
                
        except Exception as e:
            error_str = str(e)
            encountered_errors.append(error_str)
            
            if "Too Many Requests" in error_str or "429" in error_str:
                print(f"[finance_yahoo] ⚠️ {stock_id} 遇到速率限制 (429 Too Many Requests)")
            else:
                print(f"[finance_yahoo] ⚠️ {stock_id} 請求失敗: {e}")
            
            # 如果還有重試機會，繼續下一次重試
            if retry < max_retries - 1:
                continue
                
            print(f"[finance_yahoo] ❌ {stock_id} 最終請求失敗，已重試 {max_retries} 次")
    
    return pd.DataFrame()

def log_to_file(message, level='INFO'):
    """記錄資訊到日誌檔案"""
    try:
        log_file = os.path.join(LOG_DIR, 'yahoo_finance.log')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} [{level}] {message}\n")
    except Exception as e:
        print(f"[finance_yahoo] 無法寫入日誌: {e}")

# 當模組被直接執行時運行的代碼
if __name__ == "__main__":
    print("測試 Yahoo Finance 替代方案...")
    # 先測試連接
    test_yahoo_finance_connection()
    # 獲取數據
    result = get_eps_data_alternative(use_cache=False, batch_size=3)
    print(f"獲取到 {len(result)} 檔股票的 EPS 和股息數據")
    
    # 顯示前 5 筆數據
    count = 0
    for stock_id, data in result.items():
        print(f"{stock_id}: EPS={data.get('eps')}, 股息={data.get('dividend')}%")
        count += 1
        if count >= 5:
            break

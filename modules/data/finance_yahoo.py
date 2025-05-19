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
from datetime import datetime, timedelta

# 緩存目錄設置
CACHE_DIR = os.path.join(os.path.dirname(__file__), '../../cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_eps_data_alternative(use_cache=True, cache_expiry_hours=12):
    """
    使用 yfinance 替代方案獲取 EPS 和股息數據，增加緩存和重試機制
    
    參數:
    - use_cache: 是否使用緩存
    - cache_expiry_hours: 緩存有效時間（小時）
    
    返回:
    - 字典: {stock_id: {"eps": value, "dividend": value}}
    """
    from modules.data.scraper import get_all_valid_twse_stocks
    from modules.data.fetcher import get_top_stocks
    
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
    
    print("[finance_yahoo] 使用 yfinance 替代方案獲取 EPS 和股息數據...")
    
    # 獲取熱門股票列表而不是全部股票列表
    try:
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
    stocks_to_process = top_stocks[:scan_limit]
    print(f"[finance_yahoo] 限制處理 {len(stocks_to_process)} 檔股票")
    
    result = {}
    
    # 分批處理股票，避免同時發送過多請求
    batch_size = 10
    for i in range(0, len(stocks_to_process), batch_size):
        batch = stocks_to_process[i:i+batch_size]
        print(f"[finance_yahoo] 處理批次 {i//batch_size + 1}/{(len(stocks_to_process)-1)//batch_size + 1} ({len(batch)} 檔股票)")
        
        # 使用多線程但限制並發數量
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # 提交所有任務
            future_to_stock = {
                executor.submit(fetch_single_stock_data_with_retry, stock_id): stock_id 
                for stock_id in batch
            }
            
            # 處理結果
            for future in concurrent.futures.as_completed(future_to_stock):
                stock_id = future_to_stock[future]
                try:
                    data = future.result()
                    if data:
                        result[stock_id] = data
                except Exception as e:
                    print(f"[finance_yahoo] ⚠️ 處理 {stock_id} 時出錯: {e}")
        
        # 批次間添加延遲
        if i + batch_size < len(stocks_to_process):
            delay = random.uniform(1.5, 3.0)
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
        'morning': 100,
        'afternoon': 200,
        'noon': 200,
        'evening': 500
    }
    return limits.get(mode, 100)

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
            # 添加隨機延遲，避免過於頻繁的請求
            delay = random.uniform(0.5, 1.5) * (retry + 1)
            time.sleep(delay)
            
            return fetch_single_stock_data(stock_id)
            
        except Exception as e:
            if "Too Many Requests" in str(e) and retry < max_retries - 1:
                wait_time = 5 * (2 ** retry)  # 指數退避策略：5, 10, 20...秒
                print(f"[finance_yahoo] ⚠️ {stock_id} 請求速率受限，等待 {wait_time} 秒後重試 ({retry+1}/{max_retries})...")
                time.sleep(wait_time)
            elif retry < max_retries - 1:
                print(f"[finance_yahoo] ⚠️ {stock_id} 請求失敗: {e}，重試 ({retry+1}/{max_retries})...")
                time.sleep(delay)
            else:
                print(f"[finance_yahoo] ❌ {stock_id} 最終請求失敗: {e}")
                return None
    
    return None

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
        # 如果是速率限制錯誤，向上拋出以觸發重試
        if "Too Many Requests" in str(e):
            raise
        
        print(f"[finance_yahoo] ⚠️ {stock_id} 處理失敗: {e}")
        return None

def get_dividend_data_alternative(use_cache=True, cache_expiry_hours=12):
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
                delay = random.uniform(1.0, 3.0) * (retry + 1)
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
            if "Too Many Requests" in str(e) and retry < max_retries - 1 and retry_on_rate_limit:
                wait_time = 5 * (2 ** retry)  # 指數退避策略
                print(f"[finance_yahoo] ⚠️ {stock_id} 請求速率受限，等待 {wait_time} 秒後重試...")
                time.sleep(wait_time)
            elif retry < max_retries - 1:
                print(f"[finance_yahoo] ⚠️ {stock_id} 請求失敗: {e}，重試中...")
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
                delay = random.uniform(1.0, 3.0) * (retry + 1)
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
            if "Too Many Requests" in str(e) and retry < max_retries - 1 and retry_on_rate_limit:
                wait_time = 5 * (2 ** retry)  # 指數退避策略
                print(f"[finance_yahoo] ⚠️ {stock_id} 請求速率受限，等待 {wait_time} 秒後重試...")
                time.sleep(wait_time)
            elif retry < max_retries - 1:
                print(f"[finance_yahoo] ⚠️ {stock_id} 請求失敗: {e}，重試中...")
            else:
                print(f"[finance_yahoo] ❌ {stock_id} 最終請求失敗: {e}")
                return pd.DataFrame()
    
    return pd.DataFrame()

# 當模組被直接執行時運行的代碼
if __name__ == "__main__":
    print("測試 Yahoo Finance 替代方案...")
    result = get_eps_data_alternative(use_cache=False)
    print(f"獲取到 {len(result)} 檔股票的 EPS 和股息數據")
    
    # 顯示前 5 筆數據
    count = 0
    for stock_id, data in result.items():
        print(f"{stock_id}: EPS={data.get('eps')}, 股息={data.get('dividend')}%")
        count += 1
        if count >= 5:
            break

"""
數據爬蟲模組 - 整合 eps_dividend_scraper.py、fundamental_scraper.py、twse_scraper.py
增強版本：改進數據獲取可靠性和錯誤處理 (2025版 - 修復超時設置)
"""
print("[scraper] ✅ 已載入最新版")

import requests
import pandas as pd
from io import StringIO
import datetime
from bs4 import BeautifulSoup
import io
import time
import os
import json
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import socket

# 緩存目錄設置
CACHE_DIR = os.path.join(os.path.dirname(__file__), '../../cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# 全局配置參數 - 從環境變量獲取或使用默認值
MAX_RETRIES = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
CONNECTION_TIMEOUT = int(os.getenv("SCRAPER_CONNECTION_TIMEOUT", "10"))
READ_TIMEOUT = int(os.getenv("SCRAPER_READ_TIMEOUT", "20"))
BATCH_DELAY = float(os.getenv("SCRAPER_BATCH_DELAY", "1.5"))

# 建立一個可重試的 requests session
def create_retry_session(retries=MAX_RETRIES, backoff_factor=0.5, 
                         status_forcelist=(500, 502, 504, 429),
                         allowed_methods=('GET', 'POST')):
    """
    建立一個具有重試功能的 requests session
    """
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=allowed_methods
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    # 設定更長的默認超時 - 修復版本，避免使用 super
    original_request = session.request
    session.request = lambda method, url, **kwargs: original_request(
        method=method, 
        url=url, 
        timeout=kwargs.pop('timeout', (CONNECTION_TIMEOUT, READ_TIMEOUT)),  # 使用提供的超時或默認值
        **kwargs
    )
    
    return session

def get_latest_season():
    """
    獲取最近一季的年度和季度
    
    返回:
    - 民國年，季度(01, 02, 03, 04)
    """
    now = datetime.datetime.now()
    year = now.year - 1911  # 轉換為民國年
    month = now.month
    
    if month <= 3:
        season = "04"
        year -= 1  # 前一年第四季
    elif month <= 6:
        season = "01"  # 當年第一季
    elif month <= 9:
        season = "02"  # 當年第二季
    else:
        season = "03"  # 當年第三季
        
    return str(year), season

# 全局數據獲取狀態跟踪
data_fetch_status = {
    "last_fetch_time": None,
    "last_fetch_source": None,
    "successful_sources": [],
    "failed_sources": []
}

def get_eps_data(use_cache=True, cache_expiry_hours=72):
    """
    抓取所有上市公司的 EPS 和股息資料，增加多來源獲取和強化錯誤處理
    
    參數:
    - use_cache: 是否使用緩存
    - cache_expiry_hours: 緩存有效時間（小時）
    
    返回:
    - 字典: {stock_id: {"eps": value, "dividend": value}}
    """
    global data_fetch_status
    
    # 檢查緩存（增加緩存有效期至72小時）
    cache_file = os.path.join(CACHE_DIR, 'eps_data_cache.json')
    if use_cache and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                cache_time = datetime.datetime.fromisoformat(cache_data['timestamp'])
                
                # 檢查緩存是否過期（延長至72小時）
                if datetime.datetime.now() - cache_time < datetime.timedelta(hours=cache_expiry_hours):
                    print(f"[scraper] ✅ 使用緩存的 EPS 和股息數據 (更新於 {cache_time.strftime('%Y-%m-%d %H:%M')})")
                    return cache_data['data']
        except Exception as e:
            print(f"[scraper] ⚠️ 讀取緩存失敗: {e}")
    
    # 並行從多個來源獲取數據
    print("[scraper] 🔄 從多個數據源並行獲取 EPS 和股息數據...")
    
    # 定義數據源函數列表
    data_sources = [
        ("MOPS", get_eps_data_from_mops),
        ("Yahoo Finance", get_eps_data_from_yahoo),
        ("Backup", get_backup_eps_data)
    ]
    
    # 追踪結果
    results = {}
    successful_source = None
    
    # 使用線程池並行執行數據獲取
    with ThreadPoolExecutor(max_workers=len(data_sources)) as executor:
        # 提交所有任務
        future_to_source = {executor.submit(source_func): source_name for source_name, source_func in data_sources}
        
        # 當任何一個任務完成時處理結果
        for future in as_completed(future_to_source):
            source_name = future_to_source[future]
            try:
                data = future.result()
                if data and len(data) > 0:
                    print(f"[scraper] ✅ 從 {source_name} 成功獲取 {len(data)} 檔股票的 EPS 和股息數據")
                    results = data
                    successful_source = source_name
                    data_fetch_status["successful_sources"].append(source_name)
                    
                    # 中斷其他仍在執行的任務
                    for f in future_to_source:
                        if not f.done():
                            f.cancel()
                    break
                else:
                    print(f"[scraper] ⚠️ 從 {source_name} 獲取數據失敗或為空")
                    data_fetch_status["failed_sources"].append(source_name)
            except Exception as e:
                print(f"[scraper] ❌ 從 {source_name} 獲取數據時出錯: {e}")
                data_fetch_status["failed_sources"].append(source_name)
    
    # 如果所有來源都失敗，使用備用方案
    if not results:
        print("[scraper] ⚠️ 所有數據源均失敗，使用硬編碼的備用數據")
        results = get_hardcoded_eps_data()
        successful_source = "Hardcoded Backup"
    
    # 更新狀態追踪
    data_fetch_status["last_fetch_time"] = datetime.datetime.now().isoformat()
    data_fetch_status["last_fetch_source"] = successful_source
    
    # 記錄數據獲取狀態
    try:
        status_file = os.path.join(CACHE_DIR, 'data_fetch_status.json')
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(data_fetch_status, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[scraper] ⚠️ 無法保存數據獲取狀態: {e}")
    
    # 儲存結果到緩存
    if use_cache and results:
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                cache_data = {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'source': successful_source,
                    'data': results
                }
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            print(f"[scraper] ✅ 已更新 EPS 和股息數據緩存")
        except Exception as e:
            print(f"[scraper] ⚠️ 寫入緩存失敗: {e}")
    
    return results

def get_eps_data_from_mops():
    """從公開資訊觀測站獲取 EPS 數據（設置優化的超時和重試機制）"""
    year, season = get_latest_season()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://mops.twse.com.tw/mops/web/t05st09_1"
    }

    print(f"[scraper] 嘗試獲取 {year} 年第 {season} 季的 EPS 數據...")
    
    # 初始化結果字典和數據框
    result = {}
    eps_df = pd.DataFrame()
    div_df = pd.DataFrame()
    
    # 使用優化的重試機制和更短的超時設定 - 減少整體等待時間
    session = create_retry_session(retries=2, backoff_factor=0.3)
    
    # 檢查連接是否可用
    try:
        socket_timeout = 5  # 使用非常短的超時測試連接
        host = "mops.twse.com.tw"
        port = 443
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(socket_timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result != 0:
            print(f"[scraper] ⚠️ 無法連接到 {host}:{port}，狀態碼: {result}")
            return {}
    except Exception as e:
        print(f"[scraper] ⚠️ 連接測試失敗: {e}")
        return {}
    
    # 成功連接後，嘗試獲取數據
    try:
        # 嘗試獲取每股盈餘資料，設置更短的超時
        eps_url = "https://mops.twse.com.tw/mops/web/ajax_t05st09_1"
        eps_data = {
            "encodeURIComponent": "1",
            "step": "1",
            "firstin": "1",
            "off": "1",
            "TYPEK": "sii",
            "year": year,
            "season": season
        }
        
        # 增加重試邏輯但縮短超時時間和重試次數
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                # 發送請求，使用較短的超時
                eps_res = session.post(
                    eps_url,
                    data=eps_data,
                    headers=headers,
                    timeout=(5, 10)  # 連接超時5秒，讀取超時10秒
                )
                
                if eps_res.status_code == 200 and "<table" in eps_res.text.lower():
                    try:
                        tables = pd.read_html(StringIO(eps_res.text))
                        if len(tables) > 1:
                            eps_df = tables[1]
                            eps_df.columns = eps_df.columns.str.strip()
                            eps_df = eps_df.rename(columns={"公司代號": "stock_id", "基本每股盈餘（元）": "EPS"})
                            eps_df = eps_df[["stock_id", "EPS"]].dropna()
                            eps_df["EPS"] = pd.to_numeric(eps_df["EPS"], errors="coerce")
                            eps_df = eps_df.dropna()
                            break  # 成功獲取數據，跳出重試循環
                    except Exception as e:
                        print(f"[scraper] ⚠️ EPS表格解析失敗 (嘗試 {attempt+1}/{max_attempts}): {e}")
                
                # 如果不是最後一次嘗試，暫停一下再重試（縮短等待時間）
                if attempt < max_attempts - 1:
                    time.sleep(1)  # 減少延遲
            except Exception as e:
                print(f"[scraper] ⚠️ EPS數據請求失敗 (嘗試 {attempt+1}/{max_attempts}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(1)
    except Exception as e:
        print(f"[scraper] ❌ 查無 EPS 表格或格式錯誤：{e}")
    
    # 同樣的方式處理股息資料，但縮短等待時間
    try:
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                # 嘗試獲取股息資料，減少超時時間
                div_res = session.post(
                    "https://mops.twse.com.tw/mops/web/ajax_t05st34",
                    data={"encodeURIComponent": "1", "step": "1", "firstin": "1", "off": "1", "TYPEK": "sii"},
                    headers=headers, 
                    timeout=(5, 10)  # 減少超時時間
                )
                
                if div_res.status_code == 200 and "<table" in div_res.text.lower():
                    try:
                        tables = pd.read_html(StringIO(div_res.text))
                        if len(tables) > 1:
                            div_df = tables[1]
                            div_df.columns = div_df.columns.str.strip()
                            div_df = div_df.rename(columns={"公司代號": "stock_id", "現金股利": "Dividend"})
                            div_df = div_df[["stock_id", "Dividend"]].dropna()
                            div_df["Dividend"] = pd.to_numeric(div_df["Dividend"], errors="coerce")
                            div_df = div_df.dropna()
                            break  # 成功獲取數據，跳出重試循環
                    except Exception as e:
                        print(f"[scraper] ⚠️ 股息表格解析失敗 (嘗試 {attempt+1}/{max_attempts}): {e}")
                
                # 如果不是最後一次嘗試，暫停一下再重試
                if attempt < max_attempts - 1:
                    time.sleep(1)  # 減少延遲
            except Exception as e:
                print(f"[scraper] ⚠️ 股息數據請求失敗 (嘗試 {attempt+1}/{max_attempts}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(1)
    except Exception as e:
        print(f"[scraper] ❌ 查無股利表格或格式錯誤：{e}")
    
    # 檢查是否成功獲取數據
    if eps_df.empty and div_df.empty:
        print("[scraper] ⚠️ 無法從公開資訊觀測站獲取數據")
        return {}
    
    # 合併數據
    for _, row in eps_df.iterrows():
        try:
            sid = str(row["stock_id"]).zfill(4)
            result[sid] = {"eps": round(row["EPS"], 2), "dividend": None}
        except:
            continue

    for _, row in div_df.iterrows():
        try:
            sid = str(row["stock_id"]).zfill(4)
            if sid not in result:
                result[sid] = {"eps": None, "dividend": None}
            result[sid]["dividend"] = round(row["Dividend"], 2)
        except:
            continue
    
    print(f"[scraper] ✅ 成功從公開資訊觀測站獲取 {len(result)} 檔股票的 EPS 和股息數據")
    return result

def get_eps_data_from_yahoo():
    """從 Yahoo Finance 獲取 EPS 和股息數據"""
    try:
        # 導入 finance_yahoo 模組中的函數
        from modules.data.finance_yahoo import get_eps_data_alternative
        
        # 使用縮短超時的設置來調用此函數，並指定更小的處理批次來避免速率限制
        return get_eps_data_alternative(max_stocks=40, timeout=15, batch_size=3, batch_delay=2.0)
    except Exception as e:
        print(f"[scraper] ❌ 使用 Yahoo Finance 獲取數據失敗：{e}")
        return {}

def get_backup_eps_data():
    """嘗試從備用來源獲取 EPS 數據"""
    try:
        # 先檢查備用緩存，即使過期也使用
        backup_cache_file = os.path.join(CACHE_DIR, 'backup_eps_data_cache.json')
        if os.path.exists(backup_cache_file):
            try:
                with open(backup_cache_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                    # 顯示緩存年齡
                    cache_time = datetime.datetime.fromisoformat(backup_data['timestamp'])
                    age_hours = (datetime.datetime.now() - cache_time).total_seconds() / 3600
                    print(f"[scraper] ℹ️ 使用備用緩存的 EPS 數據 (年齡：{age_hours:.1f}小時)")
                    return backup_data['data']
            except Exception as e:
                print(f"[scraper] ⚠️ 讀取備用緩存失敗: {e}")
        
        # 否則使用硬編碼的備用數據
        return get_hardcoded_eps_data()
    except Exception as e:
        print(f"[scraper] ❌ 備份數據源失敗: {e}")
        return {}

def get_hardcoded_eps_data():
    """提供硬編碼的重要股票 EPS 和股息數據作為最後的備用方案"""
    print("[scraper] 使用硬編碼的重要股票 EPS 和股息數據")
    
    # 大型股的基本財務數據 - 2025年更新的數據
    return {
        "2330": {"eps": 9.8, "dividend": 3.2},   # 台積電
        "2317": {"eps": 5.5, "dividend": 4.7},   # 鴻海
        "2454": {"eps": 52.0, "dividend": 53.0}, # 聯發科
        "2412": {"eps": 4.7, "dividend": 5.0},   # 中華電
        "2303": {"eps": 2.3, "dividend": 2.1},   # 聯電
        "2308": {"eps": 6.0, "dividend": 4.4},   # 台達電
        "2882": {"eps": 2.2, "dividend": 2.9},   # 國泰金
        "2881": {"eps": 2.2, "dividend": 2.6},   # 富邦金
        "1301": {"eps": 5.0, "dividend": 4.0},   # 台塑
        "1303": {"eps": 4.2, "dividend": 3.6},   # 南亞
        "2002": {"eps": 1.9, "dividend": 2.3},   # 中鋼
        "2886": {"eps": 2.0, "dividend": 2.5},   # 兆豐金
        "1216": {"eps": 3.8, "dividend": 3.6},   # 統一
        "2891": {"eps": 1.9, "dividend": 2.3},   # 中信金
        "3008": {"eps": 4.7, "dividend": 4.3},   # 大立光
        "2884": {"eps": 1.8, "dividend": 1.9},   # 玉山金
        "2327": {"eps": 15.0, "dividend": 9.0},  # 國巨
        "2603": {"eps": 2.5, "dividend": 2.7},   # 長榮
        "3045": {"eps": 5.4, "dividend": 4.7},   # 台灣大
        "2912": {"eps": 7.8, "dividend": 7.0},   # 統一超
        "2382": {"eps": 5.2, "dividend": 4.0},   # 廣達
        "2609": {"eps": 3.3, "dividend": 2.8},   # 陽明
        "6505": {"eps": 6.9, "dividend": 5.5},   # 台塑化
        "2892": {"eps": 1.8, "dividend": 1.7},   # 第一金
        "2887": {"eps": 1.6, "dividend": 1.5},   # 台新金
        "1101": {"eps": 1.8, "dividend": 1.6},   # 台泥
        "3711": {"eps": 13.8, "dividend": 7.0},  # 日月光投控
        "2615": {"eps": 2.7, "dividend": 2.2},   # 萬海
        "2345": {"eps": 5.6, "dividend": 4.5},   # 智邦
        "5880": {"eps": 3.2, "dividend": 2.9}    # 合庫金
    }


def get_all_valid_twse_stocks(limit=None, use_cache=True, cache_expiry_hours=48):
    """
    從證交所獲取所有有效的上市股票，增加緩存機制
    
    參數:
    - limit: 限制返回的股票數量，None 表示不限制
    - use_cache: 是否使用緩存
    - cache_expiry_hours: 緩存有效時間（小時）
    
    返回:
    - 股票資訊列表 [{"stock_id": id, "stock_name": name, "market_type": type, "industry": ind}]
    """
    # 檢查緩存
    cache_file = os.path.join(CACHE_DIR, 'twse_stocks_cache.json')
    if use_cache and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                cache_time = datetime.datetime.fromisoformat(cache_data['timestamp'])
                
                # 檢查緩存是否過期
                if datetime.datetime.now() - cache_time < datetime.timedelta(hours=cache_expiry_hours):
                    print(f"[scraper] ✅ 使用緩存的股票列表 (更新於 {cache_time.strftime('%Y-%m-%d %H:%M')})")
                    
                    # 在返回緩存結果前增加限制檢查
                    if limit is not None and isinstance(limit, int) and limit > 0:
                        print(f"[scraper] 限制返回 {limit} 檔股票")
                        return cache_data['data'][:limit]
                    
                    return cache_data['data']
        except Exception as e:
            print(f"[scraper] ⚠️ 讀取股票列表緩存失敗: {e}")
    
    url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    # 使用優化的重試設置
    session = create_retry_session(retries=2, backoff_factor=0.5)
    
    try:
        # 增加重試邏輯，但使用更短的超時
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                response = session.get(url, headers=headers, timeout=(5, 15))
                response.encoding = 'big5'
                
                if response.status_code == 200 and len(response.text) > 1000:
                    break  # 成功獲取數據
                    
                # 如果不是最後一次嘗試，暫停一下再重試
                if attempt < max_attempts - 1:
                    time.sleep(1.5)
            except Exception as e:
                print(f"[scraper] ⚠️ 獲取股票列表失敗 (嘗試 {attempt+1}/{max_attempts}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(1.5)
                else:
                    # 如果最後一次嘗試仍然失敗，使用備用列表
                    print(f"[scraper] ⚠️ 獲取股票列表失敗，使用備用列表")
                    backup_stocks = get_backup_stock_list()
                    
                    # 在返回備用列表前增加限制檢查
                    if limit is not None and isinstance(limit, int) and limit > 0:
                        print(f"[scraper] 限制返回 {limit} 檔備用股票")
                        return backup_stocks[:limit]
                    
                    return backup_stocks

        # 解析數據
        try:
            tables = pd.read_html(StringIO(response.text))
            df = tables[0]
            df.columns = df.iloc[0]
            df = df[1:]

            all_stocks = []
            for _, row in df.iterrows():
                if pd.isna(row["有價證券代號及名稱"]):
                    continue
                    
                parts = str(row["有價證券代號及名稱"]).split()
                if len(parts) != 2:
                    continue
                    
                stock_id, stock_name = parts
                market_type = str(row["市場別"])
                industry = str(row["產業別"])

                # 篩選上市股票，排除下市、空白代碼
                if not stock_id.isdigit():
                    continue

                # 排除已下市或特別標記的股票
                if "下市" in stock_name:
                    continue

                all_stocks.append({
                    "stock_id": stock_id,
                    "stock_name": stock_name,
                    "market_type": market_type,
                    "industry": industry
                })

            print(f"[scraper] ✅ 成功獲取 {len(all_stocks)} 檔上市股票列表")
            
            # 儲存結果到緩存
            if use_cache and all_stocks:
                try:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        cache_data = {
                            'timestamp': datetime.datetime.now().isoformat(),
                            'data': all_stocks
                        }
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                    print(f"[scraper] ✅ 已更新股票列表緩存")
                except Exception as e:
                    print(f"[scraper] ⚠️ 寫入股票列表緩存失敗: {e}")
            
            # 在返回結果前增加限制檢查
            if limit is not None and isinstance(limit, int) and limit > 0:
                print(f"[scraper] 限制返回 {limit} 檔股票")
                return all_stocks[:limit]
            
            return all_stocks
        except Exception as e:
            print(f"[scraper] ⚠️ 解析股票列表數據失敗: {e}")
            # 如果解析失敗，使用備用列表
            backup_stocks = get_backup_stock_list()
            
            # 在返回備用列表前增加限制檢查
            if limit is not None and isinstance(limit, int) and limit > 0:
                print(f"[scraper] 限制返回 {limit} 檔備用股票")
                return backup_stocks[:limit]
            
            return backup_stocks
            
    except Exception as e:
        print(f"[scraper] ❌ 獲取上市股票列表失敗：{e}")
        # 如果失敗，返回一個包含主要上市公司的備用列表
        print(f"[scraper] ⚠️ 使用備用上市股票列表...")
        backup_stocks = get_backup_stock_list()
        
        # 在返回備用列表前增加限制檢查
        if limit is not None and isinstance(limit, int) and limit > 0:
            print(f"[scraper] 限制返回 {limit} 檔備用股票")
            return backup_stocks[:limit]
        
        return backup_stocks


def get_backup_stock_list():
    """提供備用的上市股票列表 - 更新至2025年版本"""
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
        {"stock_id": "2884", "stock_name": "玉山金", "market_type": "上市", "industry": "金融業"},
        {"stock_id": "2382", "stock_name": "廣達", "market_type": "上市", "industry": "電腦及週邊設備業"},
        {"stock_id": "2609", "stock_name": "陽明", "market_type": "上市", "industry": "航運業"},
        {"stock_id": "6505", "stock_name": "台塑化", "market_type": "上市", "industry": "石油、煤製品業"},
        {"stock_id": "2892", "stock_name": "第一金", "market_type": "上市", "industry": "金融業"},
        {"stock_id": "2887", "stock_name": "台新金", "market_type": "上市", "industry": "金融業"},
        {"stock_id": "2345", "stock_name": "智邦", "market_type": "上市", "industry": "通信網路業"},
        {"stock_id": "3008", "stock_name": "大立光", "market_type": "上市", "industry": "光電業"},
        {"stock_id": "2615", "stock_name": "萬海", "market_type": "上市", "industry": "航運業"},
        {"stock_id": "5880", "stock_name": "合庫金", "market_type": "上市", "industry": "金融業"},
        {"stock_id": "3045", "stock_name": "台灣大", "market_type": "上市", "industry": "電信業"}
    ]
    return backup_stocks


def get_dividend_data(use_cache=True, cache_expiry_hours=72):
    """
    僅獲取股息資料，增加緩存有效期
    
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
                cache_time = datetime.datetime.fromisoformat(cache_data['timestamp'])
                
                # 檢查緩存是否過期，延長到72小時
                if datetime.datetime.now() - cache_time < datetime.timedelta(hours=cache_expiry_hours):
                    print(f"[scraper] ✅ 使用緩存的股息數據 (更新於 {cache_time.strftime('%Y-%m-%d %H:%M')})")
                    return cache_data['data']
        except Exception as e:
            print(f"[scraper] ⚠️ 讀取股息緩存失敗: {e}")
    
    # 獲取完整 EPS 和股息數據
    all_data = get_eps_data(use_cache, cache_expiry_hours)
    
    # 提取股息數據
    dividend_data = {sid: val["dividend"] for sid, val in all_data.items() if val["dividend"] is not None}
    
    # 儲存結果到緩存
    if use_cache and dividend_data:
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                cache_data = {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'data': dividend_data
                }
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            print(f"[scraper] ✅ 已更新股息數據緩存")
        except Exception as e:
            print(f"[scraper] ⚠️ 寫入股息緩存失敗: {e}")
    
    return dividend_data


def get_all_valid_twse_stocks_with_type(use_cache=True):
    """
    獲取所有上市股票，並添加股票類型標記（大型股、中小型股、ETF）
    
    參數:
    - use_cache: 是否使用緩存
    
    返回:
    - 添加了類型的股票列表
    """
    from modules.data.fetcher import is_etf
    
    # 獲取原始股票列表
    raw = get_all_valid_twse_stocks(use_cache)
    stocks = []
    
    for item in raw:
        stock_id = item["stock_id"]
        stock_name = item["stock_name"]
        
        # 判斷股票類型
        if is_etf(stock_name):
            stock_type = "etf"
        elif int(stock_id) < 4000:
            stock_type = "large"  # 一般認為編號小於4000的多為大型股
        else:
            stock_type = "small"  # 編號大於4000多為中小型股
            
        stocks.append({
            "stock_id": stock_id, 
            "stock_name": stock_name, 
            "type": stock_type,
            "industry": item["industry"]
        })
        
    return stocks

def fetch_fundamental_data(stock_ids, max_stocks=20):
    """
    獲取基本面數據（PE, PB, ROE, 法人持股等），增加平行處理和超時控制
    
    參數:
    - stock_ids: 股票代碼列表
    - max_stocks: 最大處理數量
    
    返回:
    - 包含基本面資訊的 DataFrame
    """
    print(f"[scraper] ⏳ 開始擷取法人與本益比資料 (最多處理 {max_stocks} 檔)...")
    base_url = "https://goodinfo.tw/tw/StockInfo.asp?STOCK_ID="
    
    # 隨機化 User-Agent 以避免被封鎖
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 Edg/94.0.992.38"
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://goodinfo.tw/tw/index.asp"
    }
    
    result = []
    
    # 限制處理的數量
    if len(stock_ids) > max_stocks:
        print(f"[scraper] ⚠️ 限制處理數量為 {max_stocks} 檔股票 (原 {len(stock_ids)} 檔)")
        stock_ids = stock_ids[:max_stocks]

    # 使用優化的重試設置，但減少重試次數
    session = create_retry_session(retries=1, backoff_factor=0.5)
    
    # 並行處理股票，但增加限流控制，減少並行數
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        
        for i, stock_id in enumerate(stock_ids):
            # 每2個請求添加延遲以避免過快請求
            if i > 0 and i % 2 == 0:
                time.sleep(BATCH_DELAY)
            
            futures.append(executor.submit(
                fetch_single_stock_fundamental, 
                stock_id, 
                session, 
                base_url, 
                headers
            ))
        
        # 處理完成的任務
        for future in as_completed(futures):
            try:
                data = future.result()
                if data:
                    result.append(data)
            except Exception as e:
                print(f"[scraper] ⚠️ 基本面數據獲取任務失敗: {e}")

    print(f"[scraper] ✅ 成功獲取 {len(result)} 檔股票的基本面數據")
    return pd.DataFrame(result)

def fetch_single_stock_fundamental(stock_id, session, base_url, headers):
    """獲取單一股票的基本面數據，包含更好的錯誤處理"""
    try:
        stock_id = str(stock_id).replace('="', '').replace('"', '').strip()
        url = base_url + stock_id
        
        # 嘗試重試邏輯，但使用更短的超時
        max_attempts = 1  # 減少重試次數，提高效率
        for attempt in range(max_attempts):
            try:
                resp = session.get(url, headers=headers, timeout=(5, 10))
                if resp.status_code == 200:
                    break
                time.sleep(1)
            except Exception as e:
                if attempt < max_attempts - 1:
                    time.sleep(1)
                else:
                    raise
        
        soup = BeautifulSoup(resp.text, "html.parser")

        tables = pd.read_html(StringIO(str(soup)), flavor="bs4")
        summary_table = None
        for table in tables:
            if "本益比" in str(table):
                summary_table = table
                break

        if summary_table is None or len(summary_table.columns) < 2:
            raise ValueError("無法擷取正確欄位")

        flat = summary_table.values.flatten()
        pe, pb, roe = None, None, None
        for idx, val in enumerate(flat):
            if str(val).strip() == "本益比":
                try:
                    pe = float(flat[idx + 1])
                except:
                    pe = None
            if str(val).strip() == "股價淨值比":
                try:
                    pb = float(flat[idx + 1])
                except:
                    pb = None
            if str(val).strip() == "ROE":
                try:
                    roe = float(flat[idx + 1])
                except:
                    roe = None

        return {
            "證券代號": stock_id,
            "PE": pe,
            "PB": pb,
            "ROE": roe,
            "外資": None,  # 可擴展加入法人持股資訊
            "投信": None,
            "自營商": None,
        }

    except Exception as e:
        print(f"[scraper] ⚠️ {stock_id} 擷取失敗：{e}")
        return None

"""
處理連線超時問題的方案（scraper.py）
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
from io import StringIO
import datetime
from bs4 import BeautifulSoup
import io
import time

# 建立一個可重試的 requests session
def create_retry_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
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
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
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

def get_eps_data():
    """
    抓取所有上市公司的 EPS 和股息資料，增加重試機制
    
    返回:
    - 字典: {stock_id: {"eps": value, "dividend": value}}
    """
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
    
    # 使用重試機制的 session
    session = create_retry_session(retries=5, backoff_factor=1.0)
    
    try:
        # 嘗試獲取每股盈餘資料
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
        
        # 增加重試邏輯和錯誤處理
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # 發送請求，增加超時時間
                eps_res = session.post(
                    eps_url,
                    data=eps_data,
                    headers=headers,
                    timeout=60  # 增加超時時間到60秒
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
                
                # 如果不是最後一次嘗試，暫停一下再重試
                if attempt < max_attempts - 1:
                    time.sleep(5 * (attempt + 1))  # 增加的延遲
            except Exception as e:
                print(f"[scraper] ⚠️ EPS數據請求失敗 (嘗試 {attempt+1}/{max_attempts}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(5 * (attempt + 1))
    except Exception as e:
        print(f"[scraper] ❌ 查無 EPS 表格或格式錯誤：{e}")
    
    # 同樣的方式處理股息資料
    try:
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # 嘗試獲取股息資料
                div_res = session.post(
                    "https://mops.twse.com.tw/mops/web/ajax_t05st34",
                    data={"encodeURIComponent": "1", "step": "1", "firstin": "1", "off": "1", "TYPEK": "sii"},
                    headers=headers, 
                    timeout=60  # 增加超時時間
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
                    time.sleep(5 * (attempt + 1))  # 增加的延遲
            except Exception as e:
                print(f"[scraper] ⚠️ 股息數據請求失敗 (嘗試 {attempt+1}/{max_attempts}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(5 * (attempt + 1))
    except Exception as e:
        print(f"[scraper] ❌ 查無股利表格或格式錯誤：{e}")
    
    # 檢查是否成功獲取數據
    if eps_df.empty and div_df.empty:
        print("[scraper] ⚠️ 無法從公開資訊觀測站獲取數據，嘗試使用替代方案...")
        return get_eps_data_from_yahoo()
    
    # 合併數據
    for _, row in eps_df.iterrows():
        sid = str(row["stock_id"]).zfill(4)
        result[sid] = {"eps": round(row["EPS"], 2), "dividend": None}

    for _, row in div_df.iterrows():
        sid = str(row["stock_id"]).zfill(4)
        if sid not in result:
            result[sid] = {"eps": None, "dividend": None}
        result[sid]["dividend"] = round(row["Dividend"], 2)
    
    print(f"[scraper] ✅ 成功獲取 {len(result)} 檔股票的 EPS 和股息數據")
    return result

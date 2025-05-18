"""
修改 modules/data/scraper.py 中的 get_eps_data 和 get_dividend_data 函數
整合備用方案
"""

def get_eps_data():
    """
    抓取所有上市公司的 EPS 和股息資料
    
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
        
        # 發送請求
        eps_res = requests.post(
            eps_url,
            data=eps_data,
            headers=headers,
            timeout=30
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
            except Exception as e:
                print(f"[scraper] ⚠️ EPS表格解析失敗: {e}")
    except Exception as e:
        print(f"[scraper] ❌ 查無 EPS 表格或格式錯誤：{e}")
    
    try:
        # 嘗試獲取股息資料
        div_res = requests.post(
            "https://mops.twse.com.tw/mops/web/ajax_t05st34",
            data={"encodeURIComponent": "1", "step": "1", "firstin": "1", "off": "1", "TYPEK": "sii"},
            headers=headers, 
            timeout=30
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
            except Exception as e:
                print(f"[scraper] ⚠️ 股息表格解析失敗: {e}")
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


def get_eps_data_from_yahoo():
    """
    使用 Yahoo Finance 獲取 EPS 和股息數據 (備用方案)
    """
    import yfinance as yf
    from concurrent.futures import ThreadPoolExecutor
    from tqdm import tqdm
    
    print("[scraper] 使用 Yahoo Finance 替代方案獲取財務數據...")
    
    # 獲取股票列表
    stock_list = get_all_valid_twse_stocks()
    # 限制股票數量，避免請求過多
    max_stocks = 200
    stock_list = stock_list[:max_stocks]
    
    result = {}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {}
        for stock in stock_list:
            stock_id = stock["stock_id"]
            futures[executor.submit(fetch_stock_finance, stock_id)] = stock_id
        
        for future in tqdm(futures, desc="[scraper] 獲取財務數據"):
            stock_id = futures[future]
            try:
                data = future.result()
                if data:
                    result[stock_id] = data
            except Exception as e:
                print(f"[scraper] ⚠️ 處理 {stock_id} 時出錯: {str(e)[:100]}")
    
    print(f"[scraper] ✅ 成功獲取 {len(result)} 檔股票的財務數據 (Yahoo Finance)")
    return result


def fetch_stock_finance(stock_id):
    """
    從 Yahoo Finance 獲取單一股票的財務數據
    """
    try:
        import yfinance as yf
        
        ticker = yf.Ticker(f"{stock_id}.TW")
        info = ticker.info
        
        # 獲取財務數據
        eps = info.get('trailingEPS')
        dividend_yield = info.get('dividendYield', 0)
        
        # 轉換股息率為百分比
        if dividend_yield:
            dividend_yield = round(dividend_yield * 100, 2)
        
        return {
            "eps": round(float(eps), 2) if eps and eps != 'N/A' else None,
            "dividend": dividend_yield if dividend_yield and dividend_yield > 0 else None
        }
    except Exception:
        return None


def get_dividend_data():
    """
    僅獲取股息資料
    
    返回:
    - 字典: {stock_id: dividend_value}
    """
    all_data = get_eps_data()
    return {sid: val["dividend"] for sid, val in all_data.items() if val["dividend"] is not None}

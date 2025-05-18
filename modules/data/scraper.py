"""
數據爬蟲模組 - 整合 eps_dividend_scraper.py、fundamental_scraper.py、twse_scraper.py
"""
print("[scraper] ✅ 已載入最新版")

import requests
import pandas as pd
from io import StringIO
import datetime
from bs4 import BeautifulSoup
import io


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


def get_all_valid_twse_stocks():
    """
    從證交所獲取所有有效的上市股票
    
    返回:
    - 股票資訊列表 [{"stock_id": id, "stock_name": name, "market_type": type, "industry": ind}]
    """
    url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'big5'

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
        return all_stocks
    except Exception as e:
        print(f"[scraper] ❌ 獲取上市股票列表失敗：{e}")
        # 如果失敗，返回一個包含主要上市公司的備用列表
        print(f"[scraper] ⚠️ 使用備用上市股票列表...")
        return get_backup_stock_list()


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
        
        for future in futures:
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


def get_all_valid_twse_stocks_with_type():
    """
    獲取所有上市股票，並添加股票類型標記（大型股、中小型股、ETF）
    
    返回:
    - 添加了類型的股票列表
    """
    from modules.data.fetcher import is_etf
    
    raw = get_all_valid_twse_stocks()
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


def fetch_fundamental_data(stock_ids):
    """
    獲取基本面數據（PE, PB, ROE, 法人持股等）
    
    參數:
    - stock_ids: 股票代碼列表
    
    返回:
    - 包含基本面資訊的 DataFrame
    """
    print("[scraper] ⏳ 開始擷取法人與本益比資料...")
    base_url = "https://goodinfo.tw/tw/StockInfo.asp?STOCK_ID="
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    result = []

    for stock_id in stock_ids:
        try:
            stock_id = str(stock_id).replace('="', '').replace('"', '').strip()
            url = base_url + stock_id
            resp = requests.get(url, headers=headers, timeout=10)
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
                    pe = float(flat[idx + 1])
                if str(val).strip() == "股價淨值比":
                    pb = float(flat[idx + 1])
                if str(val).strip() == "ROE":
                    roe = float(flat[idx + 1])

            result.append({
                "證券代號": stock_id,
                "PE": pe,
                "PB": pb,
                "ROE": roe,
                "外資": None,  # 可擴展加入法人持股資訊
                "投信": None,
                "自營商": None,
            })

        except Exception as e:
            print(f"[scraper] ⚠️ {stock_id} 擷取失敗：{e}")

    return pd.DataFrame(result)

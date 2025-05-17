"""
數據獲取模組 - 整合 price_fetcher.py 和 hot_stock_scraper.py
"""
print("[fetcher] ✅ 已載入最新版")

import requests
import pandas as pd

def get_top_stocks(limit=100, filter_type=None):
    """
    從台灣證交所取得當日成交量前 N 名股票代碼
    
    參數:
    - limit: 要獲取的股票數量
    - filter_type: 篩選類型 ('small_cap', 'large_cap', None)
    
    返回:
    - 股票代碼列表
    """
    try:
        url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date=&type=ALL"
        res = requests.get(url, timeout=10)
        data = res.json()

        for table in data["tables"]:
            df = pd.DataFrame(table["data"], columns=table["fields"])
            if "證券代號" in df.columns and "成交金額" in df.columns:
                break
        else:
            raise ValueError("無法找到有效的熱門股資料")

        df["成交金額"] = pd.to_numeric(df["成交金額"].str.replace(",", ""), errors="coerce")
        df = df.sort_values(by="成交金額", ascending=False)

        df["證券代號"] = df["證券代號"].astype(str)
        all_ids = df["證券代號"].tolist()

        if filter_type == "small_cap":
            return all_ids[50:50+limit]  # 中小型股（排除前50大）
        elif filter_type == "large_cap":
            return all_ids[:limit]  # 大型股（前N大）
        else:
            return all_ids[:limit]  # 不分類型，直接前N大

    except Exception as e:
        print(f"[fetcher] ⚠️ 熱門股讀取失敗：{e}")
        # 返回預設的熱門股列表作為備用
        default_stocks = ["2330", "2317", "2454", "2303", "2882", "2881", "2412", "2308", "2881", "6505"]
        return default_stocks[:limit]


def fetch_top_100_volume_stocks():
    """
    從台灣證交所取得當日成交量前 100 名股票代碼
    
    返回:
    - 股票代碼列表
    """
    # 直接使用 get_top_stocks 函數，同樣的功能
    return get_top_stocks(limit=100)


def get_latest_valid_trading_date():
    """
    獲取最近的有效交易日期
    
    返回:
    - 日期字符串 (YYYY-MM-DD)
    """
    from datetime import datetime, timedelta
    
    today = datetime.now()
    
    # 如果是週末，回退到最近的週五
    if today.weekday() >= 5:  # 週六日
        offset = today.weekday() - 4
        today -= timedelta(days=offset)
    
    # 檢查是否為假日，若有需要
    # TODO: 實現更完整的假日檢查邏輯
    
    return today.strftime("%Y-%m-%d")


def is_etf(stock_name):
    """
    判斷股票是否為 ETF
    
    參數:
    - stock_name: 股票名稱
    
    返回:
    - 是否為 ETF 的布爾值
    """
    etf_keywords = ["ETF", "元大", "富邦", "永豐", "國泰", "中信", "兆豐"]
    return any(keyword in stock_name for keyword in etf_keywords)

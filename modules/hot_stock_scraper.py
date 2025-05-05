# modules/hot_stock_scraper.py

import requests

def fetch_top_100_volume_stocks():
    """
    從台灣證交所取得當日成交量前 100 名股票代碼
    """
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date=&type=ALL"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        rows = data.get("data9", [])
        stock_ids = [row[0] for row in rows if row[0].isdigit()]
        return stock_ids[:100]
    except Exception as e:
        print("⚠️ 熱門股抓取失敗：", e)
        return []

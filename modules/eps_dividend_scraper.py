# modules/eps_dividend_scraper.py

import requests
from bs4 import BeautifulSoup

def fetch_eps_dividend_info():
    url = "https://goodinfo.tw/tw2/StockList.asp?MARKET_CAT=全部&INDUSTRY_CAT=全部&STOCK_ID=&YEAR_CODE=&RPT_CAT=XX&QRY_TIME=&SHEET_CAT=EPS"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", class_="b1 p4_2 r10 box_shadow")
        if not table:
            print("⚠️ 找不到 EPS 表格")
            return {}

        rows = table.find_all("tr")[1:]
        data = {}
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 10:
                continue
            stock_id = cells[0].text.strip()
            name = cells[1].text.strip()
            try:
                eps = float(cells[4].text.strip())
                yield_rate = float(cells[10].text.strip())
            except:
                eps = 0
                yield_rate = 0

            data[stock_id] = {
                "name": name,
                "EPS": eps,
                "殖利率": yield_rate,
                "法人連買": False  # 預設為 False，之後可改為真實資料
            }
        return data
    except Exception as e:
        print(f"⚠️ EPS 爬蟲失敗：{e}")
        return {}

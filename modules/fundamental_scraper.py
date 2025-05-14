print("[fundamental_scraper] ✅ 已載入最新版（修正 14 欄錯誤）")

import requests
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup

def fetch_fundamental_data(stock_ids):
    print("[fundamental_scraper] 開始擷取法人與本益比資料...")
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
                "外資": None,
                "投信": None,
                "自營商": None,
            })

        except Exception as e:
            print(f"[fundamental_scraper] ⚠️ {stock_id} 擷取失敗：{e}")

    return pd.DataFrame(result)

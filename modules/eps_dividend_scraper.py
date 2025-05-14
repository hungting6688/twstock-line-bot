print("[eps_dividend_scraper] ✅ 已載入最新版（含 int 清洗與字串轉換）")

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

def clean_stock_id(stock_id):
    return str(stock_id).replace('="', '').replace('"', '').strip()

def fetch_eps_dividend_data(stock_ids, max_count=100):
    print(f"[eps_dividend_scraper] 開始擷取 EPS / 殖利率 / YTD（最多 {max_count} 檔）...")
    result = []
    base_url = "https://mops.twse.com.tw/mops/web/ajax_t05st09"

    for idx, stock_id in enumerate(stock_ids[:max_count], 1):
        stock_id = clean_stock_id(stock_id)
        print(f"[eps_dividend_scraper] 第 {idx} 檔：{stock_id}")

        try:
            int(stock_id)  # 防止 ETF 錯誤格式

            resp = requests.get(base_url, params={
                'encodeURIComponent': '1',
                'step': '1',
                'firstin': '1',
                'off': '1',
                'keyword4': stock_id
            }, timeout=10)

            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table", class_="hasBorder")
            if not table:
                raise ValueError("無法找到資料表格")

            rows = table.find_all("tr")[1:]  # 跳過標題列
            eps_values = []
            dividend = 0

            for row in rows:
                cols = [col.text.strip() for col in row.find_all(["td", "th"])]
                if len(cols) >= 8:
                    try:
                        eps = float(cols[7])  # 每股盈餘位置
                        eps_values.append(eps)
                    except:
                        continue
                if len(cols) >= 10:
                    try:
                        dividend = float(cols[9])
                    except:
                        pass

            eps_sum = sum(eps_values[-4:]) if eps_values else 0  # 最近四季 EPS
            result.append({
                "證券代號": stock_id,
                "EPS": eps_sum,
                "殖利率": dividend,
                "YTD報酬率": None,  # 保留後續補上漲幅資訊
            })

        except Exception as e:
            print(f"[eps_dividend_scraper] ❌ 擷取失敗：{stock_id} → {e}")

    print(f"[eps_dividend_scraper] ✅ 擷取完成，共 {len(result)} 檔")
    return pd.DataFrame(result)

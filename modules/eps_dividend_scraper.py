print("[eps_dividend_scraper] ✅ 已載入最新版（含 retry 與容錯）")

import requests
import pandas as pd
from bs4 import BeautifulSoup
from time import sleep
from random import randint

def fetch_eps_dividend_data(stock_ids):
    print(f"[eps_dividend_scraper] 開始擷取 EPS / 殖利率 / YTD（最多 {len(stock_ids)} 檔）...")
    result = []

    for idx, stock_id in enumerate(stock_ids[:100], start=1):
        print(f"[eps_dividend_scraper] 第 {idx} 檔：{stock_id}")
        retries = 3
        for attempt in range(retries):
            try:
                url = f"https://mops.twse.com.tw/mops/web/ajax_t05st09?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4={stock_id}"
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(resp.text, "html.parser")
                
                table = soup.find("table", class_="hasBorder")
                if table is None:
                    raise ValueError("無法找到資料表格")

                rows = table.find_all("tr")
                if len(rows) < 2:
                    raise ValueError("表格資料不足")

                data_row = rows[1].find_all("td")
                if len(data_row) < 10:
                    raise ValueError("欄位數不足")

                eps = data_row[9].text.strip()
                dividend = data_row[7].text.strip()

                eps = float(eps) if eps.replace('.', '', 1).isdigit() else 0.0
                dividend = float(dividend) if dividend.replace('.', '', 1).isdigit() else 0.0

                result.append({
                    "stock_id": stock_id,
                    "eps": eps,
                    "dividend": dividend,
                })
                break  # 若成功則中斷 retry
            except Exception as e:
                if attempt < retries - 1:
                    sleep(randint(1, 3))  # retry 間隔
                    continue
                print(f"[eps_dividend_scraper] ❌ 擷取失敗：{stock_id} → {e}")
                continue

    print(f"[eps_dividend_scraper] ✅ 擷取完成，共 {len(result)} 檔")
    return result

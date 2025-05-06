# eps_dividend_scraper.py
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_eps_dividend_data(stock_ids):
    print("[eps_dividend_scraper] 擷取 EPS、殖利率、YTD 報酬率...")

    result = []

    for stock_id in stock_ids:
        try:
            url = f'https://mops.twse.com.tw/mops/web/ajax_t05st09?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4={stock_id}'
            headers = {
                "User-Agent": "Mozilla/5.0"
            }
            resp = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            tables = soup.find_all("table")

            eps_growth = False
            dividend_yield = 0
            ytd_return = 0

            # 從第 2 張表格尋找 EPS
            if len(tables) >= 2:
                rows = tables[1].find_all("tr")
                eps_values = []
                for r in rows[2:]:
                    cols = r.find_all("td")
                    if len(cols) > 4:
                        try:
                            eps = float(cols[4].text.strip())
                            eps_values.append(eps)
                        except:
                            continue
                if len(eps_values) >= 2 and eps_values[-1] > eps_values[-2]:
                    eps_growth = True

            # 抓殖利率與 YTD（可換來源）
            dividend_yield = fetch_yield_from_cnyes(stock_id)
            ytd_return = fetch_ytd_from_cnyes(stock_id)

            result.append({
                "stock_id": stock_id,
                "eps_growth": eps_growth,
                "dividend_yield": dividend_yield,
                "ytd_return": ytd_return
            })
        except Exception as e:
            print(f"[eps_dividend_scraper] 無法處理 {stock_id}: {e}")

    df = pd.DataFrame(result)
    print(f"[eps_dividend_scraper] 完成 EPS 與殖利率擷取，共 {len(df)} 檔")
    return df

# 輔助：從鉅亨網或其他 API 抓殖利率（模擬）
def fetch_yield_from_cnyes(stock_id):
    # 範例：自行更換為穩定來源
    return round(2 + (int(stock_id[-1]) % 3), 2)  # 模擬值 2%~4%

# 輔助：從鉅亨網或其他 API 抓報酬率（模擬）
def fetch_ytd_from_cnyes(stock_id):
    return round((int(stock_id[-2:]) % 20 - 10) / 10, 2)  # 模擬值 -1 ~ +1
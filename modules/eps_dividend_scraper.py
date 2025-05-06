# modules/eps_dividend_scraper.py

import requests
import pandas as pd
from bs4 import BeautifulSoup

def fetch_eps_dividend_data(stock_ids, limit=20):
    print(f"[eps_dividend_scraper] 開始擷取 EPS / 殖利率 / YTD（最多 {limit} 檔）...")

    result = []

    for i, stock_id in enumerate(stock_ids[:limit]):
        print(f"[eps_dividend_scraper] 第 {i+1} 檔：{stock_id}")
        try:
            url = f'https://mops.twse.com.tw/mops/web/ajax_t05st09?encodeURIComponent=1&step=1&firstin=1&off=1&keyword4={stock_id}'
            headers = { "User-Agent": "Mozilla/5.0" }
            resp = requests.get(url, headers=headers, timeout=10)  # 加 timeout 避免卡住
            soup = BeautifulSoup(resp.text, "html.parser")
            tables = soup.find_all("table")

            eps_growth = False
            dividend_yield = 0.0
            ytd_return = 0.0

            # 嘗試擷取 EPS 資料
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

            # 模擬殖利率與 YTD（未來可接正式資料）
            dividend_yield = round(2 + (int(stock_id[-1]) % 3), 2)
            ytd_return = round((int(stock_id[-2:]) % 20 - 10) / 10, 2)

            result.append({
                "stock_id": stock_id,
                "eps_growth": eps_growth,
                "dividend_yield": dividend_yield,
                "ytd_return": ytd_return
            })

        except Exception as e:
            print(f"[eps_dividend_scraper] ❌ 擷取失敗：{stock_id} → {e}")

    df = pd.DataFrame(result)
    print(f"[eps_dividend_scraper] ✅ 擷取完成，共 {len(df)} 檔")
    return df

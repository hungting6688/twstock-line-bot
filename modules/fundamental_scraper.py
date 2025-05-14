# modules/fundamental_scraper.py
print("[fundamental_scraper] ✅ 已載入最新版")

import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_fundamental_data(stock_ids: list[str]) -> pd.DataFrame:
    all_data = []
    for stock_id in stock_ids:
        try:
            url = f"https://mops.twse.com.tw/mops/web/ajax_t51sb01?encodeURIComponent=1&step=1&firstin=1&off=1&queryName=co_id&inpuType=co_id&TYPEK=sii&co_id={stock_id}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            table = soup.find("table", class_="hasBorder")
            if not table:
                continue

            rows = table.find_all("tr")
            pe_ratio, pb_ratio, roe = None, None, None
            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue
                label = cells[0].text.strip()
                value = cells[1].text.strip().replace(",", "")
                if "本益比" in label:
                    pe_ratio = float(value) if value.replace(".", "").isdigit() else None
                elif "股價淨值比" in label:
                    pb_ratio = float(value) if value.replace(".", "").isdigit() else None
                elif "股東權益報酬率" in label:
                    roe = float(value) if value.replace(".", "").isdigit() else None

            foreign, dealer, investment = fetch_institutional_trading(stock_id)
            all_data.append({
                "stock_id": stock_id,
                "pe_ratio": pe_ratio,
                "pb_ratio": pb_ratio,
                "roe": roe,
                "foreign_buy": foreign,
                "dealer_buy": dealer,
                "investment_buy": investment,
                "buy_total": sum(x for x in [foreign, dealer, investment] if x is not None)
            })

        except Exception as e:
            print(f"[fundamental_scraper] ⚠️ 擷取 {stock_id} 資料失敗：{e}")

    return pd.DataFrame(all_data)

def fetch_institutional_trading(stock_id: str):
    try:
        today = datetime.today().strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/fund/T86?response=json&date={today}&selectType=ALL"
        response = requests.get(url, timeout=10)
        data = response.json()
        df = pd.DataFrame(data["data"], columns=data["fields"])
        df = df[df["證券代號"] == stock_id]
        if df.empty:
            return None, None, None
        row = df.iloc[0]
        foreign = safe_int(row["外陸資買賣超股數(不含外資自營商)"])
        dealer = safe_int(row["自營商買賣超股數"])
        investment = safe_int(row["投信買賣超股數"])
        return foreign, dealer, investment
    except Exception as e:
        print(f"[fundamental_scraper] ⚠️ 法人資料失敗：{e}")
        return None, None, None

def safe_int(value):
    try:
        return int(str(value).replace(",", ""))
    except:
        return None

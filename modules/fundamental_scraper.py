# modules/fundamental_scraper.py
print("[fundamental_scraper] ✅ 已載入最新版")

import time
import requests
import pandas as pd
from bs4 import BeautifulSoup

def fetch_fundamental_data(stock_ids):
    base_url = "https://mops.twse.com.tw/mops/web/ajax_t05st32"
    headers = {
        "User-Agent": "Mozilla/5.0",
    }

    result = []

    for sid in stock_ids:
        try:
            stock_id = str(sid).zfill(4)

            # 查詢法人買賣超 (以證交所為例)
            url = f"https://www.twse.com.tw/fund/TWT38U?response=json&selectType=ALLBUT0999&_=1234567890"
            res = requests.get(url, headers=headers, timeout=10)
            data = res.json().get("data", [])
            df = pd.DataFrame(data, columns=[
                "證券代號", "證券名稱", "外陸資買進股數", "外陸資賣出股數", "外陸資買賣超股數",
                "投信買進股數", "投信賣出股數", "投信買賣超股數",
                "自營商買進股數", "自營商賣出股數", "自營商買賣超股數",
                "合計買進股數", "合計賣出股數", "合計買賣超股數"
            ])
            df = df[df["證券代號"] == stock_id]
            if df.empty:
                continue

            buy_total = int(df["合計買賣超股數"].values[0].replace(",", ""))
            foreign_buy = int(df["外陸資買賣超股數"].values[0].replace(",", ""))
            invest_buy = int(df["投信買賣超股數"].values[0].replace(",", ""))
            dealer_buy = int(df["自營商買賣超股數"].values[0].replace(",", ""))

            # 查詢本益比、PB、ROE（使用 Yahoo Finance）
            url_yahoo = f"https://tw.stock.yahoo.com/quote/{stock_id}/key-statistics"
            res2 = requests.get(url_yahoo, headers=headers, timeout=10)
            soup = BeautifulSoup(res2.text, "html.parser")
            rows = soup.select("li div[class*='D(f)']")
            pe, pb, roe = None, None, None
            for r in rows:
                text = r.get_text()
                if "本益比" in text:
                    pe = float(text.split("本益比")[-1].strip())
                elif "股價淨值比" in text:
                    pb = float(text.split("股價淨值比")[-1].strip())
                elif "ROE" in text:
                    roe = float(text.split("ROE")[-1].strip().replace("%", ""))

            result.append({
                "證券代號": stock_id,
                "法人買超": buy_total,
                "外資買超": foreign_buy,
                "投信買超": invest_buy,
                "自營買超": dealer_buy,
                "PE": pe,
                "PB": pb,
                "ROE": roe,
            })

            time.sleep(0.3)  # 防止被擋

        except Exception as e:
            print(f"[fundamental_scraper] ⚠️ {stock_id} 擷取失敗：{e}")
            continue

    return pd.DataFrame(result)

# modules/fundamental_scraper.py

import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_fundamental_data():
    print("[fundamental_scraper] 擷取法人買賣超資料...")
    try:
        today = datetime.today()
        date_str = f"{today.year - 1911:03d}{today.strftime('%m%d')}"
        url = f"https://www.twse.com.tw/fund/T86?response=html&date={date_str}&selectType=ALL"

        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.find_all("table")
        print(f"[fundamental_scraper] ⚙️ 擷取表格數量：{len(tables)}")

        if not tables:
            raise ValueError("No tables found")

        df = pd.read_html(str(tables[0]))[0]
        df.columns = df.columns.droplevel(0) if isinstance(df.columns, pd.MultiIndex) else df.columns

        if "證券代號" not in df.columns or "三大法人買賣超合計" not in df.columns:
            raise ValueError("找不到包含法人資料的合法表格")

        df = df.rename(columns={
            "證券代號": "stock_id",
            "三大法人買賣超合計": "buy_total"
        })
        df = df[["stock_id", "buy_total"]].dropna()
        df["stock_id"] = df["stock_id"].astype(str).str.strip()
        df["buy_total"] = df["buy_total"].astype(str).str.replace(",", "").astype(float)
        print(f"[fundamental_scraper] ✅ 擷取完成，共 {len(df)} 筆資料")
        return df

    except Exception as e:
        print(f"[fundamental_scraper] ⚠️ 擷取失敗，自動回傳空資料：{e}")
        return pd.DataFrame(columns=["stock_id", "buy_total"])

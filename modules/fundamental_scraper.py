# modules/fundamental_scraper.py

import pandas as pd
import requests
from bs4 import BeautifulSoup

def fetch_fundamental_data():
    print("[fundamental_scraper] 擷取法人買賣超資料...")

    url = "https://www.twse.com.tw/zh/page/trading/fund/T86.html"
    try:
        res = requests.get(url, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        tables = pd.read_html(res.text)

        print(f"[fundamental_scraper] ⚙️ 擷取表格數量：{len(tables)}")

        # 嘗試抓出第一個有「證券代號」的表格
        target_df = None
        for df in tables:
            if any("代號" in str(col) for col in df.columns):
                target_df = df.copy()
                break

        if target_df is None:
            raise ValueError("找不到包含法人資料的合法表格")

        # 標準化欄位
        target_df.columns = target_df.columns.astype(str)
        target_df.columns = target_df.columns.str.strip()
        target_df = target_df.rename(columns={
            target_df.columns[0]: "stock_id",
            target_df.columns[1]: "stock_name",
            target_df.columns[-1]: "buy_total"
        })

        df = target_df[["stock_id", "buy_total"]].copy()
        df["stock_id"] = df["stock_id"].astype(str).str.zfill(4)
        df["buy_total"] = pd.to_numeric(df["buy_total"].astype(str).str.replace(",", ""), errors="coerce").fillna(0)

        print(f"[fundamental_scraper] ✅ 擷取完成，共 {len(df)} 筆")
        return df

    except Exception as e:
        print(f"[fundamental_scraper] ⚠️ 擷取失敗，自動回傳空資料：{e}")
        return pd.DataFrame(columns=["stock_id", "buy_total"])

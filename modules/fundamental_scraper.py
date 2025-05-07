# modules/fundamental_scraper.py
import pandas as pd
import requests
from io import StringIO

def fetch_fundamental_data():
    url = "https://www.twse.com.tw/fund/T86?response=html&date=&selectType=ALLBUT0999"
    print("[fundamental_scraper] 擷取法人買賣超資料...")

    try:
        res = requests.get(url, timeout=10)
        tables = pd.read_html(StringIO(res.text))
        print(f"[fundamental_scraper] ⚙️ 擷取表格數量：{len(tables)}")

        # 嘗試找出包含「代號」與「法人買超金額」的表格
        df = None
        for t in tables:
            cols = [str(c) for c in t.columns]
            if any("代號" in c or "名稱" in c for c in cols) and any("合計" in c or "三大法人" in c for c in cols):
                df = t
                break

        if df is None:
            raise ValueError("找不到包含法人資料的合法表格")

        df.columns = df.columns.astype(str)
        df = df.rename(columns={
            df.columns[0]: "stock_id",
            df.columns[1]: "stock_name",
            df.columns[-1]: "buy_total"
        })

        df["stock_id"] = df["stock_id"].astype(str).str.zfill(4)
        df["buy_total"] = pd.to_numeric(df["buy_total"], errors="coerce").fillna(0).astype(int)
        df = df[["stock_id", "buy_total"]]
        return df

    except Exception as e:
        print(f"[fundamental_scraper] ⚠️ 擷取失敗，自動回傳空資料：{e}")
        return pd.DataFrame(columns=["stock_id", "buy_total"])

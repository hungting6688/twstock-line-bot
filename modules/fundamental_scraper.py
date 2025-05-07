import requests
import pandas as pd
from io import StringIO

def fetch_fundamental_data():
    print("[fundamental_scraper] 擷取法人買賣超資料...")

    url = "https://www.twse.com.tw/fund/BFI82U?response=html"

    try:
        res = requests.get(url, timeout=10)
        res.encoding = "utf-8"

        # 嘗試用 read_html 擷取表格
        tables = pd.read_html(res.text)
        print(f"[fundamental_scraper] ⚙️ 擷取表格數量：{len(tables)}")

        df = None
        for i, t in enumerate(tables):
            if "證券代號" in t.columns.tolist()[0] or "證券名稱" in t.columns.tolist():
                df = t
                break

        if df is None:
            raise ValueError("找不到包含法人資料的合法表格")

        # 標準化欄位
        df.columns = df.columns.str.strip()
        df = df.rename(columns={
            df.columns[0]: "stock_id",
            df.columns[1]: "stock_name",
            df.columns[-1]: "buy_total"  # 三大法人買賣超合計
        })

        df["stock_id"] = df["stock_id"].astype(str).str.zfill(4)
        df["buy_total"] = pd.to_numeric(df["buy_total"].astype(str).str.replace(",", ""), errors="coerce").fillna(0)

        return df[["stock_id", "buy_total"]]

    except Exception as e:
        print(f"[fundamental_scraper] ⚠️ 擷取失敗，自動回傳空資料：{e}")
        return pd.DataFrame(columns=["stock_id", "buy_total"])

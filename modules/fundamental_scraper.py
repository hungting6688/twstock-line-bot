# modules/fundamental_scraper.py

import pandas as pd
import requests
from io import StringIO

def fetch_fundamental_data():
    try:
        url = "https://www.twse.com.tw/fund/T86?response=csv&date=&selectType=ALL"
        response = requests.get(url)
        response.encoding = "utf-8"
        raw_csv = response.text

        # 嘗試解析所有表格
        tables = pd.read_html(StringIO(raw_csv), encoding='utf-8')
        print(f"[fundamental_scraper] ⚙️ 擷取表格數量：{len(tables)}")

        # 自動偵測含法人資料的合法表格
        for i, t in enumerate(tables):
            colnames = t.columns.astype(str).tolist()
            if any("代號" in c or "名稱" in c for c in colnames) and any("三大法人" in c or "合計" in c for c in colnames):
                df = t
                break
        else:
            raise ValueError("找不到包含法人資料的合法表格")

        # 清洗與轉換欄位
        df.columns = [str(col).strip() for col in df.columns]
        df = df.rename(columns={df.columns[0]: "stock_id", df.columns[1]: "stock_name"})
        df = df[["stock_id", "stock_name", df.columns[-1]]]
        df.columns = ["stock_id", "stock_name", "buy_total"]

        df["stock_id"] = df["stock_id"].astype(str).str.zfill(4)
        df["buy_total"] = pd.to_numeric(df["buy_total"].astype(str).str.replace(",", ""), errors="coerce").fillna(0)

        return df[["stock_id", "buy_total"]]

    except Exception as e:
        print(f"[fundamental_scraper] ⚠️ 擷取失敗，自動回傳空資料：{e}")
        return pd.DataFrame(columns=["stock_id", "buy_total"])

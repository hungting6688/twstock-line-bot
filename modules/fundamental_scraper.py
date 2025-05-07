import pandas as pd
import requests
from io import StringIO

def fetch_fundamental_data():
    print("[fundamental_scraper] 擷取法人買賣超資料...")

    url = "https://www.twse.com.tw/fund/TWT38U?response=csv&date=&selectType=ALL"

    try:
        res = requests.get(url)
        res.encoding = 'utf-8'

        # 擷取所有表格
        dfs = pd.read_html(StringIO(res.text), flavor='bs4')
        for i, df in enumerate(dfs):
            preview = df.columns.tolist()
            print(f"[fundamental_scraper] 欄位預覽 [{i}]: {preview}")
            if "證券代號" in preview:
                df.columns = df.columns.str.strip()
                df = df.rename(columns={
                    "證券代號": "stock_id",
                    "買賣超股數": "buy_total"
                })
                df = df[["stock_id", "buy_total"]]
                df["stock_id"] = df["stock_id"].astype(str).str.zfill(4)
                df["buy_total"] = pd.to_numeric(df["buy_total"].astype(str).str.replace(",", ""), errors="coerce").fillna(0).astype(int)
                print(f"[fundamental_scraper] ✅ 擷取完成，共 {len(df)} 檔")
                return df

        raise ValueError("❌ 找不到正確欄位的法人表格")

    except Exception as e:
        print(f"[fundamental_scraper] ⚠️ 擷取失敗，自動回傳空資料：{e}")
        return pd.DataFrame(columns=["stock_id", "buy_total"])

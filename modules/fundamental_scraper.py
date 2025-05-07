import pandas as pd
import requests
from bs4 import BeautifulSoup

def fetch_fundamental_data():
    print("[fundamental_scraper] 擷取法人買賣超資料...")

    url = "https://www.twse.com.tw/fund/T86?response=html&selectType=ALLBUT0999&date=&_=0"

    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        table = soup.find("table")
        if table is None:
            raise ValueError("無法擷取法人買賣超主表格")

        df = pd.read_html(str(table))[0]

        # 強制單層欄位名稱
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.columns = df.columns.str.replace(r"\s", "", regex=True)
        df = df.rename(columns={"證券代號": "stock_id", "外資及陸資買賣超股數": "buy_total"})

        df["buy_total"] = df["buy_total"].astype(str).str.replace(",", "").astype(float)
        df["stock_id"] = df["stock_id"].astype(str).str.strip()

        df = df[["stock_id", "buy_total"]].dropna()
        print(f"[fundamental_scraper] ✅ 擷取成功，共 {len(df)} 檔")
        return df

    except Exception as e:
        print(f"[fundamental_scraper] ⚠️ 擷取失敗，自動回傳空資料：{e}")
        return pd.DataFrame(columns=["stock_id", "buy_total"])

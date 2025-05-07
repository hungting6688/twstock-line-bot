import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_fundamental_data():
    print("[fundamental_scraper] 擷取法人買賣超資料...")
    try:
        today = datetime.today()
        roc_year = today.year - 1911
        date_str = f"{roc_year}年{today.month:02d}月{today.day:02d}日"

        url = "https://www.twse.com.tw/fund/T86?response=html&selectType=ALLBUT0999&_=1680500000000"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        tables = soup.find_all("table")
        print(f"[fundamental_scraper] ⚙️ 擷取表格數量：{len(tables)}")
        if not tables:
            raise ValueError("No tables found")

        df = pd.read_html(str(tables[0]))[0]

        # 重新命名欄位（視實際情況可能要調整）
        df.columns = df.columns.get_level_values(0) if isinstance(df.columns, pd.MultiIndex) else df.columns
        df.columns = df.columns.str.replace("\s", "", regex=True)

        if '證券代號' not in df.columns or '外資及陸資(不含外資自營商)買賣超股數' not in df.columns:
            raise ValueError("找不到包含法人資料的合法表格")

        df = df.rename(columns={
            "證券代號": "stock_id",
            "外資及陸資(不含外資自營商)買賣超股數": "buy_total"
        })

        df = df[["stock_id", "buy_total"]]
        df["buy_total"] = (
            df["buy_total"].astype(str)
              .str.replace(",", "")
              .str.replace("--", "0")
              .astype(float)
        )

        return df

    except Exception as e:
        print(f"[fundamental_scraper] ⚠️ 擷取失敗，自動回傳空資料：{e}")
        return pd.DataFrame(columns=["stock_id", "buy_total"])

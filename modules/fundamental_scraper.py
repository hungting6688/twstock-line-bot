import pandas as pd
import requests
from datetime import datetime, timedelta
import io

def fetch_fundamental_data():
    print("[fundamental_scraper] 擷取法人買賣超資料...")

    try:
        # 使用昨日日期
        date = (datetime.today() - timedelta(days=1)).strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={date}&type=ALLBUT0999"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        content = res.text

        # 處理 CSV 格式（移除無效行）
        lines = content.splitlines()
        cleaned_lines = [line for line in lines if not line.startswith('=')]
        csv_data = "\n".join(cleaned_lines)

        # 讀取為 DataFrame（中文欄位）
        df = pd.read_csv(io.StringIO(csv_data))

        # 過濾出需要的欄位（股票代號與法人買超欄位）
        df = df[df["證券代號"].apply(lambda x: str(x).isdigit())]
        df["stock_id"] = df["證券代號"].astype(str)

        # 整理三大法人買賣超欄位，加總為 buy_total
        df["buy_total"] = (
            df["外陸資買進股數(不含外資自營商)"].replace(",", "", regex=True).astype(float) -
            df["外陸資賣出股數(不含外資自營商)"].replace(",", "", regex=True).astype(float) +
            df["投信買進股數"].replace(",", "", regex=True).astype(float) -
            df["投信賣出股數"].replace(",", "", regex=True).astype(float) +
            df["自營商買進股數(自行買賣)"].replace(",", "", regex=True).astype(float) -
            df["自營商賣出股數(自行買賣)"].replace(",", "", regex=True).astype(float)
        )

        return df[["stock_id", "buy_total"]]

    except Exception as e:
        print(f"[fundamental_scraper] ⚠️ 擷取失敗，自動回傳空資料：{e}")
        return pd.DataFrame(columns=["stock_id", "buy_total"])

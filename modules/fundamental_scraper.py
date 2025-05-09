import pandas as pd
import requests
from datetime import datetime, timedelta
import io

def fetch_fundamental_data():
    print("[fundamental_scraper] 擷取法人買賣超資料...")

    try:
        # 取昨日日期（證交所每日法人統計）
        date = (datetime.today() - timedelta(days=1)).strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={date}&type=ALLBUT0999"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        content = res.text

        # 清理原始 CSV
        lines = content.splitlines()
        cleaned_lines = [line for line in lines if not line.startswith('=') and ',' in line]
        csv_data = "\n".join(cleaned_lines)

        # 使用 pandas 讀入並跳過錯誤行
        df = pd.read_csv(io.StringIO(csv_data), on_bad_lines="skip")

        # 過濾代號為數字的股票
        df = df[df["證券代號"].apply(lambda x: str(x).isdigit())]
        df["stock_id"] = df["證券代號"].astype(str)

        # 整理法人三方買賣合計
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

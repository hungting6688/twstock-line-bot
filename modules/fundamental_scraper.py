import pandas as pd
import requests
from datetime import datetime, timedelta
import io

def fetch_fundamental_data():
    print("[fundamental_scraper] 擷取法人買賣超資料...")

    try:
        # 取昨日日期
        date = (datetime.today() - timedelta(days=1)).strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={date}&type=ALLBUT0999"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        content = res.text

        # 清理原始 CSV
        lines = content.splitlines()
        cleaned_lines = [line for line in lines if not line.startswith('=') and ',' in line]
        csv_data = "\n".join(cleaned_lines)

        # 安全解析 CSV 並驗證欄位存在
        df = pd.read_csv(io.StringIO(csv_data), on_bad_lines="skip")

        if "證券代號" not in df.columns:
            raise ValueError("CSV 欄位中缺少『證券代號』，可能資料格式異常")

        df = df[df["證券代號"].apply(lambda x: str(x).isdigit())]
        df["stock_id"] = df["證券代號"].astype(str)

        # 統整法人買賣超欄位
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

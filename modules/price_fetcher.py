import pandas as pd
import requests
import io
from datetime import datetime

def fetch_price_data(min_turnover=5000, limit=100, mode="opening", strategy=None):
    print("[price_fetcher] ✅ 使用 TWSE CSV 報表穩定解析版本")

    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={datetime.today().strftime('%Y%m%d')}&type=ALL"

    try:
        response = requests.get(url, timeout=10)
        lines = response.text.splitlines()
        cleaned = [line for line in lines if line.count(",") >= 16 and "證券代號" not in line]
        cleaned_csv = "\n".join(["證券代號,證券名稱,成交股數,成交筆數,成交金額,開盤價,最高價,最低價,收盤價,漲跌(+/-),漲跌價差,最後揭示買價,最後揭示買量,最後揭示賣價,最後揭示賣量,本益比"] + cleaned)

        df = pd.read_csv(io.StringIO(cleaned_csv))
        df = df.rename(columns=lambda x: x.strip())
        df = df.rename(columns={"證券代號": "stock_id", "證券名稱": "stock_name", "成交金額": "turnover"})

        df["turnover"] = df["turnover"].replace(",", "", regex=True).astype(float)
        df = df[df["turnover"] >= min_turnover]
        df = df[df["stock_id"].astype(str).str.isnumeric()]

        df = df[["stock_id", "stock_name", "turnover"]].head(limit)
        print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame(columns=["stock_id", "stock_name", "turnover"])

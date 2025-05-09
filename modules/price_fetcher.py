# ✅ price_fetcher.py（回復接近原本成功版本的轉換邏輯）
import pandas as pd
import requests
from io import StringIO
from datetime import datetime

def fetch_price_data(min_turnover=1_000_000, limit=100, mode="opening", strategy=None):
    print("[price_fetcher] ✅ 使用 TWSE CSV 報表穩定解析版本")
    today = datetime.today().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={today}&type=ALLBUT0999"

    try:
        res = requests.get(url, timeout=10)
        raw_text = res.text

        # 篩選有意義的資料行
        lines = [line for line in raw_text.splitlines() if line.count(",") > 5 and ('證券代號' in line or line[:1].isdigit())]
        cleaned_csv = "\n".join(lines)
        df = pd.read_csv(StringIO(cleaned_csv))

        df.columns = df.columns.str.strip()
        print("[price_fetcher] 欄位名稱：", df.columns.tolist())

        df = df.rename(columns={
            "證券代號": "stock_id",
            "證券名稱": "stock_name",
            "收盤價": "close",
            "成交金額": "turnover",
            "成交股數": "volume"
        })

        df = df[df["stock_id"].astype(str).str.isnumeric()]

        # 回復早期成功版本的轉換邏輯
        df["turnover"] = pd.to_numeric(df["turnover"].astype(str).str.replace(",", "", regex=False), errors="coerce")
        df["close"] = pd.to_numeric(df["close"].astype(str).str.replace(",", "", regex=False), errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"].astype(str).str.replace(",", "", regex=False), errors="coerce")

        df = df[df["turnover"] >= min_turnover]
        df = df.sort_values(by="turnover", ascending=False).head(limit).reset_index(drop=True)

        print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")
        print("[price_fetcher] 前幾筆熱門股：")
        print(df[["stock_id", "stock_name", "turnover"]].head())
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()
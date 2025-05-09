import pandas as pd
import requests
from io import StringIO
from datetime import datetime

def fetch_price_data(min_turnover=50000000, limit=100, mode="opening", strategy=None):
    print("[price_fetcher] ✅ 使用 TWSE CSV 報表穩定解析版本")

    today = datetime.today().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={today}&type=ALLBUT0999"
    headers = {"User-Agent": "Mozilla/5.0"}

    res = requests.get(url, headers=headers, timeout=10)
    csv_content = res.text

    # 篩除無效行
    lines = [line for line in csv_content.splitlines() if ',' in line and '"' not in line]
    cleaned_csv = "\n".join(lines)
    df = pd.read_csv(StringIO(cleaned_csv))

    print(f"[price_fetcher] 欄位名稱： {list(df.columns)}")

    # 修正欄位名稱
    df.rename(columns={"資訊代號": "stock_id", "資訊名稱": "stock_name"}, inplace=True)
    df = df.rename(columns={df.columns[0]: "stock_id", df.columns[1]: "stock_name"})

    # 轉換成交易金額
    print("[debug] 成交金額前五筆原始值：")
    print(df["成交金額"].head(5).tolist())

    df["turnover"] = pd.to_numeric(df["成交金額"].astype(str).str.replace(",", "", regex=False), errors="coerce")

    print("[debug] 成交金額轉為數值後前五筆：")
    print(df["turnover"].head(5).tolist())

    df = df[df["turnover"] >= min_turnover].copy()
    df = df.sort_values(by="turnover", ascending=False).head(limit)

    df = df[["stock_id", "stock_name", "turnover"]]
    print(f"[price_fetcher] ✅ 共取得 {len(df)} 横營股")
    print("[price_fetcher] 前幾筆熱門股：")
    print(df.head())

    return df
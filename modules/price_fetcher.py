# modules/price_fetcher.py
import pandas as pd
import requests
from io import StringIO
from datetime import datetime

def fetch_price_data(min_turnover=5000, limit=100, mode="opening", strategy=None):
    print("[price_fetcher] ✅ 使用 TWSE CSV 報表穩定解析版本")

    today = datetime.today().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={today}&type=ALLBUT0999"
    res = requests.get(url)
    content = res.text

    lines = content.splitlines()
    cleaned_lines = [line for line in lines if ',' in line and not line.startswith('=')]
    cleaned_csv = "\n".join(cleaned_lines)

    try:
        df = pd.read_csv(StringIO(cleaned_csv), on_bad_lines="skip")
    except Exception as e:
        print(f"[price_fetcher] ❌ CSV 解析錯誤：{e}")
        return pd.DataFrame(columns=["stock_id", "stock_name", "turnover"])

    print(f"[price_fetcher] 欄位名稱： {df.columns.tolist()}")

    df = df[df["證券代號"].astype(str).str.isnumeric()]
    df["stock_id"] = df["證券代號"].astype(str)
    df["stock_name"] = df["證券名稱"]
    df["turnover"] = df["成交金額"].replace(",", "", regex=True).astype(float)

    if df.empty:
        print("[price_fetcher] ⚠️ 表格為空")
        return pd.DataFrame(columns=["stock_id", "stock_name", "turnover"])

    print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")

    df = df[df["turnover"] >= min_turnover * 1000]
    df = df.sort_values(by="turnover", ascending=False)

    print(f"[price_fetcher] 前幾筆熱門股：\n{df[['stock_id', 'stock_name', 'turnover']].head(3)}")
    return df[["stock_id", "stock_name", "turnover"]].head(limit).reset_index(drop=True)

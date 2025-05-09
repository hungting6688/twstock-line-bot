import requests
import pandas as pd
from io import StringIO
from datetime import datetime

def fetch_price_data(min_turnover=50_000_000, limit=100, mode="opening", strategy=None):
    print("[price_fetcher] ✅ 使用 TWSE CSV 報表穩定解析版本")

    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={}&type=ALLBUT0999"
    today = datetime.today().strftime("%Y%m%d")
    full_url = url.format(today)

    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(full_url, headers=headers)
    content = res.text

    # 清理 CSV 內容
    lines = content.splitlines()
    cleaned_lines = [line for line in lines if ',' in line and not line.startswith('=')]
    cleaned_csv = "\n".join(cleaned_lines)

    if not cleaned_csv.strip() or "證券代號" not in cleaned_csv:
        print("[price_fetcher] ⚠️ 檔案無效或無資料，跳過讀取")
        return pd.DataFrame(columns=["stock_id", "stock_name", "turnover"])

    df = pd.read_csv(StringIO(cleaned_csv))

    print("[price_fetcher] 欄位名稱：", list(df.columns))

    df = df.rename(columns={
        "證券代號": "stock_id",
        "證券名稱": "stock_name",
        "成交金額": "turnover"
    })

    df = df[["stock_id", "stock_name", "turnover"]]
    df["turnover"] = pd.to_numeric(df["turnover"].astype(str).str.replace(",", "", regex=True), errors="coerce")

    print("[debug] 成交金額最大值：", df["turnover"].max())
    print("[debug] 未篩選前前幾筆 turnover：")
    print(df.head())

    df = df.dropna(subset=["turnover"])
    df = df[df["turnover"] >= min_turnover]
    df = df.sort_values(by="turnover", ascending=False).head(limit)

    print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")
    print("[price_fetcher] 前幾筆熱門股：")
    print(df[["stock_id", "stock_name", "turnover"]].head())

    return df.reset_index(drop=True)
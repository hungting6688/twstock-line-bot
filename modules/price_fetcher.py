# ✅ modules/price_fetcher.py（參照穩定成功版本，並保留可擴充欄位）

import requests
import pandas as pd
from io import StringIO
from datetime import datetime

def fetch_price_data(min_turnover=50000000, limit=100, mode="opening", strategy=None):
    print("[price_fetcher] ✅ 使用 TWSE CSV 報表穩定解析版本")

    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={}&type=ALLBUT0999"
    today = datetime.today().strftime("%Y%m%d")
    response = requests.get(url.format(today))
    raw_text = response.text

    # 去除開頭與無效列
    cleaned_lines = [line for line in raw_text.split("\n") if len(line.split('",')) > 10]
    cleaned_csv = "\n".join(cleaned_lines)

    try:
        df = pd.read_csv(StringIO(cleaned_csv))
    except Exception as e:
        print(f"[price_fetcher] ❌ 解析 CSV 失敗: {e}")
        return pd.DataFrame(columns=["stock_id", "stock_name", "turnover"])

    print(f"[price_fetcher] 欄位名稱： {list(df.columns)}")

    # 編碼與條件篩選
    df = df.rename(columns={
        "證券代號": "stock_id",
        "證券名稱": "stock_name",
        "成交金額": "turnover"
    })

    df = df[df["stock_id"].astype(str).str.isnumeric()]  # 限定數字代號

    df["turnover"] = pd.to_numeric(df["turnover"], errors="coerce")
    df = df.dropna(subset=["turnover"])

    print(f"[price_fetcher] 清理後計算成交金額")
    df = df[df["turnover"] >= min_turnover]
    df = df.sort_values(by="turnover", ascending=False).head(limit)

    df = df[["stock_id", "stock_name", "turnover"]].reset_index(drop=True)
    print(f"[price_fetcher] ✅ 共取得 {len(df)} 横營股")
    print(f"[price_fetcher] 前幾筆熱門股：\n{df.head()}")

    return df

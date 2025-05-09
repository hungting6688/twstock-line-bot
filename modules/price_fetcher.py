# ✅ price_fetcher.py（強化欄位解析與除錯）
import pandas as pd
import requests
from io import StringIO
from datetime import datetime

def fetch_price_data(min_turnover=40000000, limit=100, mode="opening", strategy=None):
    print("[price_fetcher] ✅ 使用 TWSE CSV 報表穩定解析版本")
    today = datetime.today().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={today}&type=ALLBUT0999"

    try:
        res = requests.get(url, timeout=10)
        raw_text = res.text
        lines = [line for line in raw_text.splitlines() if line.count(",") > 5 and '證券代號' in line or line[0:1].isdigit()]
        cleaned_csv = "\n".join(lines)
        df = pd.read_csv(StringIO(cleaned_csv))

        # 清理欄位名稱與空白
        df.columns = df.columns.str.strip()
        print("[price_fetcher] 欄位名稱：", df.columns.tolist())

        df = df.rename(columns={
            "證券代號": "stock_id",
            "證券名稱": "stock_name",
            "收盤價": "close",
            "成交股數": "volume",
            "成交金額": "turnover"
        })

        df = df[df["stock_id"].astype(str).str.isnumeric()]

        # 轉換數值欄位
        for col in ["close", "volume", "turnover"]:
            df[col] = df[col].astype(str).str.replace(",", "", regex=False).replace("--", "0")
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # 篩選成交金額門檻
        df = df[df["turnover"] >= min_turnover]

        # 依成交金額排序
        df = df.sort_values(by="turnover", ascending=False).head(limit).reset_index(drop=True)
        print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()

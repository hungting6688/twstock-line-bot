# modules/price_fetcher.py
import pandas as pd
import requests
from io import StringIO
from datetime import datetime

def fetch_price_data(min_turnover=50000000, limit=100, mode="opening", strategy=None):
    print("[price_fetcher] ✅ 使用 TWSE CSV 報表穩定解析版本")

    try:
        date_str = datetime.today().strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={date_str}&type=ALLBUT0999"
        res = requests.get(url)
        res.encoding = "utf-8"
        raw_csv = res.text

        # 清除非資料行
        lines = raw_csv.splitlines()
        cleaned = [line for line in lines if line.count(",") > 3 and "--" not in line and "證券代號" not in line[:5]]
        cleaned_csv = "\n".join(cleaned)

        df = pd.read_csv(StringIO(cleaned_csv), engine="python")
        df.columns = df.columns.str.strip()

        df = df.rename(columns={"證券代號": "stock_id", "證券名稱": "stock_name", "成交金額": "turnover"})
        df = df[["stock_id", "stock_name", "turnover"]]
        df = df[df["stock_id"].astype(str).str.isnumeric()]
        df["turnover"] = df["turnover"].replace(",", "", regex=True).astype(float)

        max_turnover = df["turnover"].max()
        print(f"[price_fetcher] 成交金額最大值： {max_turnover}")
        print("[price_fetcher] 未篩選前前幾筆 turnover：")
        print(df[["stock_id", "stock_name", "turnover"]].head())

        df_filtered = df[df["turnover"] >= min_turnover].sort_values("turnover", ascending=False).head(limit)
        print(f"[price_fetcher] ✅ 共取得 {len(df_filtered)} 檔熱門股")
        print("[price_fetcher] 前幾筆熱門股：")
        print(df_filtered[["stock_id", "stock_name", "turnover"]].head())

        return df_filtered.reset_index(drop=True)

    except Exception as e:
        print(f"[price_fetcher] ⚠️ 擷取失敗：{e}")
        return pd.DataFrame(columns=["stock_id", "stock_name", "turnover"])
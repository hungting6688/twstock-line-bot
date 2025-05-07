import pandas as pd
import requests
from io import StringIO
from datetime import datetime

def fetch_price_data(min_turnover=50000000, limit=450):
    print("[price_fetcher] ✅ 使用 TWSE CSV 版本")

    today_str = datetime.today().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={today_str}&type=ALL"

    try:
        res = requests.get(url, timeout=10)
        res.encoding = "big5"  # TWSE 使用 big5 編碼

        # 濾掉前面非資料列
        csv_text = "\n".join([line for line in res.text.splitlines() if line.count(",") > 10])

        df = pd.read_csv(StringIO(csv_text))
        df.columns = df.columns.str.replace(r"\s", "", regex=True)

        # 欄位標準化
        df = df.rename(columns={
            "證券代號": "stock_id", "代號": "stock_id",
            "證券名稱": "stock_name", "名稱": "stock_name",
            "成交金額(千元)": "turnover", "成交金額": "turnover"
        })

        df = df[["stock_id", "stock_name", "turnover"]].dropna()
        df["turnover"] = df["turnover"].astype(str).str.replace(",", "").astype(float) * 1000
        df = df[df["turnover"] >= min_turnover]

        # 只抓股票或 ETF（含字母結尾）
        df = df[df["stock_id"].astype(str).str.match(r"^[0-9]{4}[A-Z]?$")]
        df = df.sort_values(by="turnover", ascending=False).head(limit).reset_index(drop=True)

        print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗: {e}")
        return pd.DataFrame()

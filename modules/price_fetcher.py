import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import StringIO

def fetch_price_data(min_turnover=50000000, limit=450):
    print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=html&date=&type=ALL"
    try:
        res = requests.get(url, timeout=10)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # 嘗試找出第一張有成交金額的表格（只跑一次）
        tables = soup.find_all("table")
        found_df = None

        for table in tables:
            try:
                df_try = pd.read_html(StringIO(str(table)), flavor="bs4")[0]
                df_try.columns = df_try.columns.str.replace(r"\s", "", regex=True)

                if ("證券代號" in df_try.columns or "代號" in df_try.columns) and \
                   ("成交金額(千元)" in df_try.columns or "成交金額" in df_try.columns):
                    found_df = df_try
                    break
            except Exception:
                continue

        if found_df is None:
            print("[price_fetcher] ❌ 找不到包含成交金額的表格")
            return pd.DataFrame()

        # 欄位統一命名
        df = found_df.rename(columns={
            "證券代號": "stock_id", "代號": "stock_id",
            "證券名稱": "stock_name", "名稱": "stock_name",
            "成交金額(千元)": "turnover", "成交金額": "turnover"
        })

        df = df[["stock_id", "stock_name", "turnover"]].dropna()
        df["turnover"] = df["turnover"].astype(str).str.replace(",", "").astype(float) * 1000
        df = df[df["turnover"] >= min_turnover]

        # 僅保留有效股票代碼（純數字或 ETF 類）
        df = df[df["stock_id"].astype(str).str.match(r"^[0-9]{4}$|^00[0-9]{2}$|^006[0-9]{2}[LRU]?$")]
        df = df.sort_values(by="turnover", ascending=False).head(limit).reset_index(drop=True)

        print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗: {e}")
        return pd.DataFrame()

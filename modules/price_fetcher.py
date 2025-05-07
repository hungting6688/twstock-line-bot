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

        tables = soup.find_all("table")
        found_df = None

        for idx, table in enumerate(tables):
            try:
                df_try = pd.read_html(StringIO(str(table)), flavor="bs4")[0]
                df_try.columns = df_try.columns.str.replace(r"\s", "", regex=True)

                # debug: 印出欄位名稱
                print(f"[price_fetcher] 表格 {idx+1} 欄位：{list(df_try.columns)}")

                if ("證券代號" in df_try.columns or "代號" in df_try.columns) and \
                   ("成交金額(千元)" in df_try.columns or "成交金額" in df_try.columns):
                    found_df = df_try
                    break
            except Exception as e:
                continue

        if found_df is None:
            print("[price_fetcher] ❌ 找不到包含成交金額的表格（請參考上方欄位列表）")
            return pd.DataFrame()

        # 統一欄位命名
        df = found_df.rename(columns={
            "證券代號": "stock_id", "代號": "stock_id",
            "證券名稱": "stock_name", "名稱": "stock_name",
            "成交金額(千元)": "turnover", "成交金額": "turnover"
        })

        df = df[["stock_id", "stock_name", "turnover"]].dropna()
        df["turnover"] = df["turnover"].astype(str).str.replace(",", "").astype(float) * 1000
        df = df[df["turnover"] >= min_turnover]

        df = df[df["stock_id"].astype(str).str.match(r"^[0-9]{4}$|^00[0-9]{2}$|^006[0-9]{2}[LRU]?$")]
        df = df.sort_values(by="turnover", ascending=False).head(limit).reset_index(drop=True)

        print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗: {e}")
        return pd.DataFrame()

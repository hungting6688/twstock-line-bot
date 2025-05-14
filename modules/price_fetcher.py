print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import requests
import pandas as pd
from io import StringIO
from datetime import datetime

def fetch_price_data(limit=100, exclude_etf=True):
    print("[price_fetcher] ⏳ 擷取台股熱門股清單（來自 TWSE CSV）...")
    try:
        url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={}&type=ALL"
        date_str = datetime.today().strftime("%Y%m%d")
        full_url = url.format(date_str)
        response = requests.get(full_url, timeout=10)
        raw_text = response.text

        # 清理 CSV 資料：去除開頭非資料行
        lines = raw_text.splitlines()
        data_lines = [line for line in lines if line.count(",") > 10]
        clean_csv = "\n".join(data_lines)

        df = pd.read_csv(StringIO(clean_csv))
        df = df.rename(columns=lambda x: x.strip())

        df = df.rename(columns={"證券代號": "stock_id", "證券名稱": "name", "成交金額": "成交金額"})
        df = df[["stock_id", "name", "成交金額"]].copy()

        # 去除千分位與非數字
        df["成交金額"] = pd.to_numeric(df["成交金額"].astype(str).str.replace(",", "", regex=False), errors='coerce')
        df = df.dropna(subset=["成交金額"])

        # 排除 ETF 與下市股票
        if exclude_etf:
            df = df[~df["stock_id"].astype(str).str.startswith("00")]  # 粗略排除部分 ETF 以避免錯誤
            df = df[~df["name"].astype(str).str.contains("ETF|基金|永續|債", na=False)]

        df = df.sort_values("成交金額", ascending=False).head(limit)
        df.reset_index(drop=True, inplace=True)

        print(f"[price_fetcher] ✅ 成功擷取 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return []

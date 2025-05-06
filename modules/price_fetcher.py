# modules/price_fetcher.py

import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_price_data(min_turnover=50000000):
    print("[price_fetcher] 載入當日股價與成交金額...")

    today = datetime.today().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=html&date={today}&type=ALL"

    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.find_all("table")

        if not tables:
            raise ValueError("無法擷取表格，網站可能變更格式")

        # 通常第 9 或 10 個表格是上市股票交易資訊（包含成交金額）
        df = None
        for table in tables:
            df_try = pd.read_html(str(table), flavor="bs4")[0]
            if "證券代號" in df_try.columns and "成交金額(元)" in df_try.columns:
                df = df_try
                break

        if df is None:
            raise ValueError("找不到包含成交金額的表格")

        df = df.rename(columns=lambda x: str(x).strip())
        df = df.rename(columns={"證券代號": "stock_id", "證券名稱": "stock_name", "成交金額(元)": "turnover"})

        df['stock_id'] = df['stock_id'].astype(str).str.replace('="', '').str.replace('"', '').str.strip()
        df['turnover'] = pd.to_numeric(df['turnover'].astype(str).str.replace(",", ""), errors="coerce")

        df = df[df['turnover'] >= min_turnover].copy()
        df = df[['stock_id', 'stock_name', 'turnover']].dropna()

        print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗: {e}")
        return pd.DataFrame(columns=['stock_id', 'stock_name', 'turnover'])

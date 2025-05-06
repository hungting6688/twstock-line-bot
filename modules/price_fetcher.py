# modules/price_fetcher.py

import requests
import pandas as pd
from io import StringIO
from datetime import datetime

def fetch_price_data(min_turnover=50000000):
    print("[price_fetcher] 載入當日股價與成交金額...")

    today = datetime.today().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={today}&type=ALL"

    try:
        response = requests.get(url, timeout=10)
        lines = response.text.splitlines()

        valid_lines = [line for line in lines if line.count(',') > 10]
        csv_text = "\n".join(valid_lines)

        df = pd.read_csv(StringIO(csv_text))

        df = df.rename(columns=lambda x: x.strip())
        df = df.rename(columns={"證券代號": "stock_id", "證券名稱": "stock_name", "成交金額(元)": "turnover"})

        df['stock_id'] = df['stock_id'].astype(str).str.replace('="', '').str.replace('"', '').str.strip()
        df['turnover'] = pd.to_numeric(df['turnover'].astype(str).str.replace(",", ""), errors="coerce")

        df = df[df['turnover'] >= min_turnover].copy()
        df = df[['stock_id', 'stock_name', 'turnover']].dropna()

        print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 下載或解析失敗: {e}")
        return pd.DataFrame(columns=['stock_id', 'stock_name', 'turnover'])

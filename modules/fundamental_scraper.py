# modules/fundamental_scraper.py

import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from io import StringIO
import re

def fetch_fundamental_data():
    print("[fundamental_scraper] 擷取法人買賣超資料...")

    date_str = datetime.now().strftime('%Y%m%d')
    url = f"https://www.twse.com.tw/fund/BFI82U?response=html&dayDate={date_str}&type=day"

    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.find_all("table")

        if not tables:
            raise ValueError("找不到表格，可能網站格式變更")

        df = None
        for table in tables:
            try:
                df_try = pd.read_html(StringIO(str(table)), flavor="bs4")[0]
                if "證券代號" in df_try.columns and "外陸資買賣超股數(不含外資自營商)" in df_try.columns:
                    df = df_try
                    break
            except:
                continue

        if df is None:
            raise ValueError("無法擷取法人買賣超主表格")

        df = df.rename(columns=lambda x: str(x).strip())
        df = df.rename(columns={
            "證券代號": "stock_id",
            "外陸資買賣超股數(不含外資自營商)": "foreign",
            "投信買賣超股數": "investment",
            "自營商買賣超股數(自行買賣)": "dealer"
        })

        df['stock_id'] = df['stock_id'].astype(str).str.replace('="', '').str.replace('"', '').str.strip()
        df = df[df['stock_id'].apply(lambda x: re.fullmatch(r'[0-9A-Z]+', x) is not None)]

        for col in ['foreign', 'investment', 'dealer']:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')

        df['buy_total'] = df[['foreign', 'investment', 'dealer']].sum(axis=1)
        df = df[['stock_id', 'buy_total']].dropna()

        print(f"[fundamental_scraper] ✅ 擷取完成，共 {len(df)} 檔")
        return df

    except Exception as e:
        print(f"[fundamental_scraper] ❌ 擷取失敗: {e}")
        return pd.DataFrame(columns=['stock_id', 'buy_total'])

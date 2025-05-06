# modules/fundamental_scraper.py

import requests
import pandas as pd
from io import StringIO
from datetime import datetime

def fetch_fundamental_data():
    print("[fundamental_scraper] 擷取法人買賣超資料...")

    date_str = datetime.now().strftime('%Y%m%d')
    url = f"https://www.twse.com.tw/fund/BFI82U?response=csv&dayDate={date_str}&type=day"

    try:
        response = requests.get(url, timeout=10)
        if not response.text or 'html' in response.text.lower():
            raise ValueError("回傳內容異常，可能是網站錯誤或格式變更")

        raw_text = response.text
        lines = [line for line in raw_text.split('\n') if line.count('",') >= 10]
        cleaned_csv = '\n'.join(lines)
        df = pd.read_csv(StringIO(cleaned_csv))
        df = df.rename(columns=lambda x: x.strip().replace('\r', '').replace('\n', ''))

        required_columns = [
            '證券代號',
            '外陸資買賣超股數(不含外資自營商)',
            '投信買賣超股數',
            '自營商買賣超股數(自行買賣)'
        ]

        if not all(col in df.columns for col in required_columns):
            raise ValueError("找不到法人資料欄位")

        df = df[required_columns]
        df.columns = ['stock_id', 'foreign', 'investment', 'dealer']

        for col in ['foreign', 'investment', 'dealer']:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')

        df['buy_total'] = df[['foreign', 'investment', 'dealer']].sum(axis=1)
        df['stock_id'] = df['stock_id'].astype(str).str.replace('="', '').str.replace('"', '').str.strip()

        result = df[['stock_id', 'buy_total']]
        print(f"[fundamental_scraper] ✅ 擷取完成，共 {len(result)} 檔")
        return result

    except Exception as e:
        print(f"[fundamental_scraper] ❌ 擷取失敗: {e}")
        return pd.DataFrame(columns=['stock_id', 'buy_total'])

# modules/fundamental_scraper.py

import requests
import pandas as pd
from io import StringIO
from datetime import datetime
import re

def fetch_fundamental_data():
    print("[fundamental_scraper] 擷取法人買賣超資料...")

    date_str = datetime.now().strftime('%Y%m%d')
    url = f"https://www.twse.com.tw/fund/BFI82U?response=csv&dayDate={date_str}&type=day"

    try:
        response = requests.get(url, timeout=10)
        if not response.text or '<html' in response.text.lower():
            raise ValueError("回傳內容為 HTML 或空白，可能網站異常")

        # 過濾欄位數多的行（合法 CSV 行）
        lines = [line for line in response.text.split('\n') if line.count('",') > 10]
        if not lines:
            raise ValueError("回傳內容格式錯誤，無合法資料行")

        cleaned_csv = "\n".join(lines)
        df = pd.read_csv(StringIO(cleaned_csv))

        df = df.rename(columns=lambda x: x.strip().replace('\r', '').replace('\n', ''))

        required_cols = [
            '證券代號',
            '外陸資買賣超股數(不含外資自營商)',
            '投信買賣超股數',
            '自營商買賣超股數(自行買賣)'
        ]
        if not all(col in df.columns for col in required_cols):
            raise ValueError("找不到必要欄位，欄位名稱可能已變")

        df = df[required_cols]
        df.columns = ['stock_id', 'foreign', 'investment', 'dealer']

        # 清理 stock_id，保留數字 + 大寫字母（含 ETF 代碼）
        df['stock_id'] = df['stock_id'].astype(str).str.replace('="', '').str.replace('"', '').str.strip()
        df = df[df['stock_id'].apply(lambda x: re.fullmatch(r'[0-9A-Z]+', x) is not None)]

        # 整理數據欄位
        for col in ['foreign', 'investment', 'dealer']:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')

        df['buy_total'] = df[['foreign', 'investment', 'dealer']].sum(axis=1)
        df = df[['stock_id', 'buy_total']].dropna()

        print(f"[fundamental_scraper] ✅ 擷取完成，共 {len(df)} 檔")
        return df

    except Exception as e:
        print(f"[fundamental_scraper] ❌ 擷取失敗: {e}")
        return pd.DataFrame(columns=['stock_id', 'buy_total'])

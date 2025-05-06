# fundamental_scraper.py
import requests
import pandas as pd
from io import StringIO
from datetime import datetime

def fetch_fundamental_data():
    print("[fundamental_scraper] 擷取法人買賣超資料...")

    date_str = datetime.now().strftime('%Y%m%d')
    url = f"https://www.twse.com.tw/fund/BFI82U?response=csv&dayDate={date_str}&type=day"

    try:
        response = requests.get(url)
        response.encoding = 'utf-8'
        raw_text = response.text

        # 清除空行與非資料列
        lines = [line for line in raw_text.split('\n') if line.count('",') >= 10]
        cleaned_csv = '\n'.join(lines)
        df = pd.read_csv(StringIO(cleaned_csv))
        df = df.rename(columns=lambda x: x.strip().replace('\r', '').replace('\n', ''))

        # 原始欄位名稱（繁中）
        required_raw_columns = [
            '證券代號',
            '外陸資買賣超股數(不含外資自營商)',
            '投信買賣超股數',
            '自營商買賣超股數(自行買賣)'
        ]

        if not all(col in df.columns for col in required_raw_columns):
            raise ValueError("找不到法人資料的對應欄位")

        # 重新命名並取出需要欄位
        df = df[required_raw_columns]
        df.columns = ['stock_id', 'foreign', 'investment', 'dealer']

        # 清理數值欄位
        for col in ['foreign', 'investment', 'dealer']:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.strip(), errors='coerce')

        df['buy_total'] = df[['foreign', 'investment', 'dealer']].sum(axis=1)
        df['stock_id'] = df['stock_id'].astype(str).str.zfill(4)

        result = df[['stock_id', 'buy_total']]
        print(f"[fundamental_scraper] 擷取完成，共 {len(result)} 檔")
        return result

    except Exception as e:
        print(f"[fundamental_scraper] 擷取失敗: {e}")
        return pd.DataFrame(columns=['stock_id', 'buy_total'])

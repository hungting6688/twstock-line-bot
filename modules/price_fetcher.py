# price_fetcher.py
import requests
import pandas as pd
from io import StringIO
from datetime import datetime

def fetch_price_data(min_turnover=50000000):
    print("[price_fetcher] 載入當日股價與成交金額...")

    today = datetime.now().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={today}&type=ALL"
    response = requests.get(url)
    content = response.text

    # 清洗 CSV 格式資料
    lines = [line for line in content.split("\n") if len(line.split('",')) > 10]
    cleaned_csv = "\n".join(lines)
    df = pd.read_csv(StringIO(cleaned_csv))
    df = df.rename(columns=lambda x: x.strip().replace('\r', '').replace('\n', ''))

    df = df[['證券代號', '證券名稱', '收盤價', '成交金額']]
    df.columns = ['stock_id', 'stock_name', 'close', 'turnover']
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df['turnover'] = df['turnover'].astype(str).str.replace(',', '')
    df['turnover'] = pd.to_numeric(df['turnover'], errors='coerce')

    df = df.dropna(subset=['close', 'turnover'])
    df = df[df['turnover'] >= min_turnover]
    df['stock_id'] = df['stock_id'].astype(str).str.zfill(4)
    
    print(f"[price_fetcher] 共取得 {len(df)} 檔熱門股")
    return df.reset_index(drop=True)
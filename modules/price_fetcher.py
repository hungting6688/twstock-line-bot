# modules/price_fetcher.py

import pandas as pd
import requests
from io import StringIO
from datetime import datetime
from modules.eps_dividend_scraper import fetch_eps_dividend_data as fetch_eps_and_dividend  # ✅ 別名處理

def fetch_price_data(min_turnover=5000, limit=100, mode="opening", strategy=None):
    print("[price_fetcher] ✅ 使用 TWSE CSV 報表穩定解析版本")

    today = datetime.today().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={today}&type=ALLBUT0999"

    try:
        resp = requests.get(url, timeout=10)
        csv_raw = resp.text

        # 清理資料：保留逗號數量足夠的行
        lines = csv_raw.splitlines()
        cleaned_lines = [line for line in lines if line.count(",") > 10 and "證券代號" in line or line[0:4].isdigit()]
        cleaned_csv = "\n".join(cleaned_lines)

        df = pd.read_csv(StringIO(cleaned_csv))

        print(f"[price_fetcher] 欄位名稱： {list(df.columns)}")

        # 清理欄位名稱
        df.columns = df.columns.str.strip()

        # 移除非數字代號與 ETF
        df = df[df["證券代號"].astype(str).str.isnumeric()]
        df = df[~df["證券名稱"].str.contains("ETF|受益憑證|指數股票型")]

        # 新增欄位 stock_id 與成交金額（純數字）
        df["stock_id"] = df["證券代號"].astype(str)
        df["stock_name"] = df["證券名稱"].astype(str)
        df["成交金額"] = df["成交金額"].replace(",", "", regex=True).astype(float)
        df["turnover"] = df["成交金額"] / 1e6  # 單位轉成百萬

        print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")
        print("[price_fetcher] 前幾筆熱門股：")
        print(df[["stock_id", "stock_name", "turnover"]].head())

        # 篩選成交金額大於門檻的熱門股，並排序
        df = df[df["turnover"] >= min_turnover].sort_values(by="turnover", ascending=False)

        return df.head(limit).reset_index(drop=True)

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame(columns=["stock_id", "stock_name", "turnover"])

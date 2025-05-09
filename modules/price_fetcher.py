# modules/price_fetcher.py

import pandas as pd
import requests
from io import StringIO
from datetime import datetime

def fetch_price_data(min_turnover=50000000, limit=100):
    print("[price_fetcher] ✅ 使用 TWSE CSV 報表穩定解析版本")

    today_str = datetime.today().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={today_str}&type=ALL"

    try:
        res = requests.get(url, timeout=10)
        res.encoding = "big5"

        lines = res.text.splitlines()
        start_index = -1

        for i, line in enumerate(lines):
            if "證券代號" in line and "成交金額" in line:
                start_index = i
                break

        if start_index == -1:
            raise ValueError("找不到包含成交金額的表格（請參考上方欄位列表）")

        data_lines = []
        for line in lines[start_index:]:
            if line.strip() == "" or "備註" in line:
                break
            data_lines.append(line)

        csv_text = "\n".join(data_lines)
        df = pd.read_csv(StringIO(csv_text))
        df.columns = df.columns.str.replace(r"\s", "", regex=True)

        turnover_col = next((col for col in df.columns if "成交金額" in col), None)
        close_col = next((col for col in df.columns if "收盤價" in col), None)

        if not turnover_col or not close_col:
            raise ValueError("找不到成交金額或收盤價欄位")

        df = df.rename(columns={
            "證券代號": "stock_id",
            "證券名稱": "stock_name",
            turnover_col: "turnover",
            close_col: "close"
        })

        df = df[["stock_id", "stock_name", "turnover", "close"]].dropna()
        df = df[~df["turnover"].astype(str).str.contains("--")]
        df = df[~df["close"].astype(str).str.contains("--")]

        df["turnover"] = df["turnover"].astype(str).str.replace(",", "").astype(float) * 1000
        df["close"] = df["close"].astype(str).str.replace(",", "").astype(float)

        df = df[df["turnover"] >= min_turnover]
        df = df[df["stock_id"].astype(str).str.match(r"^[0-9]{4}[A-Z]?$")]

        df = df.sort_values(by="turnover", ascending=False).head(limit).reset_index(drop=True)
        print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗: {e}")
        return pd.DataFrame()

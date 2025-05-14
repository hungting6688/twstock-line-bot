print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import pandas as pd
import requests
from io import StringIO
import re

def fetch_price_data(limit=100):
    print("[price_fetcher] ⏳ 擷取台股熱門股清單（前 100 檔，來自 TWSE CSV）...")
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"

    try:
        response = requests.get(url, timeout=10)
        response.encoding = "big5"
        raw_text = response.text

        # 擷取表格資料（從證券代號開頭）
        lines = raw_text.split("\n")
        content_lines = []
        start = False

        for line in lines:
            if re.match(r'^\d{4}', line):  # 以 4 碼數字開頭的股票代號
                start = True
                content_lines.append(line)
            elif start and line.count(",") >= 10:
                content_lines.append(line)
            elif start and line.strip() == "":
                break  # 到空行停止

        if not content_lines:
            raise ValueError("無法從回傳內容中擷取有效表格（content_lines 為空）")

        cleaned_csv = "\n".join(content_lines)
        df = pd.read_csv(StringIO(cleaned_csv), header=None)

        # 使用明確欄位索引定位
        df = df[[0, 1, 4]]  # 0: 證券代號, 1: 證券名稱, 4: 成交金額
        df.columns = ["stock_id", "name", "成交金額"]

        df["成交金額"] = pd.to_numeric(df["成交金額"].astype(str).str.replace(",", ""), errors="coerce")
        df = df.dropna(subset=["成交金額"])
        df = df.sort_values("成交金額", ascending=False).head(limit)
        df.reset_index(drop=True, inplace=True)

        print(f"[price_fetcher] ✅ 成功取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()

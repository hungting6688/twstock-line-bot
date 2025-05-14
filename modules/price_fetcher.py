print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import pandas as pd
import requests
from io import StringIO
import re

def fetch_price_data():
    print("[price_fetcher] ⏳ 擷取台股熱門股清單（來自 TWSE CSV）...")
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"

    try:
        response = requests.get(url, timeout=10)
        response.encoding = "big5"
        raw_text = response.text

        lines = raw_text.split("\n")
        content_lines = []
        for line in lines:
            # 跳過指數類或非股票資料
            if re.match(r'^\d{4}', line) and line.count(',') >= 10:
                fields = line.split(',')
                if len(fields) < 10:
                    continue
                stock_id = fields[0].strip().replace('"', '')
                if stock_id.startswith(('00', '01')) or not stock_id.isdigit():  # 00~01多為ETF或指數
                    continue
                content_lines.append(line)

        if not content_lines:
            raise ValueError("無法從回傳內容中擷取有效表格（content_lines 為空）")

        cleaned_csv = "\n".join(content_lines)
        df = pd.read_csv(StringIO(cleaned_csv), header=None)
        df.columns = ["證券代號", "證券名稱", "成交股數", "成交筆數", "成交金額"] + list(df.columns[5:])

        df["成交金額"] = df["成交金額"].replace(",", "", regex=True)
        df = df[pd.to_numeric(df["成交金額"], errors="coerce").notnull()]
        df["成交金額"] = df["成交金額"].astype(float)

        df = df.sort_values("成交金額", ascending=False)
        df = df[["證券代號", "證券名稱", "成交金額"]].copy()
        df.columns = ["stock_id", "name", "成交金額"]
        df.reset_index(drop=True, inplace=True)

        print(f"[price_fetcher] ✅ 成功取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()
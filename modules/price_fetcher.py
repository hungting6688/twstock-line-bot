print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import pandas as pd
import requests
from io import StringIO
import re

def fetch_price_data(limit=100):
    print("[price_fetcher] ⏳ 擷取台股熱門股清單（來自 TWSE CSV）...")
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"

    try:
        response = requests.get(url, timeout=10)
        response.encoding = "big5"
        raw_text = response.text

        # 找到開始於「證券代號」表格區段之後的內容
        lines = raw_text.split("\n")
        start = False
        content_lines = []

        for line in lines:
            if "證券代號" in line and "證券名稱" in line and "成交金額" in line:
                start = True
                content_lines.append(line)
                continue
            if start:
                if re.match(r'^\d{4}', line):
                    content_lines.append(line)
                else:
                    break  # 一旦不是股票代碼行，就結束擷取

        if not content_lines or len(content_lines) <= 1:
            raise ValueError("無法從回傳內容中擷取有效表格（content_lines 為空）")

        df = pd.read_csv(StringIO("\n".join(content_lines)))
        df.columns = df.columns.str.strip()
        print(f"[price_fetcher] ✅ 原始欄位：{df.columns.tolist()}")

        df = df[["證券代號", "證券名稱", "成交金額"]].copy()
        df.columns = ["stock_id", "name", "成交金額"]
        df["成交金額"] = df["成交金額"].replace(",", "", regex=True).astype(float)
        df = df.sort_values("成交金額", ascending=False).head(limit)
        df.reset_index(drop=True, inplace=True)

        print(f"[price_fetcher] ✅ 成功取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()

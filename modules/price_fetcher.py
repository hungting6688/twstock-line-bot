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

        # 找出正確資料區段（含「證券代號」開頭）
        lines = raw_text.split("\n")
        content_lines = []
        capture = False
        for line in lines:
            if "證券代號" in line and "證券名稱" in line:
                capture = True
                content_lines.append(line)
                continue
            if capture:
                if re.match(r'^\d{4}', line):  # 股票代號為四碼數字
                    content_lines.append(line)
                else:
                    break  # 表格區塊結束

        if not content_lines or len(content_lines) < 2:
            raise ValueError("無法從回傳內容中擷取有效表格（content_lines 為空）")

        cleaned_csv = "\n".join(content_lines)
        df = pd.read_csv(StringIO(cleaned_csv))
        df.columns = df.columns.str.strip()
        print(f"[price_fetcher] ✅ 擷取欄位名稱：{df.columns.tolist()}")

        # 保留必要欄位
        df = df[["證券代號", "證券名稱", "成交金額"]].copy()
        df.columns = ["stock_id", "name", "成交金額"]

        # 過濾非數值成交金額
        df = df[df["成交金額"].astype(str).str.replace(",", "").str.strip().str.match(r'^\d+(\.\d+)?$')]
        df["成交金額"] = df["成交金額"].replace(",", "", regex=True).astype(float)

        df = df.sort_values("成交金額", ascending=False).head(limit)
        df.reset_index(drop=True, inplace=True)

        print(f"[price_fetcher] ✅ 成功取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()

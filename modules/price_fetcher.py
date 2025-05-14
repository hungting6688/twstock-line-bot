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

        lines = raw_text.split("\n")
        content_lines = []
        start_capture = False

        for line in lines:
            # 開始擷取的條件是含「證券代號」且下一行開頭是 4 碼數字（股票代碼）
            if not start_capture and "證券代號" in line and "證券名稱" in line:
                start_capture = True
                content_lines.append(line)
                continue
            if start_capture:
                if re.match(r'^"\d{4}"', line):  # 股票代碼開頭
                    content_lines.append(line)
                else:
                    break  # 一旦非股票資料，就停止擷取

        if not content_lines or len(content_lines) < 2:
            raise ValueError("無法從回傳內容中擷取有效表格（content_lines 為空）")

        cleaned_csv = "\n".join(content_lines)
        df = pd.read_csv(StringIO(cleaned_csv))
        df.columns = df.columns.str.strip()

        # 自動對應欄位名稱
        col_id = next((c for c in df.columns if "證券代號" in c), None)
        col_name = next((c for c in df.columns if "證券名稱" in c), None)
        col_value = next((c for c in df.columns if "成交金額" in c), None)

        if not all([col_id, col_name, col_value]):
            raise ValueError(f"缺少必要欄位，實際欄位為：{df.columns.tolist()}")

        df = df[[col_id, col_name, col_value]].copy()
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
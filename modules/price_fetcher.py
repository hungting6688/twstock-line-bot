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

        # 加入 DEBUG 協助判斷資料行
        print("[price_fetcher] 🧐 DEBUG：顯示前 50 行 TWSE 原始資料")
        for i, line in enumerate(raw_text.splitlines()[:50]):
            print(f"{i+1:02d}: {line}")

        # 主表格開始條件：包含「證券代號」「證券名稱」且下一行以數字開頭
        lines = raw_text.split("\n")
        content_lines = []
        found_header = False

        for i, line in enumerate(lines):
            if not found_header:
                if "證券代號" in line and "證券名稱" in line:
                    found_header = True
                    content_lines.append(line)
            else:
                # 資料行必須開頭是數字（股票代號）
                if re.match(r'^\d{4}', line):
                    content_lines.append(line)
                else:
                    break  # 遇到非股票資料行代表表格結束

        if not content_lines or len(content_lines) < 2:
            raise ValueError("無法從回傳內容中擷取有效表格（content_lines 為空）")

        cleaned_csv = "\n".join(content_lines)
        df = pd.read_csv(StringIO(cleaned_csv))
        df.columns = df.columns.str.strip()
        print(f"[price_fetcher] ✅ 擷取欄位名稱：{df.columns.tolist()}")

        # 嘗試匹配關鍵欄位
        col_id = next((col for col in df.columns if "證券代號" in col), None)
        col_name = next((col for col in df.columns if "證券名稱" in col), None)
        col_value = next((col for col in df.columns if "成交金額" in col), None)

        if not all([col_id, col_name, col_value]):
            raise ValueError(f"欄位錯誤：找不到 證券代號/名稱/成交金額，實際欄位為 {df.columns.tolist()}")

        df = df[[col_id, col_name, col_value]].copy()
        df.columns = ["stock_id", "name", "成交金額"]

        # 處理數值轉換錯誤，跳過無法轉 float 的行
        df["成交金額"] = pd.to_numeric(df["成交金額"].astype(str).str.replace(",", ""), errors="coerce")
        df = df.dropna(subset=["成交金額"])
        df = df.sort_values("成交金額", ascending=False).head(limit)
        df.reset_index(drop=True, inplace=True)

        print(f"[price_fetcher] ✅ 成功取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()

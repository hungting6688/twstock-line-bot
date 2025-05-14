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

        # 只擷取表格區塊：從開頭包含數字代碼（四碼）直到表格結尾（含逗號數量判斷）
        lines = raw_text.split("\n")
        content_lines = []
        for line in lines:
            if re.match(r'^\d{4}', line) and line.count(',') >= 10:
                content_lines.append(line)

        if not content_lines:
            raise ValueError("無法從回傳內容中擷取有效表格（content_lines 為空）")

        cleaned_csv = "\n".join(content_lines)
        df = pd.read_csv(StringIO(cleaned_csv))
        df.columns = df.columns.str.strip()
        print(f"[price_fetcher] 取得欄位名稱：{df.columns.tolist()}")

        # 嘗試辨識可能的欄位名稱變體
        candidate_map = {
            "證券代號": ["證券代號", "代號"],
            "證券名稱": ["證券名稱", "名稱"],
            "成交金額": ["成交金額", "成交金額(元)"]
        }

        final_cols = {}
        for key, variants in candidate_map.items():
            for var in variants:
                if var in df.columns:
                    final_cols[key] = var
                    break
            else:
                raise ValueError(f"缺少欄位：{key}，實際欄位：{df.columns.tolist()}")

        df = df[[final_cols["證券代號"], final_cols["證券名稱"], final_cols["成交金額"]]].copy()
        df.columns = ["stock_id", "name", "成交金額"]

        df["成交金額"] = df["成交金額"].replace(",", "", regex=True).astype(float)
        df = df.sort_values("成交金額", ascending=False).head(limit)
        df.reset_index(drop=True, inplace=True)

        print(f"[price_fetcher] ✅ 成功取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()

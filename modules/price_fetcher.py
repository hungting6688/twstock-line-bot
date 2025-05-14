print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import pandas as pd
import requests
from io import StringIO
import re

def fetch_price_data(limit=None, mode="opening"):
    print("[price_fetcher] ⏳ 擷取台股熱門股清單（來自 TWSE CSV）...")
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"

    # 根據分析模式自動設定 limit
    mode_limits = {
        "opening": 100,
        "intraday": 80,
        "dividend": 60,
        "closing": 300,
    }
    final_limit = limit or mode_limits.get(mode, 100)

    try:
        response = requests.get(url, timeout=10)
        response.encoding = "big5"
        raw_text = response.text

        # 擷取有效股票資料行（開頭為 4 碼數字，且含逗號數 >10）
        lines = raw_text.split("\n")
        content_lines = []
        for line in lines:
            if re.match(r'^"\\d{4}"', line) and line.count(",") > 10:
                content_lines.append(line)

        if not content_lines:
            raise ValueError("無法從回傳內容中擷取有效表格（content_lines 為空）")

        cleaned_csv = "\n".join(content_lines)
        df = pd.read_csv(StringIO(cleaned_csv), header=None)

        df.columns = [
            "證券代號", "證券名稱", "成交股數", "成交金額", "成交筆數",
            "開盤價", "最高價", "最低價", "收盤價", "漲跌(+/-)",
            "漲跌價差", "最後揭示買價", "最後揭示買量", "最後揭示賣價",
            "最後揭示賣量", "本益比"
        ]

        df = df[["證券代號", "證券名稱", "成交金額"]].copy()
        df.columns = ["stock_id", "name", "成交金額"]

        df["成交金額"] = df["成交金額"].replace(",", "", regex=True)
        df = df[pd.to_numeric(df["成交金額"], errors="coerce").notna()]  # 移除不能轉換為數字的資料（如指數）
        df["成交金額"] = df["成交金額"].astype(float)

        df = df.sort_values("成交金額", ascending=False).head(final_limit)
        df.reset_index(drop=True, inplace=True)

        print(f"[price_fetcher] ✅ 成功取得 {len(df)} 檔熱門股（模式：{mode}，limit={final_limit}）")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()

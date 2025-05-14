print("[price_fetcher] ✅ 已載入最新版 (real-time 熱門股)")

import pandas as pd
import requests
from io import StringIO
import re

def fetch_price_data(limit=100):
    print(f"[price_fetcher] ⏳ 擷取台股熱門股清單（前 {limit} 檔，來自 TWSE CSV）...")
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=&type=ALL"

    try:
        response = requests.get(url, timeout=10)
        response.encoding = "big5"
        raw_text = response.text

        lines = raw_text.split("\n")
        content_lines = []
        for line in lines:
            if re.match(r'^"\d{4}"', line) and line.count(",") >= 10:
                content_lines.append(line)

        if not content_lines:
            raise ValueError("無法從回傳內容中擷取有效表格（content_lines 為空）")

        cleaned_csv = "\n".join(content_lines)
        df = pd.read_csv(StringIO(cleaned_csv), header=None)

        # 嘗試定位欄位順序
        df.columns = [
            "證券代號", "證券名稱", "_1", "_2", "_3", "_4", "_5", "_6",
            "成交金額", "_8", "_9", "_10", "_11", "_12", "_13", "_14"
        ][:df.shape[1]]

        df = df[["證券代號", "證券名稱", "成交金額"]].copy()
        df["成交金額"] = pd.to_numeric(df["成交金額"].astype(str).str.replace(",", ""), errors="coerce")
        df.dropna(subset=["成交金額"], inplace=True)

        # 排除 ETF 與指數類股票（多半為英文名、代號非四碼或非數字）
        df = df[df["證券代號"].str.match(r'^\d{4}$')]
        df = df.sort_values("成交金額", ascending=False).head(limit)

        df = df.rename(columns={"證券代號": "stock_id", "證券名稱": "name"})
        df.reset_index(drop=True, inplace=True)

        print(f"[price_fetcher] ✅ 成功取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()
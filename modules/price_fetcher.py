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

        # 解析出真正的個股資料表格（開頭為 4 碼代號、逗號超過 10 格者）
        lines = raw_text.split("\n")
        content_lines = []
        for line in lines:
            if re.match(r'^"?\d{4}"?,', line) and line.count(",") >= 10:
                content_lines.append(line)

        if not content_lines:
            print("[price_fetcher] ❌ 擷取失敗：無法從回傳內容中擷取有效表格（content_lines 為空）")
            return pd.DataFrame()

        cleaned_csv = "\n".join(content_lines)
        df = pd.read_csv(StringIO(cleaned_csv), header=None)

        # 自動對應欄位：證券代號、名稱、成交金額
        df.columns = [f"col{i}" for i in range(df.shape[1])]
        df = df.rename(columns={
            "col0": "stock_id",
            "col1": "name",
            "col9": "成交金額"
        })

        df = df[["stock_id", "name", "成交金額"]].copy()
        df["成交金額"] = df["成交金額"].astype(str).str.replace(",", "").astype(float)
        df = df.sort_values("成交金額", ascending=False).head(limit)
        df.reset_index(drop=True, inplace=True)

        print(f"[price_fetcher] ✅ 成功取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()

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
        for line in lines:
            if re.match(r'^"?\d{4}"?,', line) and line.count(",") >= 10:
                content_lines.append(line)

        if not content_lines:
            print("[price_fetcher] ❌ 擷取失敗：無法從回傳內容中擷取有效表格（content_lines 為空）")
            return pd.DataFrame()

        cleaned_csv = "\n".join(content_lines)
        df = pd.read_csv(StringIO(cleaned_csv), header=None)

        df.columns = [f"col{i}" for i in range(df.shape[1])]
        df = df.rename(columns={
            "col0": "stock_id",
            "col1": "name",
            "col9": "成交金額"
        })

        df = df[["stock_id", "name", "成交金額"]].copy()

        # 嘗試轉換金額，無法轉換者略過（如 ETF/指數）
        cleaned_data = []
        for _, row in df.iterrows():
            try:
                amount = float(str(row["成交金額"]).replace(",", "").strip())
                stock_id = str(row["stock_id"]).strip().strip('"')
                if stock_id.isdigit():
                    cleaned_data.append({
                        "stock_id": stock_id,
                        "name": str(row["name"]).strip(),
                        "成交金額": amount
                    })
            except:
                continue

        final_df = pd.DataFrame(cleaned_data)
        final_df = final_df.sort_values("成交金額", ascending=False).head(limit)
        final_df.reset_index(drop=True, inplace=True)

        print(f"[price_fetcher] ✅ 成功取得 {len(final_df)} 檔熱門股")
        return final_df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗：{e}")
        return pd.DataFrame()

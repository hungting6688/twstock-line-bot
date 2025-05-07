import pandas as pd
import requests
from io import StringIO
from datetime import datetime

def fetch_price_data(min_turnover=50000000, limit=450):
    print("[price_fetcher] ✅ 使用 TWSE CSV 報表穩定解析版本")

    today_str = datetime.today().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={today_str}&type=ALL"

    try:
        res = requests.get(url, timeout=10)
        res.encoding = "big5"

        # 擷取含有有效表格開頭的段落
        start_index = -1
        lines = res.text.splitlines()

        # 找出表格開頭的位置（含「證券代號」與「成交金額」）
        for i, line in enumerate(lines):
            if "證券代號" in line and "成交金額" in line:
                start_index = i
                break

        if start_index == -1:
            raise ValueError("找不到包含成交金額的表格（請參考上方欄位列表）")

        # 取出有效段落直到遇到空列或下一區段
        data_lines = []
        for line in lines[start_index:]:
            if line.strip() == "" or "備註" in line:
                break
            data_lines.append(line)

        # 合併為有效 CSV 內容並讀入 pandas
        csv_text = "\n".join(data_lines)
        df = pd.read_csv(StringIO(csv_text))

        # 欄位標準化
        df.columns = df.columns.str.replace(r"\s", "", regex=True)
        df = df.rename(columns={
            "證券代號": "stock_id",
            "證券名稱": "stock_name",
            "成交金額(千元)": "turnover"
        })

        df = df[["stock_id", "stock_name", "turnover"]].dropna()
        df["turnover"] = df["turnover"].astype(str).str.replace(",", "").astype(float) * 1000
        df = df[df["turnover"] >= min_turnover]

        # 只保留台股代碼（4碼數字或含 1 個大寫英文字母）
        df = df[df["stock_id"].astype(str).str.match(r"^[0-9]{4}[A-Z]?$")]
        df = df.sort_values(by="turnover", ascending=False).head(limit).reset_index(drop=True)

        print(f"[price_fetcher] ✅ 共取得 {len(df)} 檔熱門股")
        return df

    except Exception as e:
        print(f"[price_fetcher] ❌ 擷取失敗: {e}")
        return pd.DataFrame()

import pandas as pd
import requests
from datetime import datetime, timedelta
import io

def fetch_fundamental_data():
    print("[fundamental_scraper] 擷取法人買賣超資料...")

    headers = {"User-Agent": "Mozilla/5.0"}
    max_lookback_days = 5  # 最多往前找 5 天

    for i in range(max_lookback_days):
        date = (datetime.today() - timedelta(days=i + 1)).strftime("%Y%m%d")
        print(f"[fundamental_scraper] 嘗試擷取日期：{date}")
        url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={date}&type=ALLBUT0999"

        try:
            res = requests.get(url, headers=headers, timeout=10)
            content = res.text

            # 清理 CSV
            lines = content.splitlines()
            cleaned_lines = [line for line in lines if "," in line and not line.startswith('=')]
            csv_data = "\n".join(cleaned_lines)

            df = pd.read_csv(io.StringIO(csv_data), on_bad_lines="skip")

            if "證券代號" not in df.columns:
                print(f"[fundamental_scraper] ⏩ 略過：無『證券代號』欄位")
                continue  # 試下一天

            df = df[df["證券代號"].apply(lambda x: str(x).isdigit())]
            df["stock_id"] = df["證券代號"].astype(str)

            df["buy_total"] = (
                df["外陸資買進股數(不含外資自營商)"].replace(",", "", regex=True).astype(float) -
                df["外陸資賣出股數(不含外資自營商)"].replace(",", "", regex=True).astype(float) +
                df["投信買進股數"].replace(",", "", regex=True).astype(float) -
                df["投信賣出股數"].replace(",", "", regex=True).astype(float) +
                df["自營商買進股數(自行買賣)"].replace(",", "", regex=True).astype(float) -
                df["自營商賣出股數(自行買賣)"].replace(",", "", regex=True).astype(float)
            )

            print(f"[fundamental_scraper] ✅ 擷取成功（使用資料日：{date}）")
            return df[["stock_id", "buy_total"]]

        except Exception as e:
            print(f"[fundamental_scraper] ⚠️ 擷取失敗（{date}）：{e}")

    # 若全部都抓不到
    print("[fundamental_scraper] ❌ 無法擷取最近可用法人資料，回傳空表")
    return pd.DataFrame(columns=["stock_id", "buy_total"])

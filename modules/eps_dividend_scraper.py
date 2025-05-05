import pandas as pd
import requests
from io import StringIO
from datetime import datetime

def fetch_twse_eps_dividend():
    """
    從證交所每日資料頁抓殖利率、EPS、淨值比等資訊。
    來源：https://www.twse.com.tw/zh/page/trading/exchange/BWIBBU_d.html
    """
    today = datetime.today().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/exchangeReport/BWIBBU_d?response=csv&date={today}&selectType=ALL"

    try:
        resp = requests.get(url)
        raw = resp.text
        lines = raw.splitlines()
        clean_lines = [line for line in lines if len(line.split(",")) == 15 and "--" not in line]
        csv_data = "\n".join(clean_lines)
        df = pd.read_csv(StringIO(csv_data))
        df = df.rename(columns={
            "證券代號": "stock_id",
            "殖利率(%)": "dividend_yield",
            "本益比": "pe_ratio",
            "股價淨值比": "pb_ratio",
            "EPS": "eps"
        })
        df["stock_id"] = df["stock_id"].astype(str).str.zfill(4)
        df = df[["stock_id", "dividend_yield", "eps", "pe_ratio", "pb_ratio"]]
        df = df.dropna()
        return df
    except Exception as e:
        print(f"❌ TWSE 殖利率/EPS 抓取失敗：{e}")
        return pd.DataFrame()

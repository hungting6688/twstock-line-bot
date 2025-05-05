# modules/eps_dividend_scraper.py

import requests
import pandas as pd
from datetime import datetime

def fetch_eps_dividend_data():
    url = "https://mops.twse.com.tw/mops/web/ajax_t163sb04"
    today = datetime.today()
    year = today.year - 1911
    season = (today.month - 1) // 3 + 1

    eps_data = []
    for s in range(1, season + 1):
        payload = {
            "encodeURIComponent": "1",
            "step": "1",
            "firstin": "1",
            "off": "1",
            "TYPEK": "sii",
            "year": str(year),
            "season": f"{s}"
        }
        r = requests.post(url, data=payload)
        try:
            df = pd.read_html(r.text)[1]
            df.columns = df.columns.droplevel()
            eps_data.append(df)
        except Exception:
            continue

    if not eps_data:
        return pd.DataFrame()

    combined = pd.concat(eps_data, ignore_index=True)
    combined = combined.rename(columns={
        "公司代號": "stock_id",
        "基本每股盈餘（元）": "eps"
    })
    combined["stock_id"] = combined["stock_id"].astype(str)
    combined = combined[["stock_id", "eps"]].dropna()
    combined["eps"] = pd.to_numeric(combined["eps"], errors="coerce")
    return combined

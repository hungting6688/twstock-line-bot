# modules/eps_dividend_scraper.py

import requests
import pandas as pd
import datetime

def get_latest_season():
    now = datetime.datetime.now()
    year = now.year - 1911
    month = now.month
    if month <= 3:
        season = "04"
        year -= 1
    elif month <= 6:
        season = "01"
    elif month <= 9:
        season = "02"
    else:
        season = "03"
    return str(year), season

def get_eps_data() -> dict:
    """
    從公開資訊觀測站爬取最新季度 EPS 與已公告股利資料（上市公司）
    """
    year, season = get_latest_season()

    # EPS 來源
    eps_url = "https://mops.twse.com.tw/mops/web/ajax_t05st09_1"
    eps_form = {
        "encodeURIComponent": "1",
        "step": "1",
        "firstin": "1",
        "off": "1",
        "TYPEK": "sii",
        "year": year,
        "season": season
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    eps_res = requests.post(eps_url, data=eps_form, headers=headers)
    eps_df = pd.read_html(eps_res.text)[1]
    eps_df.columns = eps_df.columns.str.strip()
    eps_df = eps_df.rename(columns={"公司代號": "stock_id", "基本每股盈餘（元）": "EPS"})
    eps_df = eps_df[["stock_id", "EPS"]].dropna()
    eps_df["EPS"] = pd.to_numeric(eps_df["EPS"], errors="coerce")
    eps_df = eps_df.dropna()

    # 股利來源
    div_url = "https://mops.twse.com.tw/mops/web/ajax_t05st34"
    div_form = {
        "encodeURIComponent": "1",
        "step": "1",
        "firstin": "1",
        "off": "1",
        "TYPEK": "sii"
    }
    div_res = requests.post(div_url, data=div_form, headers=headers)
    div_df = pd.read_html(div_res.text)[1]
    div_df.columns = div_df.columns.str.strip()
    div_df = div_df.rename(columns={"公司代號": "stock_id", "現金股利": "Dividend"})
    div_df = div_df[["stock_id", "Dividend"]].dropna()
    div_df["Dividend"] = pd.to_numeric(div_df["Dividend"], errors="coerce")
    div_df = div_df.dropna()

    # 合併
    result = {}
    for _, row in eps_df.iterrows():
        sid = str(row["stock_id"]).zfill(4)
        result[sid] = {
            "eps": round(row["EPS"], 2),
            "dividend": None
        }

    for _, row in div_df.iterrows():
        sid = str(row["stock_id"]).zfill(4)
        if sid not in result:
            result[sid] = {"eps": None, "dividend": None}
        result[sid]["dividend"] = round(row["Dividend"], 2)

    return result

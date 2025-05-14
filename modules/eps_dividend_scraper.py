print("[eps_dividend_scraper] ✅ 已載入最新版")

import requests
import pandas as pd
from io import StringIO
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

def get_eps_data():
    year, season = get_latest_season()
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        eps_res = requests.post(
            "https://mops.twse.com.tw/mops/web/ajax_t05st09_1",
            data={
                "encodeURIComponent": "1", "step": "1", "firstin": "1", "off": "1",
                "TYPEK": "sii", "year": year, "season": season
            }, headers=headers, timeout=10
        )
        eps_df = pd.read_html(StringIO(eps_res.text))[1]
        eps_df.columns = eps_df.columns.str.strip()
        eps_df = eps_df.rename(columns={"公司代號": "stock_id", "基本每股盈餘（元）": "EPS"})
        eps_df = eps_df[["stock_id", "EPS"]].dropna()
        eps_df["EPS"] = pd.to_numeric(eps_df["EPS"], errors="coerce")
        eps_df = eps_df.dropna()
    except Exception as e:
        print(f"[EPS] 查無 EPS 表格或格式錯誤：{e}")
        eps_df = pd.DataFrame(columns=["stock_id", "EPS"])

    try:
        div_res = requests.post(
            "https://mops.twse.com.tw/mops/web/ajax_t05st34",
            data={"encodeURIComponent": "1", "step": "1", "firstin": "1", "off": "1", "TYPEK": "sii"},
            headers=headers, timeout=10
        )
        div_df = pd.read_html(StringIO(div_res.text))[1]
        div_df.columns = div_df.columns.str.strip()
        div_df = div_df.rename(columns={"公司代號": "stock_id", "現金股利": "Dividend"})
        div_df = div_df[["stock_id", "Dividend"]].dropna()
        div_df["Dividend"] = pd.to_numeric(div_df["Dividend"], errors="coerce")
        div_df = div_df.dropna()
    except Exception as e:
        print(f"[Dividend] 查無股利表格或格式錯誤：{e}")
        div_df = pd.DataFrame(columns=["stock_id", "Dividend"])

    result = {}
    for _, row in eps_df.iterrows():
        sid = str(row["stock_id"]).zfill(4)
        result[sid] = {"eps": round(row["EPS"], 2), "dividend": None}

    for _, row in div_df.iterrows():
        sid = str(row["stock_id"]).zfill(4)
        if sid not in result:
            result[sid] = {"eps": None, "dividend": None}
        result[sid]["dividend"] = round(row["Dividend"], 2)

    return result

def get_dividend_data():
    all_data = get_eps_data()
    return {sid: val["dividend"] for sid, val in all_data.items() if val["dividend"] is not None}

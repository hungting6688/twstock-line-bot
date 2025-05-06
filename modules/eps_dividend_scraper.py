print("[eps_dividend_scraper] ✅ 已載入最新版 (使用 BeautifulSoup)")

import requests
import pandas as pd
from bs4 import BeautifulSoup
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

def extract_table_from_html(text, keyword):
    soup = BeautifulSoup(text, "html.parser")
    tables = soup.find_all("table")
    for table in tables:
        if keyword in str(table):
            try:
                return pd.read_html(str(table))[0]
            except:
                continue
    return pd.DataFrame()

def get_eps_data() -> dict:
    year, season = get_latest_season()
    headers = {"User-Agent": "Mozilla/5.0"}

    # EPS
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
    eps_res = requests.post(eps_url, data=eps_form, headers=headers)
    eps_df = extract_table_from_html(eps_res.text, "基本每股盈餘")
    if not eps_df.empty:
        eps_df.columns = eps_df.columns.str.strip()
        eps_df = eps_df.rename(columns={"公司代號": "stock_id", eps_df.columns[-1]: "EPS"})
        eps_df = eps_df[["stock_id", "EPS"]].dropna()
        eps_df["EPS"] = pd.to_numeric(eps_df["EPS"], errors="coerce")
    else:
        print("[EPS] 查無 EPS 表格或格式錯誤")
        eps_df = pd.DataFrame(columns=["stock_id", "EPS"])

    # Dividend
    div_url = "https://mops.twse.com.tw/mops/web/ajax_t05st34"
    div_form = {
        "encodeURIComponent": "1",
        "step": "1",
        "firstin": "1",
        "off": "1",
        "TYPEK": "sii"
    }
    div_res = requests.post(div_url, data=div_form, headers=headers)
    div_df = extract_table_from_html(div_res.text, "現金股利")
    if not div_df.empty:
        div_df.columns = div_df.columns.str.strip()
        div_df = div_df.rename(columns={"公司代號": "stock_id", "現金股利": "Dividend"})
        div_df = div_df[["stock_id", "Dividend"]].dropna()
        div_df["Dividend"] = pd.to_numeric(div_df["Dividend"], errors="coerce")
    else:
        print("[Dividend] 查無股利表格或格式錯誤")
        div_df = pd.DataFrame(columns=["stock_id", "Dividend"])

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

    print(f"[EPS] ✅ 成功匯入 EPS 資料筆數：{len(eps_df)}")
    print(f"[Dividend] ✅ 成功匯入股利資料筆數：{len(div_df)}")
    return result

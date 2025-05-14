print("[eps_dividend_scraper] ✅ 已載入最新版")

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
    year, season = get_latest_season()
    headers = {"User-Agent": "Mozilla/5.0"}

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
    eps_res = requests.post(eps_url,

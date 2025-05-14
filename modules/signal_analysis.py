print("[fundamental_scraper] ✅ 已載入最新版")

import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

def fetch_fundamental_data(stock_ids):
    result = []

    for stock_id in stock_ids:
        try:
            # 延遲避免被擋
            time.sleep(0.5)

            url = f"https://goodinfo.tw/tw/StockBzPerformance.asp?STOCK_ID={stock_id}"
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://goodinfo.tw/tw/index.asp",
            }

            r = requests.get(url, headers=headers, timeout=10)
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")

            # 三大法人買賣超（僅當日）
            chip_table = soup.select_one('table.b1.p4_2.r10.box_shadow')
            if chip_table:
                rows = chip_table.find_all("tr")
                chip_text = str(rows[-1].text) if rows else ""
                foreign_buy = parse_chip_text(chip_text, "外資")
                invest_buy = parse_chip_text(chip_text, "投信")
                dealer_buy = parse_chip_text(chip_text, "自營商")
            else:
                foreign_buy = invest_buy = dealer_buy = None

            # 財務指標
            pe_ratio = get_value_by_label(soup, "本益比")
            pb_ratio = get_value_by_label(soup, "股價淨值比")
            roe = get_value_by_label(soup, "ROE")

            result.append({
                "stock_id": stock_id,
                "foreign_buy": foreign_buy,
                "invest_buy": invest_buy,
                "dealer_buy": dealer_buy,
                "pe_ratio": pe_ratio,
                "pb_ratio": pb_ratio,
                "roe": roe
            })

        except Exception as e:
            print(f"[fundamental_scraper] ⚠️ 失敗 {stock_id}：{e}")
            continue

    return pd.DataFrame(result)


def get_value_by_label(soup, label):
    try:
        cells = soup.find_all("td")
        for i, td in enumerate(cells):
            if label in td.text:
                value_text = cells[i + 1].text.strip().replace("%", "")
                return float(value_text)
    except:
        return None


def parse_chip_text(text, keyword):
    try:
        start = text.find(keyword)
        if start == -1:
            return None
        sub = text[start:]
        number = ""
        for char in sub:
            if char in "0123456789-,":
                number += char
            elif char == "張":
                break
        return int(number.replace(",", ""))
    except:
        return None

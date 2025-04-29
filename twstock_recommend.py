import requests

def get_recommend_stocks(limit=5):
    url = "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_d"  # 使用台灣證交所公開資料作為起點
    res = requests.get(url)
    data = res.json()

    results = []
    for item in data:
        try:
            code = item["證券代號"]
            name = item["證券名稱"]
            pe = float(item["本益比"]) if item["本益比"] not in ["", "-"] else 999
            pb = float(item["股價淨值比"]) if item["股價淨值比"] not in ["", "-"] else 999
            dividend = float(item["股利殖利率"]) if item["股利殖利率"] not in ["", "-"] else 0

            # 條件範例：低本益比、高殖利率，並排除大型股
            if pe < 15 and dividend > 4 and pb < 2 and len(code) == 4 and int(code) > 2000:
                results.append({
                    "code": code,
                    "name": name,
                    "reason": f"本益比 {pe}、殖利率 {dividend}%、PB {pb}"
                })
        except:
            continue

    # 最多推薦 limit 檔
    return results[:limit]

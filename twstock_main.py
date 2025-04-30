
import requests
import time

def get_hot_stocks(limit=200):
    url = "https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX20"  # 市場熱門股成交排行
    try:
        res = requests.get(url, timeout=5)
        data = res.json()
    except:
        return []

    sorted_stocks = sorted(data, key=lambda x: int(x.get("成交金額", "0").replace(",", "") or 0), reverse=True)
    result = []
    for item in sorted_stocks[:limit]:
        code = item["證券代號"]
        if code.isdigit() and len(code) == 4:
            result.append(code)
    return result

def get_rsi(symbol):
    try:
        url = f"https://www.tej.com.tw/webtej/doc/uid/{symbol}"
        res = requests.get(url, timeout=5)
        if "RSI" in res.text:
            import re
            match = re.search(r"RSI\D+(\d{1,3}\.\d+)", res.text)
            if match:
                return float(match.group(1))
    except:
        pass
    return None

def get_tech_recommend(limit=5):
    hot_stocks = get_hot_stocks()
    results = []
    for code in hot_stocks:
        rsi = get_rsi(code)
        if rsi and rsi >= 70:
            results.append({
                "code": code,
                "rsi": rsi,
                "reason": f"RSI 達 {rsi}"
            })
        time.sleep(0.3)
        if len(results) >= limit:
            break
    return results

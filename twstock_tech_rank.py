
import requests
import pandas as pd
import datetime

def get_stock_history(code, days=15):
    url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={datetime.datetime.today().strftime('%Y%m01')}&stockNo={code}"
    try:
        res = requests.get(url)
        data = res.json()
        raw = data["data"]
        closes = [float(x[6].replace(",", "")) for x in raw][-days:]
        return closes if len(closes) >= 14 else None
    except:
        return None

def calculate_rsi(prices, period=14):
    deltas = pd.Series(prices).diff()
    gain = deltas.where(deltas > 0, 0).rolling(window=period).mean()
    loss = -deltas.where(deltas < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_tech_recommend():
    # 範例熱門股清單（可擴充成成交額前 100）
    stocks = {
        "2330": "台積電",
        "8046": "南電",
        "2603": "長榮"
    }
    results = []
    for code, name in stocks.items():
        closes = get_stock_history(code)
        if not closes:
            continue
        rsi_series = calculate_rsi(closes)
        rsi = rsi_series.iloc[-1] if rsi_series is not None else None
        if rsi is None:
            continue

        if rsi > 70:
            reason = "RSI 超過 70，短線偏熱，建議觀察追高風險"
        elif rsi < 30:
            reason = "RSI 低於 30，可能超跌反彈，建議觀察機會"
        else:
            continue

        results.append({
            "code": code,
            "name": name,
            "rsi": round(rsi, 1),
            "reason": reason
        })
    return results

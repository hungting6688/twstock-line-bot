
import requests
import pandas as pd
import datetime

def get_stock_history(code, days=30):
    url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={datetime.datetime.today().strftime('%Y%m01')}&stockNo={code}"
    try:
        res = requests.get(url)
        data = res.json()
        raw = data["data"]
        closes = [float(x[6].replace(",", "")) for x in raw][-days:]
        return closes if len(closes) >= 26 else None
    except:
        return None

def calculate_macd(prices, short=12, long=26, signal=9):
    if len(prices) < long:
        return None
    prices = pd.Series(prices)
    ema_short = prices.ewm(span=short, adjust=False).mean()
    ema_long = prices.ewm(span=long, adjust=False).mean()
    dif = ema_short - ema_long
    macd = dif.ewm(span=signal, adjust=False).mean()
    return dif, macd

def analyze_macd_signal(code, rsi_dict):
    prices = get_stock_history(code)
    if not prices:
        return None
    dif, macd = calculate_macd(prices)
    if dif is None or macd is None:
        return None

    today_dif = dif.iloc[-1]
    prev_dif = dif.iloc[-2]
    today_macd = macd.iloc[-1]
    prev_macd = macd.iloc[-2]

    signal = ""
    if prev_dif < prev_macd and today_dif > today_macd:
        signal = "黃金交叉，趨勢轉強，可小量佈局觀察"
    elif prev_dif > prev_macd and today_dif < today_macd:
        signal = "死亡交叉，走勢轉弱，建議減碼或觀望"
    else:
        return None

    # 判斷 RSI 是否同步強勢
    rsi = rsi_dict.get(code)
    if rsi and rsi > 70 and "黃金交叉" in signal:
        signal = "MACD + RSI 同步轉強，強勢突破，可小量佈局觀察"

    return {
        "code": code,
        "reason": signal
    }

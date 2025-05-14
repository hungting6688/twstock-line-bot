print("[market_sentiment] ✅ 已載入最新版")

import yfinance as yf
from datetime import datetime, timedelta

def get_market_sentiment_score():
    indices = {
        "^TWII": "台股加權",
        "^N225": "日經",
        "^HSI": "恆生",
        "^GSPC": "標普500",
        "^IXIC": "那斯達克",
    }

    today = datetime.today()
    start_date = today - timedelta(days=5)

    score = 0
    max_score = len(indices) * 2

    for symbol, name in indices.items():
        try:
            df = yf.download(symbol, start=start_date.strftime('%Y-%m-%d'), end=today.strftime('%Y-%m-%d'), progress=False)
            closes = df["Close"].dropna()
            if len(closes) < 2:
                raise ValueError("資料不足")
            last_close = float(closes.iloc[-1])
            prev_close = float(closes.iloc[-2])
            pct_change = (last_close - prev_close) / prev_close

            if pct_change > 0.01:
                score += 2
            elif pct_change > 0:
                score += 1

        except Exception as e:
            print(f"[market_sentiment] ❌ 無法讀取 {symbol}：{e}")
            continue

    normalized_score = round((score / max_score) * 10, 1)
    print(f"[market_sentiment] ✅ 市場情緒評分：{normalized_score}/10")
    return normalized_score

def get_market_sentiment_adjustments():
    score = get_market_sentiment_score()

    if score >= 8:
        return {
            "MACD": 1.2,
            "KD": 1.2,
            "RSI": 1.1,
            "MA": 1.2,
            "BB": 1.1,
            "dividend": 1.0,
            "eps": 1.0,
            "pe": 0.9,
            "roe": 0.9,
        }
    elif score >= 5:
        return {
            "MACD": 1.0,
            "KD": 1.0,
            "RSI": 1.0,
            "MA": 1.0,
            "BB": 1.0,
            "dividend": 1.0,
            "eps": 1.0,
            "pe": 1.0,
            "roe": 1.0,
        }
    else:
        return {
            "MACD": 0.8,
            "KD": 0.9,
            "RSI": 0.9,
            "MA": 0.8,
            "BB": 0.9,
            "dividend": 1.2,
            "eps": 1.2,
            "pe": 1.1,
            "roe": 1.1,
        }
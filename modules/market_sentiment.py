# market_sentiment.py
import yfinance as yf
from datetime import datetime, timedelta


def fetch_market_sentiment():
    """
    根據全球主要指數（台股、日經、港股、美股）漲跌幅與成交量
    回傳市場情緒分數（越高表示市場越偏多）
    """
    indices = {
        "^TWII": "台股加權",
        "^N225": "日經",
        "^HSI": "恆生",
        "^GSPC": "標普500",
        "^IXIC": "那斯達克",
    }

    today = datetime.today()
    yesterday = today - timedelta(days=3)

    score = 0
    max_score = len(indices) * 2

    for symbol, name in indices.items():
        try:
            df = yf.download(symbol, start=yesterday.strftime('%Y-%m-%d'), end=today.strftime('%Y-%m-%d'))
            if df.empty or len(df) < 2:
                continue

            prev = df.iloc[-2]
            curr = df.iloc[-1]

            price_change = (curr["Close"] - prev["Close"]) / prev["Close"]
            vol_change = (curr["Volume"] - prev["Volume"]) / prev["Volume"]

            if price_change > 0:
                score += 1
            if vol_change > 0:
                score += 1
        except Exception as e:
            print(f"[market_sentiment] ⚠️ 無法取得 {name}：{e}")
            continue

    sentiment_ratio = score / max_score  # 正規化為 0~1

    if sentiment_ratio >= 0.75:
        return "bullish"
    elif sentiment_ratio >= 0.4:
        return "neutral"
    else:
        return "bearish"

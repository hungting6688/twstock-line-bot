# modules/market_sentiment.py
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
    yesterday = today - timedelta(days=3)

    score = 0
    max_score = len(indices) * 2

    for symbol in indices:
        try:
            df = yf.download(symbol, start=yesterday.strftime('%Y-%m-%d'), end=today.strftime('%Y-%m-%d'))
            if df.empty or len(df) < 2:
                continue
            pct_change = (df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]
            if pct_change > 0.01:
                score += 2
            elif pct_change > 0:
                score += 1
        except Exception as e:
            print(f"[market_sentiment] ❌ 無法讀取 {symbol}：{e}")
            continue

    normalized_score = round((score / max_score) * 10, 1)  # 轉為 0~10 分數
    print(f"[market_sentiment] ✅ 市場情緒評分：{normalized_score}/10")
    return normalized_score

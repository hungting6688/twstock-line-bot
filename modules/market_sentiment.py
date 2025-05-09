import requests
from datetime import datetime

def get_market_sentiment():
    """
    擷取台股加權指數資料，回傳市場氣氛評估結果
    回傳範例：
    {
        "sentiment_score": 1,   # 1=正向, 0=中性, -1=負向
        "note": "加權指數上漲 0.85%，市場氣氛偏多"
    }
    """
    print("[market_sentiment] ⏳ 擷取台股加權指數資料...")

    try:
        today_str = datetime.today().strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/rwd/zh/TAIEX/MI_5MINS_INDEX?response=json&date={today_str}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        rows = data.get("data", [])

        if not rows or len(rows) < 2:
            print("[market_sentiment] ⚠️ 資料不足")
            return {"sentiment_score": 0, "note": "今日資料不足，視為中性"}

        # 過濾非法數值
        def safe_float(value):
            try:
                return float(value.replace(",", ""))
            except:
                return None

        first = safe_float(rows[0][1])
        last = safe_float(rows[-1][1])

        if first is None or last is None or first == 0:
            print("[market_sentiment] ⚠️ 數值轉換失敗")
            return {"sentiment_score": 0, "note": "加權指數解析錯誤，視為中性"}

        percent_change = (last - first) / first * 100

        if percent_change > 0.5:
            return {"sentiment_score": 1, "note": f"加權指數上漲 {percent_change:.2f}%，市場氣氛偏多"}
        elif percent_change < -0.5:
            return {"sentiment_score": -1, "note": f"加權指數下跌 {percent_change:.2f}%，市場氣氛偏空"}
        else:
            return {"sentiment_score": 0, "note": f"加權指數變動 {percent_change:.2f}%，市場氣氛中性"}

    except Exception as e:
        print(f"[market_sentiment] ❌ 擷取失敗：{e}")
        return {"sentiment_score": 0, "note": "擷取失敗，視為中性"}

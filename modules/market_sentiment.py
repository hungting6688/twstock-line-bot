import requests
from datetime import datetime

def fetch_market_sentiment():
    """
    擷取台股加權指數與成交量，判斷當日市場情緒（正向、中性、負向）
    """
    print("[market_sentiment] ⏳ 擷取台股指數資料...")
    try:
        today_str = datetime.today().strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/rwd/zh/TAIEX/MI_5MINS_INDEX?response=json&date={today_str}"
        headers = {"User-Agent": "Mozilla/5.0"}

        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        rows = data.get("data", [])

        if not rows or len(rows) < 2:
            print("[market_sentiment] ⚠️ 資料不足")
            return "中性"

        # 過濾非法數值（如 "--"）
        def safe_float(value):
            try:
                return float(value.replace(",", ""))
            except:
                return None

        first = safe_float(rows[0][1])
        last = safe_float(rows[-1][1])

        if first is None or last is None or first == 0:
            print("[market_sentiment] ⚠️ 數值轉換失敗")
            return "中性"

        percent_change = (last - first) / first * 100

        if percent_change > 0.5:
            return "正向"
        elif percent_change < -0.5:
            return "負向"
        else:
            return "中性"

    except Exception as e:
        print(f"[market_sentiment] ❌ 擷取失敗：{e}")
        return "中性"

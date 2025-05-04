import os
import requests
from datetime import date

FINMIND_API = "https://api.finmindtrade.com/api/v4/data"
TOKEN = os.getenv("FINMIND_TOKEN")

# ✅ 基本請求格式
def fetch_data(dataset, **kwargs):
    payload = {
        "dataset": dataset,
        "token": TOKEN,
        **kwargs
    }
    response = requests.get(FINMIND_API, params=payload)
    data = response.json()
    if not data.get("data"):
        return []
    return data["data"]

# ✅ 1️⃣ 取得熱門成交前 100 名股票（模擬，待你有完整來源後接替）
def get_top_100_stocks():
    # TODO: 可改抓成交金額最大前百大
    return ["2330", "2317", "2454", "2603", "2303", "2884", "2308", "1101", "8046", "2609"][:100]

# ✅ 2️⃣ 取得殖利率高的股票
def get_top_dividend_stocks(limit=5):
    today = str(date.today())
    data = fetch_data("TaiwanStockDividendYield", date=today)
    sorted_data = sorted(data, key=lambda x: x.get("DividendYield", 0), reverse=True)
    return [(d["stock_id"], round(d["DividendYield"], 2)) for d in sorted_data[:limit]]

# ✅ 3️⃣ 偵測異常放量個股（可根據 Volume 成交量判斷）
def get_intraday_breakout_stocks(limit=5):
    top_stocks = get_top_100_stocks()
    result = []
    for sid in top_stocks:
        try:
            data = fetch_data("TaiwanStockPrice", stock_id=sid, start_date=str(date.today()))
            if not data or len(data) < 2:
                continue
            latest = data[-1]
            if latest["Trading_Volume"] > 5000:  # 門檻可自訂
                result.append((sid, "今日爆量放大，短線走勢轉強"))
            if len(result) >= limit:
                break
        except:
            continue
    return result

# ✅ 4️⃣ 收盤推薦股篩選（模擬條件：法人買超 + 上漲）
def get_closing_recommendations(limit=5):
    top_stocks = get_top_100_stocks()
    recommendations = []

    for sid in top_stocks:
        data = fetch_data("TaiwanStockInstitutionalInvestors", stock_id=sid, start_date=str(date.today()))
        if not data:
            continue
        net_buy = sum(d["buy"] - d["sell"] for d in data)
        if net_buy > 500:  # 可自訂門檻
            recommendations.append((sid, "法人買超明顯，短線趨勢偏多"))
        if len(recommendations) >= limit:
            break
    return recommendations

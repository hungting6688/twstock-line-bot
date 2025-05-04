from datetime import date
from finmind_utils import fetch_finmind_data

def analyze_dividend(stock_id="2330"):
    today = date.today().strftime("%Y-%m-%d")
    df = fetch_finmind_data(
        dataset="TaiwanStockDividend",
        params={"stock_id": stock_id, "date": today}
    )
    if df.empty:
        return f"無法取得 {stock_id} 的殖利率資訊"
    
    latest = df.iloc[-1]
    return (
        f"【殖利率】{stock_id}\n"
        f"股利年度：{latest['year']}\n"
        f"現金股利：{latest['cash_dividend']}\n"
        f"殖利率：約 {latest.get('dividend_yield', '未知')}%\n"
    )

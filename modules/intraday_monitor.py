from datetime import date
from finmind_utils import fetch_finmind_data

def intraday_check(stock_id="2330"):
    today = date.today().strftime("%Y-%m-%d")
    df = fetch_finmind_data(
        dataset="TaiwanStockInstitutionalInvestors",
        params={"stock_id": stock_id, "date": today}
    )
    if df.empty:
        return f"【法人】{stock_id}：無資料"

    buy_total = df["buy"].sum()
    sell_total = df["sell"].sum()
    net = buy_total - sell_total

    return (
        f"【法人買賣超】{stock_id}\n"
        f"買進總額：{buy_total}\n"
        f"賣出總額：{sell_total}\n"
        f"淨買賣：{'買超' if net > 0 else '賣超'} {abs(net)} 張"
    )

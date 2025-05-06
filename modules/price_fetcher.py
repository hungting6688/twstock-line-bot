# modules/price_fetcher.py

import requests
import pandas as pd

def get_top_stocks(limit=100, filter_type=None):
    """
    自動擷取台股熱門股（依成交金額排序），可透過 limit 控制數量。
    
    Parameters:
        limit (int): 回傳股票數量（預設 100）
        filter_type (str): "large_cap" / "small_cap" / None
        
    Returns:
        list[str]: 熱門股票代碼列表
    """
    url = "https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date=&type=ALL"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        table = data["data5"]
        df = pd.DataFrame(table, columns=data["fields5"])

        # 清理與過濾資料
        df = df[df["證券代號"].str.isnumeric()]  # 只留數字代碼
        df["成交金額(元)"] = df["成交金額(元)"].str.replace(",", "").astype(float)
        df = df.sort_values(by="成交金額(元)", ascending=False)

        stock_ids = df["證券代號"].tolist()

        if filter_type == "large_cap":
            return stock_ids[:limit]
        elif filter_type == "small_cap":
            return stock_ids[-limit:]
        else:
            return stock_ids[:limit]

    except Exception as e:
        print(f"[get_top_stocks] 擷取失敗：{e}")
        return []

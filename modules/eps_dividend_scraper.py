# modules/eps_dividend_scraper.py

def get_eps_data() -> dict:
    """
    模擬回傳每檔股票的 EPS / 股利等基本面資料。
    真實版本未來可透過公開財報網站爬蟲實作。
    
    回傳格式：
        {
            "2330": {"eps": 25.6, "dividend": 18},
            "2317": {"eps": 10.2, "dividend": 5},
            ...
        }
    """
    return {
        "2330": {"eps": 25.6, "dividend": 18},
        "2317": {"eps": 10.2, "dividend": 5},
        "2454": {"eps": 15.3, "dividend": 10},
        "2303": {"eps": 5.1, "dividend": 2},
    }

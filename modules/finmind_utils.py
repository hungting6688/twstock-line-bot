import os
import requests
import pandas as pd

def get_finmind_token():
    """從 GitHub Secrets 取得金鑰"""
    return os.getenv("FINMIND_TOKEN")

def fetch_finmind_data(dataset: str, params: dict) -> pd.DataFrame:
    """通用 FinMind 抓資料函式"""
    token = get_finmind_token()
    url = "https://api.finmindtrade.com/api/v4/data"
    full_params = {
        "dataset": dataset,
        "token": token,
        **params
    }
    response = requests.get(url, params=full_params)
    data = response.json()
    if data["status"] != 200 or not data["data"]:
        print(f"⚠️ FinMind API 無資料，請檢查：{dataset} / {params}")
        return pd.DataFrame()
    return pd.DataFrame(data["data"])

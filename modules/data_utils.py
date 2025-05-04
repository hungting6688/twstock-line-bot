import random

def get_top_100_stocks():
    # TODO: 實作從 API 擷取真實成交量前 100 檔個股邏輯
    # 暫時用模擬假資料
    return [f"{random.randint(1100, 9999)}" for _ in range(100)]

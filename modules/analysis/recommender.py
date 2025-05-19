@staticmethod
def get_stock_recommendations(time_slot, count=None):
    """
    根據時段獲取推薦股票
    
    Args:
        time_slot (str): 時段 ('morning', 'noon', 'afternoon', 'evening')
        count (int): 推薦股票數量，None 表示使用預設值
    
    Returns:
        list: 推薦股票列表
    """
    print(f"[stock_recommender] ⏳ 執行{time_slot}推薦分析...")
    
    # 根據時段設置預設推薦數量
    if count is None:
        if time_slot == 'morning':
            count = 6  # 早盤前推薦6檔
        elif time_slot == 'noon':
            count = 6  # 午盤推薦6檔
        elif time_slot == 'afternoon':
            count = 6  # 上午看盤推薦6檔
        elif time_slot == 'evening':
            count = 10  # 盤後分析推薦10檔
        else:
            count = 6  # 默認值
    
    strategies = {
        'morning': StockRecommender._morning_strategy,
        'noon': StockRecommender._noon_strategy,
        'afternoon': StockRecommender._afternoon_strategy,
        'evening': StockRecommender._evening_strategy
    }
    
    strategy_func = strategies.get(time_slot)
    return strategy_func(count) if strategy_func else []

@staticmethod
def get_weak_valley_alerts(count=2):
    """
    識別處於極弱谷狀態的股票
    
    Args:
        count (int): 極弱谷股票數量，默認為2
    
    Returns:
        list: 極弱谷股票列表
    """
    print("[stock_recommender] ⏳ 掃描極弱谷股票...")
    
    stock_ids = get_top_stocks(limit=300)  # 從前300檔中尋找極弱谷股票
    alerts = []
    
    # 其餘邏輯保持不變...
    
    # 限制返回數量
    return alerts[:count]  # 只返回指定數量的極弱谷股票

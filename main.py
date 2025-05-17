# app.py 中添加
import schedule
import time
import threading
from datetime import datetime

# 引入新功能模組
from modules.stock_recommender import get_stock_recommendations, get_weak_valley_alerts
from modules.multi_analysis import analyze_stock_value

# 定義四個時段的推播功能
def morning_push():
    """早盤前推播 (9:00)"""
    stocks = get_stock_recommendations('morning')
    weak_valleys = get_weak_valley_alerts()
    
    # 推播給所有訂閱用戶
    user_ids = get_all_subscribed_users()
    for user_id in user_ids:
        send_recommendations(user_id, stocks, time_slot="早盤前")
        if weak_valleys:
            send_weak_valley_alerts(user_id, weak_valleys)

def noon_push():
    """中午休盤推播 (12:30)"""
    stocks = get_stock_recommendations('noon')
    user_ids = get_all_subscribed_users()
    for user_id in user_ids:
        send_recommendations(user_id, stocks, time_slot="中午休盤時")

def afternoon_push():
    """尾盤前推播 (13:00)"""
    stocks = get_stock_recommendations('afternoon')
    user_ids = get_all_subscribed_users()
    for user_id in user_ids:
        send_recommendations(user_id, stocks, time_slot="尾盤前")

def evening_push():
    """盤後分析推播 (15:00)"""
    stocks = get_stock_recommendations('evening')
    user_ids = get_all_subscribed_users()
    for user_id in user_ids:
        send_recommendations(user_id, stocks, time_slot="盤後分析")

def get_all_subscribed_users():
    """獲取所有訂閱推播的用戶 ID"""
    # 從資料庫獲取訂閱用戶
    # 這裡需要實現資料庫相關的代碼
    # 示例：
    return db.query("SELECT user_id FROM subscriptions WHERE is_active = TRUE")

def send_recommendations(user_id, stocks, time_slot):
    """發送股票推薦訊息"""
    message = f"【{time_slot}推薦股票】\n\n"
    for stock in stocks:
        message += f"📈 {stock['code']} {stock['name']}\n"
        message += f"推薦理由: {stock['reason']}\n"
        message += f"目標價: {stock['target_price']}\n"
        message += f"止損價: {stock['stop_loss']}\n\n"
    
    line_bot_api.push_message(user_id, TextSendMessage(text=message))

def send_weak_valley_alerts(user_id, weak_valleys):
    """發送極弱谷提醒"""
    message = "【極弱谷警報】\n\n"
    for stock in weak_valleys:
        message += f"⚠️ {stock['code']} {stock['name']}\n"
        message += f"當前價格: {stock['current_price']}\n"
        message += f"警報原因: {stock['alert_reason']}\n\n"
    
    line_bot_api.push_message(user_id, TextSendMessage(text=message))

# 設置排程任務
def setup_schedule():
    # 只在交易日執行推播
    schedule.every().day.at("09:00").do(lambda: is_trading_day() and morning_push())
    schedule.every().day.at("12:30").do(lambda: is_trading_day() and noon_push())
    schedule.every().day.at("13:00").do(lambda: is_trading_day() and afternoon_push())
    schedule.every().day.at("15:00").do(lambda: is_trading_day() and evening_push())

def is_trading_day():
    """檢查今天是否為交易日 (排除假日和週末)"""
    today = datetime.now()
    weekday = today.weekday()
    
    # 週末不是交易日
    if weekday >= 5:  # 5=週六, 6=週日
        return False
    
    # 這裡可以添加台灣股市假日檢查邏輯
    # 可以使用一個假日列表或API來檢查
    holidays = get_taiwan_stock_holidays()  # 實現這個函數來獲取台灣股市假日
    if today.strftime('%Y-%m-%d') in holidays:
        return False
    
    return True

def get_taiwan_stock_holidays():
    """獲取台灣股市假日列表"""
    # 可從 TWSE 網站獲取或者手動維護
    # 示例：
    return [
        "2025-01-01",  # 元旦
        "2025-01-29",  # 除夕
        "2025-01-30",  # 春節
        "2025-01-31",  # 春節
        # 更多假日...
    ]

# 在單獨的線程中運行排程器
def run_scheduler():
    setup_schedule()
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分鐘檢查一次排程

# 在主程式啟動時開始排程器
scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.daemon = True
scheduler_thread.start()

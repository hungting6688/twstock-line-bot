#!/usr/bin/env python3
import os
import sys
import argparse
from datetime import datetime

# 引入現有功能模組
from modules.run_opening import analyze_opening
from modules.intraday_monitor import analyze_intraday
from modules.dividend import analyze_dividend
from modules.closing_summary import analyze_closing
from modules.line_bot import send_line_bot_message

# 引入新功能模組
from modules.stock_recommender import get_stock_recommendations, get_weak_valley_alerts, send_recommendations_to_user, send_weak_valley_alerts_to_user

# 檢查命令行參數
parser = argparse.ArgumentParser(description='twstock-line-bot')
parser.add_argument('--mode', type=str, choices=['opening', 'intraday', 'dividend', 'closing', 'morning', 'noon', 'afternoon', 'evening'], help='指定執行模式')
args = parser.parse_args()

# 定義四個時段的推播功能
def morning_push():
    """早盤前推播 (9:00)"""
    print("[main] ⏳ 執行早盤前推播...")
    try:
        stocks = get_stock_recommendations('morning')
        weak_valleys = get_weak_valley_alerts()
        
        # 使用 LINE_USER_ID 作為推播對象
        user_id = os.getenv("LINE_USER_ID")
        if user_id:
            send_recommendations_to_user(user_id, stocks, "早盤前")
            if weak_valleys:
                send_weak_valley_alerts_to_user(user_id, weak_valleys)
        else:
            print("[main] ⚠️ 未設定 LINE_USER_ID，無法推播")
    except Exception as e:
        print(f"[main] ❌ 早盤前推播失敗：{e}")

def noon_push():
    """中午休盤推播 (12:30)"""
    print("[main] ⏳ 執行中午休盤推播...")
    try:
        stocks = get_stock_recommendations('noon')
        
        # 使用 LINE_USER_ID 作為推播對象
        user_id = os.getenv("LINE_USER_ID")
        if user_id:
            send_recommendations_to_user(user_id, stocks, "中午休盤時")
        else:
            print("[main] ⚠️ 未設定 LINE_USER_ID，無法推播")
    except Exception as e:
        print(f"[main] ❌ 中午休盤推播失敗：{e}")

def afternoon_push():
    """尾盤前推播 (13:00)"""
    print("[main] ⏳ 執行尾盤前推播...")
    try:
        stocks = get_stock_recommendations('afternoon')
        
        # 使用 LINE_USER_ID 作為推播對象
        user_id = os.getenv("LINE_USER_ID")
        if user_id:
            send_recommendations_to_user(user_id, stocks, "尾盤前")
        else:
            print("[main] ⚠️ 未設定 LINE_USER_ID，無法推播")
    except Exception as e:
        print(f"[main] ❌ 尾盤前推播失敗：{e}")

def evening_push():
    """盤後分析推播 (15:00)"""
    print("[main] ⏳ 執行盤後分析推播...")
    try:
        stocks = get_stock_recommendations('evening')
        
        # 使用 LINE_USER_ID 作為推播對象
        user_id = os.getenv("LINE_USER_ID")
        if user_id:
            send_recommendations_to_user(user_id, stocks, "盤後分析")
        else:
            print("[main] ⚠️ 未設定 LINE_USER_ID，無法推播")
    except Exception as e:
        print(f"[main] ❌ 盤後分析推播失敗：{e}")

def is_trading_day():
    """檢查今天是否為交易日 (排除假日和週末)"""
    today = datetime.now()
    weekday = today.weekday()
    
    # 週末不是交易日
    if weekday >= 5:  # 5=週六, 6=週日
        print("[main] 今天是週末，不執行推播")
        return False
    
    # 這裡可以添加台灣股市假日檢查邏輯
    # 可以使用一個假日列表或API來檢查
    holidays = get_taiwan_stock_holidays()
    if today.strftime('%Y-%m-%d') in holidays:
        print(f"[main] 今天是股市假日 {today.strftime('%Y-%m-%d')}，不執行推播")
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

# 根據命令行參數執行相應功能
if args.mode:
    # 首先檢查是否為交易日
    if not is_trading_day() and args.mode in ['morning', 'noon', 'afternoon', 'evening']:
        print(f"[main] ⚠️ 今天不是交易日，不執行 {args.mode} 推播")
        sys.exit(0)
        
    # 執行指定模式
    if args.mode == 'opening':
        analyze_opening()
    elif args.mode == 'intraday':
        analyze_intraday()
    elif args.mode == 'dividend':
        analyze_dividend()
    elif args.mode == 'closing':
        analyze_closing()
    elif args.mode == 'morning':
        morning_push()
    elif args.mode == 'noon':
        noon_push()
    elif args.mode == 'afternoon':
        afternoon_push()
    elif args.mode == 'evening':
        evening_push()
    sys.exit(0)
else:
    print("[main] ⚠️ 未指定執行模式，使用方式: python main.py --mode=[opening|intraday|dividend|closing|morning|noon|afternoon|evening]")
    sys.exit(1)

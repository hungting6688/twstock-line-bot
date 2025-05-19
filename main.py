"""
更新 main.py 以使用雙重通知系統
"""

#!/usr/bin/env python3
import os
import sys
import argparse
from datetime import datetime, timedelta
import threading
import time


# 引入通知報告模組
from modules.notification.reports import (
    analyze_opening,
    analyze_intraday,
    analyze_dividend,
    analyze_closing
)

# 引入雙重通知系統
from modules.notification.dual_notifier import (
    send_notification, 
    send_stock_recommendations, 
    send_weak_valley_alerts
)

# 引入舊版 Line Bot (備用)
from modules.notification.line_bot import send_line_bot_message

# 引入新功能模組
from modules.analysis.recommender import (
    get_stock_recommendations, 
    get_weak_valley_alerts
)

# 引入工具模組
try:
    from modules.utils import check_network_connectivity, clear_cache
except ImportError:
    # 如果工具模組不可用，提供空函數
    def check_network_connectivity():
        print("[main] ⚠️ 未找到工具模組，跳過網絡檢查")
        return True
        
    def clear_cache(days_old=None):
        print("[main] ⚠️ 未找到工具模組，跳過緩存清理")
        return (0, 0)

# 檢查命令行參數
parser = argparse.ArgumentParser(description='twstock-line-bot')
parser.add_argument('--mode', type=str, choices=['opening', 'intraday', 'dividend', 'closing', 'morning', 'noon', 'afternoon', 'evening'], help='指定執行模式')
parser.add_argument('--check', action='store_true', help='檢查系統環境')
parser.add_argument('--clear-cache', action='store_true', help='清理過期緩存')
parser.add_argument('--debug', action='store_true', help='調試模式')
args = parser.parse_args()

# 如果指定了調試模式，設置環境變量
if args.debug:
    os.environ["DEBUG"] = "1"
    print("[main] ⚠️ 已啟用調試模式")

# 定義四個時段的推播功能
def morning_push():
    """早盤前推播 (9:00)"""
    print("[main] ⏳ 執行早盤前推播...")
    try:
        # 添加超時控制
        result = {"stocks": None, "weak_valleys": None, "completed": False}
        
        def run_recommendations():
            try:
                result["stocks"] = get_stock_recommendations('morning')
                result["weak_valleys"] = get_weak_valley_alerts(2)
                result["completed"] = True
            except Exception as e:
                print(f"[main] ⚠️ 推薦分析過程中出錯：{e}")
        
        # 創建並啟動線程
        t = threading.Thread(target=run_recommendations)
        t.daemon = True
        t.start()
        
        # 等待線程完成或超時（180秒，原為60秒）
        max_wait = 180
        waited = 0
        while not result["completed"] and waited < max_wait:
            time.sleep(5)
            waited += 5
            print(f"[main] 等待推薦結果... ({waited}/{max_wait}秒)")
        
        if not result["completed"]:
            raise TimeoutError("推薦分析超時")
        
        stocks = result["stocks"]
        weak_valleys = result["weak_valleys"]
        
        # 使用雙重通知系統
        send_stock_recommendations(stocks, "早盤前")
        if weak_valleys:
            send_weak_valley_alerts(weak_valleys)
            
        print("[main] ✅ 早盤前推播完成")
    except Exception as e:
        error_message = f"[main] ❌ 早盤前推播失敗：{e}"
        print(error_message)
        # 系統錯誤也通知用戶
        send_notification(error_message, "系統錯誤 - 早盤前推播失敗")

def noon_push():
    """中午休盤推播 (12:30)"""
    print("[main] ⏳ 執行中午休盤推播...")
    try:
        # 添加超時控制
        result = {"stocks": None, "weak_valleys": None, "completed": False}
        
        def run_recommendations():
            try:
                result["stocks"] = get_stock_recommendations('noon')
                result["weak_valleys"] = get_weak_valley_alerts(2)
                result["completed"] = True
            except Exception as e:
                print(f"[main] ⚠️ 推薦分析過程中出錯：{e}")
        
        # 創建並啟動線程
        t = threading.Thread(target=run_recommendations)
        t.daemon = True
        t.start()
        
        # 等待線程完成或超時（180秒，原為60秒）
        max_wait = 180
        waited = 0
        while not result["completed"] and waited < max_wait:
            time.sleep(5)
            waited += 5
            print(f"[main] 等待推薦結果... ({waited}/{max_wait}秒)")
        
        if not result["completed"]:
            raise TimeoutError("推薦分析超時")
        
        stocks = result["stocks"]
        weak_valleys = result["weak_valleys"]
        
        # 使用雙重通知系統
        send_stock_recommendations(stocks, "中午休盤時")
        if weak_valleys:
            send_weak_valley_alerts(weak_valleys)
            
        print("[main] ✅ 中午休盤推播完成")
    except Exception as e:
        error_message = f"[main] ❌ 中午休盤推播失敗：{e}"
        print(error_message)
        # 系統錯誤也通知用戶
        send_notification(error_message, "系統錯誤 - 中午休盤推播失敗")

def afternoon_push():
    """尾盤前推播 (13:00)"""
    print("[main] ⏳ 執行尾盤前推播...")
    try:
        # 添加超時控制
        result = {"stocks": None, "weak_valleys": None, "completed": False}
        
        def run_recommendations():
            try:
                result["stocks"] = get_stock_recommendations('afternoon')
                result["weak_valleys"] = get_weak_valley_alerts(2)
                result["completed"] = True
            except Exception as e:
                print(f"[main] ⚠️ 推薦分析過程中出錯：{e}")
        
        # 創建並啟動線程
        t = threading.Thread(target=run_recommendations)
        t.daemon = True
        t.start()
        
        # 等待線程完成或超時（180秒，原為60秒）
        max_wait = 180
        waited = 0
        while not result["completed"] and waited < max_wait:
            time.sleep(5)
            waited += 5
            print(f"[main] 等待推薦結果... ({waited}/{max_wait}秒)")
        
        if not result["completed"]:
            raise TimeoutError("推薦分析超時")
        
        stocks = result["stocks"]
        weak_valleys = result["weak_valleys"]
        
        # 使用雙重通知系統
        send_stock_recommendations(stocks, "尾盤前")
        if weak_valleys:
            send_weak_valley_alerts(weak_valleys)
            
        print("[main] ✅ 尾盤前推播完成")
    except Exception as e:
        error_message = f"[main] ❌ 尾盤前推播失敗：{e}"
        print(error_message)
        # 系統錯誤也通知用戶
        send_notification(error_message, "系統錯誤 - 尾盤前推播失敗")

def evening_push():
    """盤後分析推播 (15:00)"""
    print("[main] ⏳ 執行盤後分析推播...")
    try:
        # 添加超時控制
        result = {"stocks": None, "completed": False}
        
        def run_recommendations():
            try:
                result["stocks"] = get_stock_recommendations('evening')
                result["completed"] = True
            except Exception as e:
                print(f"[main] ⚠️ 推薦分析過程中出錯：{e}")
        
        # 創建並啟動線程
        t = threading.Thread(target=run_recommendations)
        t.daemon = True
        t.start()
        
        # 等待線程完成或超時（180秒，原為60秒）
        max_wait = 180
        waited = 0
        while not result["completed"] and waited < max_wait:
            time.sleep(5)
            waited += 5
            print(f"[main] 等待推薦結果... ({waited}/{max_wait}秒)")
        
        if not result["completed"]:
            raise TimeoutError("推薦分析超時")
        
        stocks = result["stocks"]
        
        # 使用雙重通知系統
        send_stock_recommendations(stocks, "盤後分析")
        print("[main] ✅ 盤後分析推播完成")
    except Exception as e:
        error_message = f"[main] ❌ 盤後分析推播失敗：{e}"
        print(error_message)
        # 系統錯誤也通知用戶
        send_notification(error_message, "系統錯誤 - 盤後分析推播失敗")

def check_system_environment():
    """檢查系統環境"""
    print("[main] 🔍 開始檢查系統環境...")
    
    # 檢查網絡連線
    network_status = check_network_connectivity()
    
    # 檢查環境變數
    env_vars = {
        "LINE_CHANNEL_ACCESS_TOKEN": os.getenv("LINE_CHANNEL_ACCESS_TOKEN") is not None,
        "LINE_USER_ID": os.getenv("LINE_USER_ID") is not None,
        "EMAIL_SENDER": os.getenv("EMAIL_SENDER") is not None,
        "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD") is not None,
        "EMAIL_RECEIVER": os.getenv("EMAIL_RECEIVER") is not None,
        "GOOGLE_JSON_KEY": os.getenv("GOOGLE_JSON_KEY") is not None,
        "FINMIND_TOKEN": os.getenv("FINMIND_TOKEN") is not None
    }
    
    # 檢查緩存目錄
    cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
    cache_exists = os.path.exists(cache_dir)
    
    # 輸出檢查結果
    print("\n[main] 環境檢查結果:")
    print(f"網絡連線: {'✅ 正常' if network_status else '❌ 異常'}")
    
    print("\n環境變數:")
    for var, exists in env_vars.items():
        status = "✅" if exists else "❌"
        print(f"{status} {var}")
    
    print(f"\n緩存目錄: {'✅ 存在' if cache_exists else '❌ 不存在'}")
    if cache_exists:
        try:
            cache_files = os.listdir(cache_dir)
            cache_size = sum(os.path.getsize(os.path.join(cache_dir, f)) for f in cache_files if os.path.isfile(os.path.join(cache_dir, f)))
            cache_size_kb = cache_size / 1024
            print(f"緩存文件數量: {len(cache_files)}")
            print(f"緩存總大小: {cache_size_kb:.2f} KB")
        except Exception as e:
            print(f"讀取緩存目錄失敗: {e}")
    
    # 發送測試通知
    print("\n[main] 發送測試通知...")
    try:
        test_message = f"台股分析系統 - 環境檢查通知 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        send_notification(test_message, "系統環境檢查")
        print("✅ 發送測試通知成功")
    except Exception as e:
        print(f"❌ 發送測試通知失敗: {e}")
    
    print("\n[main] 系統環境檢查完成")

def is_trading_day():
    """檢查今天是否為交易日 (排除假日和週末)"""
    today = datetime.now()
    
    # 顯示當前時間，幫助診斷
    print(f"[main] 系統時間：{today}，星期：{today.weekday()}")
    
    # 設定台灣時區 (UTC+8)
    taiwan_tz_offset = timedelta(hours=8)
    taiwan_today = today + taiwan_tz_offset
    
    # 使用台灣時間判斷週末
    weekday = taiwan_today.weekday()
    print(f"[main] 台灣時間：{taiwan_today}，星期：{weekday}")
    
    # 調試模式：如果設置了 DEBUG 環境變量，則忽略交易日檢查
    if os.getenv("DEBUG") == "1":
        print("[main] ⚠️ 調試模式：忽略交易日檢查")
        return True
    
    # 週末不是交易日
    if weekday >= 5:  # 5=週六, 6=週日
        print("[main] 今天是週末，不執行推播")
        return False
    
    # 這裡可以添加台灣股市假日檢查邏輯
    # 可以使用一個假日列表或API來檢查
    holidays = get_taiwan_stock_holidays()
    if taiwan_today.strftime('%Y-%m-%d') in holidays:
        print(f"[main] 今天是股市假日 {taiwan_today.strftime('%Y-%m-%d')}，不執行推播")
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

# 主程式入口點
if __name__ == "__main__":
    # 處理命令行參數
    if args.check:
        check_system_environment()
        sys.exit(0)
        
    if args.clear_cache:
        print("[main] 清理過期緩存...")
        success, failed = clear_cache(days_old=7)  # 清理7天以上的緩存
        print(f"[main] 緩存清理完成: {success} 個文件已刪除，{failed} 個文件刪除失敗")
        sys.exit(0)
        
    # 執行交易相關功能
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

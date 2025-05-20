"""
更新 main.py 以增強錯誤處理和復原能力
- 優化超時處理
- 增加更好的部分結果支持 
- 添加緩存管理
- 2025年版本
"""

#!/usr/bin/env python3
import os
import sys
import argparse
from datetime import datetime, timedelta
import threading
import time
import json
import signal
import traceback


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

# 添加全局級別的異常處理和超時處理
class TimeoutException(Exception):
    """超時異常"""
    pass

def timeout_handler(signum, frame):
    """超時信號處理器"""
    raise TimeoutException("操作超時")

# 注冊信號處理器 (UNIX/Linux系統)
if sys.platform != 'win32':
    signal.signal(signal.SIGALRM, timeout_handler)

def run_with_timeout(func, args=(), kwargs={}, timeout_seconds=180, default_result=None):
    """
    使用超時運行函數
    
    參數:
    - func: 要運行的函數
    - args: 函數位置參數
    - kwargs: 函數關鍵字參數
    - timeout_seconds: 超時時間(秒)
    - default_result: 超時或失敗時的默認返回值
    
    返回:
    - 函數的返回值，或超時/失敗時的默認值
    """
    result = default_result
    completed = False
    error = None
    
    # 定義執行函數
    def target():
        nonlocal result, completed, error
        try:
            result = func(*args, **kwargs)
            completed = True
        except Exception as e:
            error = e
            traceback.print_exc()
            
    # 創建並啟動線程
    thread = threading.Thread(target=target)
    thread.daemon = True
    
    # 記錄開始時間
    start_time = time.time()
    
    # 啟動線程
    thread.start()
    
    # 等待線程完成或超時
    thread.join(timeout_seconds)
    
    # 檢查是否完成
    if not completed:
        if thread.is_alive():
            # 線程仍在運行，超時
            execution_time = time.time() - start_time
            print(f"[main] ⚠️ 操作在 {execution_time:.1f} 秒後超時")
            
            # 返回默認結果
            return default_result
        elif error:
            # 線程出錯
            print(f"[main] ❌ 操作失敗: {error}")
            return default_result
    
    return result

# 檢查命令行參數
parser = argparse.ArgumentParser(description='twstock-line-bot')
parser.add_argument('--mode', type=str, choices=['opening', 'intraday', 'dividend', 'closing', 'morning', 'noon', 'afternoon', 'evening'], help='指定執行模式')
parser.add_argument('--check', action='store_true', help='檢查系統環境')
parser.add_argument('--clear-cache', action='store_true', help='清理過期緩存')
parser.add_argument('--clear-all-cache', action='store_true', help='清理所有緩存')
parser.add_argument('--debug', action='store_true', help='調試模式')
parser.add_argument('--timeout', type=int, default=240, help='設置全局超時時間(秒)')
args = parser.parse_args()

# 如果指定了調試模式，設置環境變量
if args.debug:
    os.environ["DEBUG"] = "1"
    print("[main] ⚠️ 已啟用調試模式")

# 定義四個時段的推播功能
def morning_push(global_timeout=240):
    """
    早盤前推播 (9:00)
    
    參數:
    - global_timeout: 全局超時時間(秒)
    """
    print("[main] ⏳ 執行早盤前推播...")
    
    try:
        # 使用更長的超時時間獲取推薦 - 抓取財務數據需要較長時間
        timeout_recommendations = min(global_timeout - 30, 210)  # 預留30秒給其他操作
        print(f"[main] 設置股票推薦超時時間為 {timeout_recommendations} 秒")
        
        # 使用超時執行獲取推薦
        stocks = run_with_timeout(
            get_stock_recommendations, 
            args=('morning',), 
            timeout_seconds=timeout_recommendations,
            default_result=[]
        )
        
        # 檢查是否獲取到足夠的推薦
        if not stocks or len(stocks) < 2:
            # 如果不夠，嘗試從緩存或備用數據獲取
            print("[main] ⚠️ 未獲取到足夠的股票推薦，嘗試從緩存或備用數據獲取")
            
            # 嘗試讀取緩存
            cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
            cache_file = os.path.join(cache_dir, 'recommendation_morning_cache.json')
            
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                        if 'recommendations' in cache_data and len(cache_data['recommendations']) > 0:
                            stocks = cache_data['recommendations']
                            print(f"[main] ✅ 從緩存獲取了 {len(stocks)} 檔推薦股票")
                except Exception as e:
                    print(f"[main] ⚠️ 讀取緩存推薦失敗: {e}")
        
        # 使用較短的超時時間獲取極弱谷警報 - 這通常比股票推薦快
        timeout_weak_valleys = 60  # 60秒足夠了
        print(f"[main] 設置極弱谷警報超時時間為 {timeout_weak_valleys} 秒")
        
        # 使用超時執行獲取極弱谷
        weak_valleys = run_with_timeout(
            get_weak_valley_alerts,
            args=(2,),
            timeout_seconds=timeout_weak_valleys,
            default_result=[]
        )
        
        # 使用雙重通知系統
        if stocks:
            try:
                send_stock_recommendations(stocks, "早盤前")
                print("[main] ✅ 已發送股票推薦通知")
            except Exception as e:
                print(f"[main] ⚠️ 發送股票推薦通知失敗: {e}")
                # 嘗試使用備用方式通知
                error_message = f"發送股票推薦失敗: {e}"
                send_notification(error_message, "早盤前通知錯誤")
        else:
            print("[main] ⚠️ 沒有可推薦的股票")
            send_notification("今日早盤無推薦股票。系統無法獲取有效數據或符合條件的股票。", "早盤前推薦 - 無結果")
        
        # 只在早盤前發送極弱谷警報
        if weak_valleys:
            try:
                send_weak_valley_alerts(weak_valleys)
                print("[main] ✅ 已發送極弱谷警報通知")
            except Exception as e:
                print(f"[main] ⚠️ 發送極弱谷警報通知失敗: {e}")
                # 嘗試使用備用方式通知
                error_message = f"發送極弱谷警報失敗: {e}"
                send_notification(error_message, "極弱谷警報通知錯誤")
            
        print("[main] ✅ 早盤前推播完成")
        return True
    except Exception as e:
        error_message = f"[main] ❌ 早盤前推播失敗：{e}"
        print(error_message)
        
        # 系統錯誤也通知用戶
        try:
            send_notification(error_message, "系統錯誤 - 早盤前推播失敗")
        except Exception as notify_error:
            print(f"[main] ❌ 發送錯誤通知也失敗了: {notify_error}")
        
        return False

def noon_push(global_timeout=180):
    """
    中午休盤推播 (12:30)
    
    參數:
    - global_timeout: 全局超時時間(秒)
    """
    print("[main] ⏳ 執行中午休盤推播...")
    
    try:
        # 使用較短的超時時間，因為中午分析通常較快
        timeout_recommendations = min(global_timeout - 20, 160)  # 預留20秒給其他操作
        print(f"[main] 設置股票推薦超時時間為 {timeout_recommendations} 秒")
        
        # 使用超時執行獲取推薦
        stocks = run_with_timeout(
            get_stock_recommendations, 
            args=('noon',), 
            timeout_seconds=timeout_recommendations,
            default_result=[]
        )
        
        # 檢查是否獲取到足夠的推薦
        if not stocks or len(stocks) < 2:
            # 如果不夠，嘗試從緩存或備用數據獲取
            print("[main] ⚠️ 未獲取到足夠的股票推薦，嘗試從緩存或備用數據獲取")
            
            # 嘗試讀取緩存
            cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
            cache_file = os.path.join(cache_dir, 'recommendation_noon_cache.json')
            
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                        if 'recommendations' in cache_data and len(cache_data['recommendations']) > 0:
                            stocks = cache_data['recommendations']
                            print(f"[main] ✅ 從緩存獲取了 {len(stocks)} 檔推薦股票")
                except Exception as e:
                    print(f"[main] ⚠️ 讀取緩存推薦失敗: {e}")
        
        # 使用雙重通知系統，僅發送股票推薦
        if stocks:
            try:
                send_stock_recommendations(stocks, "中午休盤時")
                print("[main] ✅ 已發送股票推薦通知")
            except Exception as e:
                print(f"[main] ⚠️ 發送股票推薦通知失敗: {e}")
                # 嘗試使用備用方式通知
                error_message = f"發送股票推薦失敗: {e}"
                send_notification(error_message, "中午休盤通知錯誤")
        else:
            print("[main] ⚠️ 沒有可推薦的股票")
            send_notification("今日中午無推薦股票。系統無法獲取有效數據或符合條件的股票。", "中午休盤推薦 - 無結果")
            
        print("[main] ✅ 中午休盤推播完成")
        return True
    except Exception as e:
        error_message = f"[main] ❌ 中午休盤推播失敗：{e}"
        print(error_message)
        
        # 系統錯誤也通知用戶
        try:
            send_notification(error_message, "系統錯誤 - 中午休盤推播失敗")
        except Exception as notify_error:
            print(f"[main] ❌ 發送錯誤通知也失敗了: {notify_error}")
        
        return False

def afternoon_push(global_timeout=180):
    """
    尾盤前推播 (13:00)
    
    參數:
    - global_timeout: 全局超時時間(秒)
    """
    print("[main] ⏳ 執行尾盤前推播...")
    
    try:
        # 使用較短的超時時間
        timeout_recommendations = min(global_timeout - 20, 160)  # 預留20秒給其他操作
        print(f"[main] 設置股票推薦超時時間為 {timeout_recommendations} 秒")
        
        # 使用超時執行獲取推薦
        stocks = run_with_timeout(
            get_stock_recommendations, 
            args=('afternoon',), 
            timeout_seconds=timeout_recommendations,
            default_result=[]
        )
        
        # 檢查是否獲取到足夠的推薦
        if not stocks or len(stocks) < 2:
            # 如果不夠，嘗試從緩存或備用數據獲取
            print("[main] ⚠️ 未獲取到足夠的股票推薦，嘗試從緩存或備用數據獲取")
            
            # 嘗試讀取緩存
            cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
            cache_file = os.path.join(cache_dir, 'recommendation_afternoon_cache.json')
            
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                        if 'recommendations' in cache_data and len(cache_data['recommendations']) > 0:
                            stocks = cache_data['recommendations']
                            print(f"[main] ✅ 從緩存獲取了 {len(stocks)} 檔推薦股票")
                except Exception as e:
                    print(f"[main] ⚠️ 讀取緩存推薦失敗: {e}")
        
        # 使用雙重通知系統，僅發送股票推薦
        if stocks:
            try:
                send_stock_recommendations(stocks, "尾盤前")
                print("[main] ✅ 已發送股票推薦通知")
            except Exception as e:
                print(f"[main] ⚠️ 發送股票推薦通知失敗: {e}")
                # 嘗試使用備用方式通知
                error_message = f"發送股票推薦失敗: {e}"
                send_notification(error_message, "尾盤前通知錯誤")
        else:
            print("[main] ⚠️ 沒有可推薦的股票")
            send_notification("今日尾盤無推薦股票。系統無法獲取有效數據或符合條件的股票。", "尾盤前推薦 - 無結果")
            
        print("[main] ✅ 尾盤前推播完成")
        return True
    except Exception as e:
        error_message = f"[main] ❌ 尾盤前推播失敗：{e}"
        print(error_message)
        
        # 系統錯誤也通知用戶
        try:
            send_notification(error_message, "系統錯誤 - 尾盤前推播失敗")
        except Exception as notify_error:
            print(f"[main] ❌ 發送錯誤通知也失敗了: {notify_error}")
        
        return False

def evening_push(global_timeout=240):
    """
    盤後分析推播 (15:00)
    
    參數:
    - global_timeout: 全局超時時間(秒)
    """
    print("[main] ⏳ 執行盤後分析推播...")
    
    try:
        # 使用更長的超時時間，因為市場閉市後，我們有更多時間處理
        timeout_recommendations = min(global_timeout - 30, 210)  # 預留30秒給其他操作
        print(f"[main] 設置股票推薦超時時間為 {timeout_recommendations} 秒")
        
        # 使用超時執行獲取推薦
        stocks = run_with_timeout(
            get_stock_recommendations, 
            args=('evening',), 
            timeout_seconds=timeout_recommendations,
            default_result=[]
        )
        
        # 檢查是否獲取到足夠的推薦
        if not stocks or len(stocks) < 2:
            # 如果不夠，嘗試從緩存或備用數據獲取
            print("[main] ⚠️ 未獲取到足夠的股票推薦，嘗試從緩存或備用數據獲取")
            
            # 嘗試讀取緩存
            cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
            cache_file = os.path.join(cache_dir, 'recommendation_evening_cache.json')
            
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                        if 'recommendations' in cache_data and len(cache_data['recommendations']) > 0:
                            stocks = cache_data['recommendations']
                            print(f"[main] ✅ 從緩存獲取了 {len(stocks)} 檔推薦股票")
                except Exception as e:
                    print(f"[main] ⚠️ 讀取緩存推薦失敗: {e}")
        
        # 使用雙重通知系統
        if stocks:
            try:
                send_stock_recommendations(stocks, "盤後分析")
                print("[main] ✅ 已發送股票推薦通知")
            except Exception as e:
                print(f"[main] ⚠️ 發送股票推薦通知失敗: {e}")
                # 嘗試使用備用方式通知
                error_message = f"發送股票推薦失敗: {e}"
                send_notification(error_message, "盤後分析通知錯誤")
        else:
            print("[main] ⚠️ 沒有可推薦的股票")
            send_notification("今日盤後無推薦股票。系統無法獲取有效數據或符合條件的股票。", "盤後分析 - 無結果")
        
        print("[main] ✅ 盤後分析推播完成")
        return True
    except Exception as e:
        error_message = f"[main] ❌ 盤後分析推播失敗：{e}"
        print(error_message)
        
        # 系統錯誤也通知用戶
        try:
            send_notification(error_message, "系統錯誤 - 盤後分析推播失敗")
        except Exception as notify_error:
            print(f"[main] ❌ 發送錯誤通知也失敗了: {notify_error}")
        
        return False

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
    os.makedirs(cache_dir, exist_ok=True)  # 確保緩存目錄存在
    
    cache_exists = os.path.exists(cache_dir)
    cache_writable = os.access(cache_dir, os.W_OK) if cache_exists else False
    
    # 輸出檢查結果
    print("\n[main] 環境檢查結果:")
    print(f"網絡連線: {'✅ 正常' if network_status else '❌ 異常'}")
    
    print("\n環境變數:")
    for var, exists in env_vars.items():
        status = "✅" if exists else "❌"
        print(f"{status} {var}")
    
    print(f"\n緩存目錄: {'✅ 存在' if cache_exists else '❌ 不存在'}")
    if cache_exists:
        print(f"緩存目錄可寫: {'✅ 是' if cache_writable else '❌ 否'}")
        try:
            cache_files = os.listdir(cache_dir)
            cache_size = sum(os.path.getsize(os.path.join(cache_dir, f)) for f in cache_files if os.path.isfile(os.path.join(cache_dir, f)))
            cache_size_kb = cache_size / 1024
            
            print(f"緩存文件數量: {len(cache_files)}")
            print(f"緩存總大小: {cache_size_kb:.2f} KB")
        except Exception as e:
            print(f"讀取緩存目錄失敗: {e}")
    
    # 檢查是否可以連接到重要財經網站
    print("\n[main] 檢查重要財經網站連接...")
    
    financial_sites = [
        "https://finance.yahoo.com",
        "https://mops.twse.com.tw",
        "https://isin.twse.com.tw",
        "https://www.twse.com.tw"
    ]
    
    import requests
    for site in financial_sites:
        try:
            response = requests.get(site, timeout=5)
            print(f"✅ {site}: 連接成功，狀態碼 {response.status_code}")
        except Exception as e:
            print(f"❌ {site}: 連接失敗 - {str(e)}")
    
    # 發送測試通知
    print("\n[main] 發送測試通知...")
    try:
        test_message = f"台股分析系統 - 環境檢查通知 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        send_notification(test_message, "系統環境檢查")
        print("✅ 發送測試通知成功")
    except Exception as e:
        print(f"❌ 發送測試通知失敗: {e}")
    
    print("\n[main] 系統環境檢查完成")
    return True

def manage_cache(clear_all=False):
    """
    緩存管理函數
    
    參數:
    - clear_all: 是否清除所有緩存
    
    返回:
    - (int, int): 成功刪除的文件數量，失敗的文件數量
    """
    cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
    os.makedirs(cache_dir, exist_ok=True)  # 確保緩存目錄存在
    
    if clear_all:
        print("[main] 清理所有緩存...")
        success = 0
        failed = 0
        
        for filename in os.listdir(cache_dir):
            file_path = os.path.join(cache_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"[main] 已刪除: {filename}")
                    success += 1
            except Exception as e:
                print(f"[main] 無法刪除 {filename}: {e}")
                failed += 1
        
        print(f"[main] 緩存清理完成: {success} 個文件已刪除，{failed} 個文件刪除失敗")
        return success, failed
    else:
        # 刪除超過7天的舊緩存
        print("[main] 清理過期緩存...")
        success = 0
        failed = 0
        current_time = time.time()
        
        for filename in os.listdir(cache_dir):
            file_path = os.path.join(cache_dir, filename)
            try:
                if os.path.isfile(file_path):
                    # 獲取文件修改時間
                    mod_time = os.path.getmtime(file_path)
                    # 如果文件超過7天沒有修改過，刪除它
                    if current_time - mod_time > 7 * 24 * 60 * 60:
                        os.remove(file_path)
                        print(f"[main] 已刪除過期緩存: {filename}")
                        success += 1
            except Exception as e:
                print(f"[main] 無法刪除 {filename}: {e}")
                failed += 1
        
        print(f"[main] 過期緩存清理完成: {success} 個文件已刪除，{failed} 個文件刪除失敗")
        return success, failed

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
    """獲取台灣股市假日列表 - 2025年版本"""
    # 可從 TWSE 網站獲取或者手動維護
    # 2025年台股休市日 (包括國定假日及彈性放假)
    return [
        "2025-01-01",  # 元旦
        "2025-01-20",  # 選舉假期
        "2025-01-29",  # 除夕
        "2025-01-30",  # 春節
        "2025-01-31",  # 春節
        "2025-02-03",  # 春節
        "2025-02-28",  # 228和平紀念日
        "2025-04-04",  # 兒童節
        "2025-04-05",  # 清明節
        "2025-05-01",  # 勞動節
        "2025-06-09",  # 端午節
        "2025-09-29",  # 中秋節
        "2025-10-10",  # 國慶日
        # 更多假日...
    ]

# 主程式入口點
if __name__ == "__main__":
    # 處理命令行參數
    if args.check:
        check_system_environment()
        sys.exit(0)
    
    if args.clear_cache:
        success, failed = manage_cache(clear_all=False)
        sys.exit(0)
    
    if args.clear_all_cache:
        success, failed = manage_cache(clear_all=True)
        sys.exit(0)
    
    # 獲取全局超時設置
    global_timeout = args.timeout
    print(f"[main] 全局超時設定: {global_timeout} 秒")
    
    # 執行交易相關功能
    if args.mode:
        # 首先檢查是否為交易日
        if not is_trading_day() and args.mode in ['morning', 'noon', 'afternoon', 'evening']:
            print(f"[main] ⚠️ 今天不是交易日，不執行 {args.mode} 推播")
            sys.exit(0)
            
        # 執行指定模式
        try:
            success = False
            
            if args.mode == 'opening':
                success = run_with_timeout(analyze_opening, timeout_seconds=global_timeout, default_result=False)
            elif args.mode == 'intraday':
                success = run_with_timeout(analyze_intraday, timeout_seconds=global_timeout, default_result=False)
            elif args.mode == 'dividend':
                success = run_with_timeout(analyze_dividend, timeout_seconds=global_timeout, default_result=False)
            elif args.mode == 'closing':
                success = run_with_timeout(analyze_closing, timeout_seconds=global_timeout, default_result=False)
            elif args.mode == 'morning':
                success = morning_push(global_timeout)
            elif args.mode == 'noon':
                success = noon_push(global_timeout)
            elif args.mode == 'afternoon':
                success = afternoon_push(global_timeout)
            elif args.mode == 'evening':
                success = evening_push(global_timeout)
            
            if success:
                print(f"[main] ✅ {args.mode} 模式執行成功！")
                sys.exit(0)
            else:
                print(f"[main] ❌ {args.mode} 模式執行失敗")
                sys.exit(1)
                
        except Exception as e:
            print(f"[main] ❌ 執行過程中出現嚴重錯誤: {e}")
            # 嘗試發送錯誤通知
            try:
                error_message = f"系統運行錯誤: {str(e)}\n\n{traceback.format_exc()}"
                send_notification(error_message, f"系統錯誤 - {args.mode}模式")
            except:
                pass
            sys.exit(1)
    else:
        print("[main] ⚠️ 未指定執行模式，使用方式: python main.py --mode=[opening|intraday|dividend|closing|morning|noon|afternoon|evening]")
        sys.exit(1)

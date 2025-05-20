"""
台股分析系統主程式 - 整合三策略推播功能
"""
import os
import sys
import json
import traceback
import signal
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

# 確保可以找到模組
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 導入自訂模組
from modules.analysis.recommender import (
    get_stock_recommendations, 
    get_multi_strategy_recommendations,
    get_weak_stock_alerts
)
from modules.notification.dual_notifier import (
    send_notification, 
    send_stock_recommendations,
    send_weak_stock_alerts,
    send_combined_recommendations
)
from modules.config import TIMEOUT_SECONDS


def run_with_timeout(func, args=(), kwargs=None, timeout_seconds=300, default_result=None):
    """
    在超時限制內運行函數
    
    參數:
    - func: 要執行的函數
    - args: 函數參數元組
    - kwargs: 函數關鍵字參數字典
    - timeout_seconds: 超時秒數
    - default_result: 超時時的默認返回值
    
    返回:
    - 函數結果或默認值(如果超時)
    """
    if kwargs is None:
        kwargs = {}
    
    result = default_result
    
    # 設置超時處理
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            result = future.result(timeout=timeout_seconds)
        except TimeoutError:
            print(f"[main] ⚠️ 函數 {func.__name__} 執行超時({timeout_seconds}秒)")
        except Exception as e:
            print(f"[main] ❌ 函數 {func.__name__} 執行失敗: {e}")
            traceback.print_exc()
    
    return result


def morning_push(global_timeout=240):
    """
    早盤前推播 (9:00) - 整合短線、長線、極弱股三策略
    
    參數:
    - global_timeout: 全局超時時間(秒)
    """
    print("[main] ⏳ 執行早盤前推播...")
    
    try:
        # 設置超時時間
        timeout_recommendations = min(global_timeout - 30, 210)  # 預留30秒給其他操作
        print(f"[main] 設置多策略分析超時時間為 {timeout_recommendations} 秒")
        
        # 使用超時執行獲取多策略推薦
        strategies_data = run_with_timeout(
            get_multi_strategy_recommendations, 
            args=('morning',), 
            timeout_seconds=timeout_recommendations,
            default_result={"short_term": [], "long_term": [], "weak_stocks": []}
        )
        
        # 檢查是否獲取到足夠的推薦
        short_term_stocks = strategies_data.get("short_term", [])
        long_term_stocks = strategies_data.get("long_term", [])
        weak_stocks = strategies_data.get("weak_stocks", [])
        
        # 如果任一策略沒有獲取到足夠的推薦，嘗試從緩存或備用數據獲取
        if not short_term_stocks or not long_term_stocks:
            print("[main] ⚠️ 未獲取到足夠的股票推薦，嘗試從緩存獲取")
            
            # 嘗試讀取緩存
            cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
            cache_file = os.path.join(cache_dir, 'multi_strategy_morning_cache.json')
            
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                        if 'recommendations' in cache_data:
                            # 如果短線推薦不足，從緩存獲取
                            if not short_term_stocks and "short_term" in cache_data['recommendations']:
                                short_term_stocks = cache_data['recommendations']["short_term"]
                                strategies_data["short_term"] = short_term_stocks
                                print(f"[main] ✅ 從緩存獲取了 {len(short_term_stocks)} 檔短線推薦股票")
                            
                            # 如果長線推薦不足，從緩存獲取
                            if not long_term_stocks and "long_term" in cache_data['recommendations']:
                                long_term_stocks = cache_data['recommendations']["long_term"]
                                strategies_data["long_term"] = long_term_stocks
                                print(f"[main] ✅ 從緩存獲取了 {len(long_term_stocks)} 檔長線推薦股票")
                            
                            # 如果極弱谷警示不足，從緩存獲取
                            if not weak_stocks and "weak_stocks" in cache_data['recommendations']:
                                weak_stocks = cache_data['recommendations']["weak_stocks"]
                                strategies_data["weak_stocks"] = weak_stocks
                                print(f"[main] ✅ 從緩存獲取了 {len(weak_stocks)} 檔極弱股警示")
                except Exception as e:
                    print(f"[main] ⚠️ 讀取緩存推薦失敗: {e}")
        
        # 使用雙重通知系統發送綜合推薦報告
        try:
            # 使用新的综合推播功能
            send_combined_recommendations(strategies_data, "早盤前")
            print("[main] ✅ 已發送多策略分析報告")
        except Exception as e:
            print(f"[main] ⚠️ 發送多策略分析報告失敗: {e}")
            # 嘗試使用備用方式通知
            error_message = f"發送多策略分析報告失敗: {e}"
            send_notification(error_message, "早盤前通知錯誤")
            
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


def noon_push(global_timeout=240):
    """
    午盤推播 (12:30) - 整合短線、長線、極弱股三策略
    
    參數:
    - global_timeout: 全局超時時間(秒)
    """
    print("[main] ⏳ 執行午盤推播...")
    
    try:
        # 設置超時時間
        timeout_recommendations = min(global_timeout - 30, 210)  # 預留30秒給其他操作
        print(f"[main] 設置多策略分析超時時間為 {timeout_recommendations} 秒")
        
        # 使用超時執行獲取多策略推薦
        strategies_data = run_with_timeout(
            get_multi_strategy_recommendations, 
            args=('noon',), 
            timeout_seconds=timeout_recommendations,
            default_result={"short_term": [], "long_term": [], "weak_stocks": []}
        )
        
        # 檢查是否獲取到足夠的推薦
        short_term_stocks = strategies_data.get("short_term", [])
        long_term_stocks = strategies_data.get("long_term", [])
        weak_stocks = strategies_data.get("weak_stocks", [])
        
        # 如果任一策略沒有獲取到足夠的推薦，嘗試從緩存或備用數據獲取
        if not short_term_stocks or not long_term_stocks:
            print("[main] ⚠️ 未獲取到足夠的股票推薦，嘗試從緩存獲取")
            
            # 嘗試讀取緩存
            cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
            cache_file = os.path.join(cache_dir, 'multi_strategy_noon_cache.json')
            
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                        if 'recommendations' in cache_data:
                            # 如果短線推薦不足，從緩存獲取
                            if not short_term_stocks and "short_term" in cache_data['recommendations']:
                                short_term_stocks = cache_data['recommendations']["short_term"]
                                strategies_data["short_term"] = short_term_stocks
                                print(f"[main] ✅ 從緩存獲取了 {len(short_term_stocks)} 檔短線推薦股票")
                            
                            # 如果長線推薦不足，從緩存獲取
                            if not long_term_stocks and "long_term" in cache_data['recommendations']:
                                long_term_stocks = cache_data['recommendations']["long_term"]
                                strategies_data["long_term"] = long_term_stocks
                                print(f"[main] ✅ 從緩存獲取了 {len(long_term_stocks)} 檔長線推薦股票")
                            
                            # 如果極弱谷警示不足，從緩存獲取
                            if not weak_stocks and "weak_stocks" in cache_data['recommendations']:
                                weak_stocks = cache_data['recommendations']["weak_stocks"]
                                strategies_data["weak_stocks"] = weak_stocks
                                print(f"[main] ✅ 從緩存獲取了 {len(weak_stocks)} 檔極弱股警示")
                except Exception as e:
                    print(f"[main] ⚠️ 讀取緩存推薦失敗: {e}")
        
        # 使用雙重通知系統發送綜合推薦報告
        try:
            # 使用新的综合推播功能
            send_combined_recommendations(strategies_data, "午盤")
            print("[main] ✅ 已發送多策略分析報告")
        except Exception as e:
            print(f"[main] ⚠️ 發送多策略分析報告失敗: {e}")
            # 嘗試使用備用方式通知
            error_message = f"發送多策略分析報告失敗: {e}"
            send_notification(error_message, "午盤通知錯誤")
            
        print("[main] ✅ 午盤推播完成")
        return True
    except Exception as e:
        error_message = f"[main] ❌ 午盤推播失敗：{e}"
        print(error_message)
        
        # 系統錯誤也通知用戶
        try:
            send_notification(error_message, "系統錯誤 - 午盤推播失敗")
        except Exception as notify_error:
            print(f"[main] ❌ 發送錯誤通知也失敗了: {notify_error}")
        
        return False


def afternoon_push(global_timeout=240):
    """
    上午看盤推播 (10:30) - 整合短線、長線、極弱股三策略
    
    參數:
    - global_timeout: 全局超時時間(秒)
    """
    print("[main] ⏳ 執行上午看盤推播...")
    
    try:
        # 設置超時時間
        timeout_recommendations = min(global_timeout - 30, 210)  # 預留30秒給其他操作
        print(f"[main] 設置多策略分析超時時間為 {timeout_recommendations} 秒")
        
        # 使用超時執行獲取多策略推薦
        strategies_data = run_with_timeout(
            get_multi_strategy_recommendations, 
            args=('afternoon',), 
            timeout_seconds=timeout_recommendations,
            default_result={"short_term": [], "long_term": [], "weak_stocks": []}
        )
        
        # 檢查是否獲取到足夠的推薦
        short_term_stocks = strategies_data.get("short_term", [])
        long_term_stocks = strategies_data.get("long_term", [])
        weak_stocks = strategies_data.get("weak_stocks", [])
        
        # 如果任一策略沒有獲取到足夠的推薦，嘗試從緩存或備用數據獲取
        if not short_term_stocks or not long_term_stocks:
            print("[main] ⚠️ 未獲取到足夠的股票推薦，嘗試從緩存獲取")
            
            # 嘗試讀取緩存
            cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
            cache_file = os.path.join(cache_dir, 'multi_strategy_afternoon_cache.json')
            
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                        if 'recommendations' in cache_data:
                            # 如果短線推薦不足，從緩存獲取
                            if not short_term_stocks and "short_term" in cache_data['recommendations']:
                                short_term_stocks = cache_data['recommendations']["short_term"]
                                strategies_data["short_term"] = short_term_stocks
                                print(f"[main] ✅ 從緩存獲取了 {len(short_term_stocks)} 檔短線推薦股票")
                            
                            # 如果長線推薦不足，從緩存獲取
                            if not long_term_stocks and "long_term" in cache_data['recommendations']:
                                long_term_stocks = cache_data['recommendations']["long_term"]
                                strategies_data["long_term"] = long_term_stocks
                                print(f"[main] ✅ 從緩存獲取了 {len(long_term_stocks)} 檔長線推薦股票")
                            
                            # 如果極弱谷警示不足，從緩存獲取
                            if not weak_stocks and "weak_stocks" in cache_data['recommendations']:
                                weak_stocks = cache_data['recommendations']["weak_stocks"]
                                strategies_data["weak_stocks"] = weak_stocks
                                print(f"[main] ✅ 從緩存獲取了 {len(weak_stocks)} 檔極弱股警示")
                except Exception as e:
                    print(f"[main] ⚠️ 讀取緩存推薦失敗: {e}")
        
        # 使用雙重通知系統發送綜合推薦報告
        try:
            # 使用新的综合推播功能
            send_combined_recommendations(strategies_data, "上午看盤")
            print("[main] ✅ 已發送多策略分析報告")
        except Exception as e:
            print(f"[main] ⚠️ 發送多策略分析報告失敗: {e}")
            # 嘗試使用備用方式通知
            error_message = f"發送多策略分析報告失敗: {e}"
            send_notification(error_message, "上午看盤通知錯誤")
            
        print("[main] ✅ 上午看盤推播完成")
        return True
    except Exception as e:
        error_message = f"[main] ❌ 上午看盤推播失敗：{e}"
        print(error_message)
        
        # 系統錯誤也通知用戶
        try:
            send_notification(error_message, "系統錯誤 - 上午看盤推播失敗")
        except Exception as notify_error:
            print(f"[main] ❌ 發送錯誤通知也失敗了: {notify_error}")
        
        return False


def evening_push(global_timeout=300):
    """
    盤後推播 (15:00) - 整合短線、長線、極弱股三策略
    
    參數:
    - global_timeout: 全局超時時間(秒)
    """
    print("[main] ⏳ 執行盤後推播...")
    
    try:
        # 設置超時時間
        timeout_recommendations = min(global_timeout - 30, 270)  # 預留30秒給其他操作
        print(f"[main] 設置多策略分析超時時間為 {timeout_recommendations} 秒")
        
        # 使用超時執行獲取多策略推薦
        strategies_data = run_with_timeout(
            get_multi_strategy_recommendations, 
            args=('evening',), 
            timeout_seconds=timeout_recommendations,
            default_result={"short_term": [], "long_term": [], "weak_stocks": []}
        )
        
        # 檢查是否獲取到足夠的推薦
        short_term_stocks = strategies_data.get("short_term", [])
        long_term_stocks = strategies_data.get("long_term", [])
        weak_stocks = strategies_data.get("weak_stocks", [])
        
        # 如果任一策略沒有獲取到足夠的推薦，嘗試從緩存或備用數據獲取
        if not short_term_stocks or not long_term_stocks:
            print("[main] ⚠️ 未獲取到足夠的股票推薦，嘗試從緩存獲取")
            
            # 嘗試讀取緩存
            cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
            cache_file = os.path.join(cache_dir, 'multi_strategy_evening_cache.json')
            
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                        if 'recommendations' in cache_data:
                            # 如果短線推薦不足，從緩存獲取
                            if not short_term_stocks and "short_term" in cache_data['recommendations']:
                                short_term_stocks = cache_data['recommendations']["short_term"]
                                strategies_data["short_term"] = short_term_stocks
                                print(f"[main] ✅ 從緩存獲取了 {len(short_term_stocks)} 檔短線推薦股票")
                            
                            # 如果長線推薦不足，從緩存獲取
                            if not long_term_stocks and "long_term" in cache_data['recommendations']:
                                long_term_stocks = cache_data['recommendations']["long_term"]
                                strategies_data["long_term"] = long_term_stocks
                                print(f"[main] ✅ 從緩存獲取了 {len(long_term_stocks)} 檔長線推薦股票")
                            
                            # 如果極弱谷警示不足，從緩存獲取
                            if not weak_stocks and "weak_stocks" in cache_data['recommendations']:
                                weak_stocks = cache_data['recommendations']["weak_stocks"]
                                strategies_data["weak_stocks"] = weak_stocks
                                print(f"[main] ✅ 從緩存獲取了 {len(weak_stocks)} 檔極弱股警示")
                except Exception as e:
                    print(f"[main] ⚠️ 讀取緩存推薦失敗: {e}")
        
        # 使用雙重通知系統發送綜合推薦報告
        try:
            # 使用新的综合推播功能
            send_combined_recommendations(strategies_data, "盤後")
            print("[main] ✅ 已發送多策略分析報告")
        except Exception as e:
            print(f"[main] ⚠️ 發送多策略分析報告失敗: {e}")
            # 嘗試使用備用方式通知
            error_message = f"發送多策略分析報告失敗: {e}"
            send_notification(error_message, "盤後通知錯誤")
            
        print("[main] ✅ 盤後推播完成")
        return True
    except Exception as e:
        error_message = f"[main] ❌ 盤後推播失敗：{e}"
        print(error_message)
        
        # 系統錯誤也通知用戶
        try:
            send_notification(error_message, "系統錯誤 - 盤後推播失敗")
        except Exception as notify_error:
            print(f"[main] ❌ 發送錯誤通知也失敗了: {notify_error}")
        
        return False


def manual_push(time_slot="custom", count=3):
    """
    手動推播 - 用於測試或臨時推播
    
    參數:
    - time_slot: 時段名稱
    - count: 推薦股票數量
    """
    print(f"[main] ⏳ 執行手動推播 ({time_slot})...")
    
    try:
        # 使用超時執行獲取多策略推薦
        strategies_data = run_with_timeout(
            get_multi_strategy_recommendations, 
            args=(time_slot, count), 
            timeout_seconds=300,
            default_result={"short_term": [], "long_term": [], "weak_stocks": []}
        )
        
        # 使用雙重通知系統發送綜合推薦報告
        try:
            send_combined_recommendations(strategies_data, f"手動({time_slot})")
            print("[main] ✅ 已發送多策略分析報告")
        except Exception as e:
            print(f"[main] ⚠️ 發送多策略分析報告失敗: {e}")
            # 嘗試使用備用方式通知
            error_message = f"發送多策略分析報告失敗: {e}"
            send_notification(error_message, "手動推播錯誤")
            
        print("[main] ✅ 手動推播完成")
        return True
    except Exception as e:
        error_message = f"[main] ❌ 手動推播失敗：{e}"
        print(error_message)
        
        # 系統錯誤也通知用戶
        try:
            send_notification(error_message, "系統錯誤 - 手動推播失敗")
        except Exception as notify_error:
            print(f"[main] ❌ 發送錯誤通知也失敗了: {notify_error}")
        
        return False


def run_push_task(task_name):
    """
    運行指定的推播任務
    
    參數:
    - task_name: 任務名稱
    """
    # 設置全局超時處理
    def timeout_handler(signum, frame):
        raise TimeoutError(f"推播任務 {task_name} 執行超時")
    
    # 啟動超時計時器
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)  # 設置全局超時時間
    
    print(f"[main] 🚀 開始執行 {task_name} 推播任務")
    start_time = datetime.now()
    
    try:
        # 依據任務名稱執行不同的推播功能
        if task_name == "morning":
            result = morning_push(global_timeout=TIMEOUT_SECONDS)
        elif task_name == "noon":
            result = noon_push(global_timeout=TIMEOUT_SECONDS)
        elif task_name == "afternoon":
            result = afternoon_push(global_timeout=TIMEOUT_SECONDS)
        elif task_name == "evening":
            result = evening_push(global_timeout=TIMEOUT_SECONDS)
        elif task_name == "manual":
            result = manual_push()
        else:
            print(f"[main] ❌ 未知的推播任務: {task_name}")
            return False
        
        # 計算執行時間
        elapsed_time = (datetime.now() - start_time).total_seconds()
        print(f"[main] ✅ {task_name} 推播任務執行完成，耗時 {elapsed_time:.2f} 秒")
        
        return result
    except TimeoutError as e:
        print(f"[main] ❌ {task_name} 推播任務執行超時: {e}")
        # 嘗試通知用戶
        try:
            send_notification(f"{task_name} 推播任務執行超時", "系統錯誤 - 推播超時")
        except Exception:
            pass
        return False
    except Exception as e:
        print(f"[main] ❌ {task_name} 推播任務執行失敗: {e}")
        traceback.print_exc()
        # 嘗試通知用戶
        try:
            send_notification(f"{task_name} 推播任務執行失敗: {e}", "系統錯誤 - 推播失敗")
        except Exception:
            pass
        return False
    finally:
        # 關閉超時計時器
        signal.alarm(0)


if __name__ == "__main__":
    # 從命令行參數獲取任務名稱
    task_name = "manual"  # 默認為手動推播
    if len(sys.argv) > 1:
        task_name = sys.argv[1].lower()
    
    # 運行推播任務
    success = run_push_task(task_name)
    
    # 設置退出代碼
    sys.exit(0 if success else 1)

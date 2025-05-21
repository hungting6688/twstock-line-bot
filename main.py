"""
main.py 的主要更新部分（關鍵函數）
"""

def run_with_timeout(func, args=(), kwargs=None, timeout_seconds=300, default_result=None):
    """
    在超時限制內運行函數，增強版本
    
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
            # 記錄超時事件
            log_error(f"函數 {func.__name__} 執行超時({timeout_seconds}秒)", args, kwargs)
        except Exception as e:
            print(f"[main] ❌ 函數 {func.__name__} 執行失敗: {e}")
            traceback.print_exc()
            # 記錄錯誤
            log_error(f"函數 {func.__name__} 執行失敗: {e}", args, kwargs, traceback.format_exc())
    
    return result

def log_error(message, args=None, kwargs=None, traceback_str=None):
    """記錄錯誤到日誌文件"""
    try:
        # 確保日誌目錄存在
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 錯誤日誌文件
        log_file = os.path.join(log_dir, 'errors.log')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"===== {timestamp} =====\n")
            f.write(f"錯誤: {message}\n")
            
            if args:
                f.write(f"參數: {args}\n")
            
            if kwargs:
                f.write(f"關鍵字參數: {kwargs}\n")
            
            if traceback_str:
                f.write(f"堆疊追蹤:\n{traceback_str}\n")
            
            f.write("="*50 + "\n\n")
    except Exception as e:
        print(f"[main] ❌ 無法記錄錯誤: {e}")

def morning_push(global_timeout=240):
    """
    早盤前推播 (9:00) - 整合短線、長線、極弱股三策略
    增強版本
    
    參數:
    - global_timeout: 全局超時時間(秒)
    """
    print("[main] ⏳ 執行早盤前推播...")
    
    start_time = datetime.now()
    
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
                    log_error(f"讀取緩存推薦失敗: {e}")
        
        # 檢查最終獲取的推薦數量
        final_short_term_count = len(strategies_data.get("short_term", []))
        final_long_term_count = len(strategies_data.get("long_term", []))
        final_weak_stocks_count = len(strategies_data.get("weak_stocks", []))
        
        # 記錄執行結果
        elapsed_time = (datetime.now() - start_time).total_seconds()
        result_summary = (
            f"早盤前推播完成 - 耗時: {elapsed_time:.1f} 秒, "
            f"短線: {final_short_term_count} 檔, "
            f"長線: {final_long_term_count} 檔, "
            f"極弱股: {final_weak_stocks_count} 檔"
        )
        print(f"[main] ℹ️ {result_summary}")
        
        # 使用雙重通知系統發送綜合推薦報告
        try:
            # 使用新的综合推播功能
            send_combined_recommendations(strategies_data, "早盤前")
            print("[main] ✅ 已發送多策略分析報告")
        except Exception as e:
            print(f"[main] ⚠️ 發送多策略分析報告失敗: {e}")
            traceback.print_exc()
            log_error(f"發送多策略分析報告失敗: {e}", traceback_str=traceback.format_exc())
            
            # 嘗試使用備用方式通知
            error_message = f"發送多策略分析報告失敗: {e}"
            send_notification(error_message, "早盤前通知錯誤")
            
        print("[main] ✅ 早盤前推播完成")
        return True
    except Exception as e:
        error_message = f"[main] ❌ 早盤前推播失敗：{e}"
        print(error_message)
        traceback.print_exc()
        log_error(f"早盤前推播失敗: {e}", traceback_str=traceback.format_exc())
        
        # 系統錯誤也通知用戶
        try:
            send_notification(error_message, "系統錯誤 - 早盤前推播失敗")
        except Exception as notify_error:
            print(f"[main] ❌ 發送錯誤通知也失敗了: {notify_error}")
            log_error(f"發送錯誤通知失敗: {notify_error}")
        
        return False

# 其它 noon_push(), afternoon_push(), evening_push() 函數也做相同的更新

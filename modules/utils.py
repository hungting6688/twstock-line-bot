"""
工具函數模組 - 提供緩存管理和系統診斷功能
"""
print("[utils] ✅ 已載入工具模組")

import os
import glob
import json
import time
import random
import datetime
import requests
import shutil
import sys
import importlib

# 設定緩存目錄位置
CACHE_DIR = os.path.join(os.path.dirname(__file__), '../cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def clear_cache(file_pattern="*.json", days_old=None):
    """
    清理緩存文件
    
    參數:
    - file_pattern: 要刪除的文件模式 (例如 "*.json")
    - days_old: 只刪除指定天數以上的文件，None 表示刪除所有符合模式的文件
    
    返回:
    - (int, int): 成功刪除的文件數量，失敗的文件數量
    """
    success = 0
    failure = 0

    # 確保緩存目錄存在
    if not os.path.exists(CACHE_DIR):
        print(f"[utils] ⚠️ 緩存目錄不存在: {CACHE_DIR}")
        return success, failure

    # 取得符合模式的所有緩存文件
    cache_files = glob.glob(os.path.join(CACHE_DIR, file_pattern))
    
    if not cache_files:
        print(f"[utils] ℹ️ 找不到符合模式的緩存文件: {file_pattern}")
        return success, failure
    
    now = datetime.datetime.now()
    
    for cache_file in cache_files:
        try:
            # 檢查文件修改時間
            if days_old is not None:
                file_modified = datetime.datetime.fromtimestamp(os.path.getmtime(cache_file))
                days_diff = (now - file_modified).days
                
                if days_diff < days_old:
                    continue  # 跳過不夠舊的文件
            
            # 刪除文件
            os.remove(cache_file)
            print(f"[utils] ✅ 已刪除緩存檔案: {os.path.basename(cache_file)}")
            success += 1
            
        except Exception as e:
            print(f"[utils] ⚠️ 無法刪除緩存檔案 {os.path.basename(cache_file)}: {e}")
            failure += 1
    
    print(f"[utils] 緩存清理完成: {success} 個文件已刪除，{failure} 個文件刪除失敗")
    return success, failure

def check_network_connectivity(targets=None, timeout=5):
    """
    檢查網路連線狀態
    
    參數:
    - targets: 要檢查的網站列表，None 則使用預設列表
    - timeout: 連線逾時時間 (秒)
    
    返回:
    - dict: 連線結果字典
    """
    if targets is None:
        targets = [
            "https://www.twse.com.tw",          # 台灣證券交易所
            "https://mops.twse.com.tw",          # 公開資訊觀測站
            "https://isin.twse.com.tw",          # 證券代號查詢系統
            "https://finance.yahoo.com",         # Yahoo Finance
            "https://www.google.com"             # Google (連線測試基準)
        ]
    
    results = {}
    
    print("[utils] 📡 網路連線診斷:")
    for url in targets:
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout)
            latency = time.time() - start_time
            
            results[url] = {
                "status": response.status_code,
                "latency": round(latency, 2),
                "success": response.status_code == 200
            }
            
            status = "✅" if results[url]["success"] else "❌"
            print(f"  {status} {url}: {response.status_code} (延遲: {results[url]['latency']}秒)")
            
        except Exception as e:
            results[url] = {
                "status": "error",
                "latency": None,
                "success": False,
                "error": str(e)
            }
            print(f"  ❌ {url}: 連線失敗 ({str(e)})")
    
    # 計算連線成功率
    success_count = sum(1 for r in results.values() if r["success"])
    success_rate = (success_count / len(targets)) * 100
    
    print(f"[utils] 網路連線成功率: {success_rate:.1f}% ({success_count}/{len(targets)})")
    
    # 返回連線狀態和是否全部成功
    return {
        "results": results,
        "success_rate": success_rate,
        "all_success": all(r["success"] for r in results.values())
    }

def create_cache_file(key, data, expiry_hours=24):
    """
    創建緩存文件
    
    參數:
    - key: 緩存鍵名
    - data: 要儲存的數據
    - expiry_hours: 過期時間 (小時)
    
    返回:
    - bool: 是否成功創建
    """
    try:
        cache_file = os.path.join(CACHE_DIR, f"{key}.json")
        
        cache_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "expiry": (datetime.datetime.now() + datetime.timedelta(hours=expiry_hours)).isoformat(),
            "data": data
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
        print(f"[utils] ✅ 已創建緩存文件: {key}.json")
        return True
        
    except Exception as e:
        print(f"[utils] ❌ 創建緩存文件失敗 ({key}): {e}")
        return False

def get_cache_file(key, default=None):
    """
    讀取緩存文件
    
    參數:
    - key: 緩存鍵名
    - default: 當緩存不存在或已過期時返回的默認值
    
    返回:
    - 緩存的數據，或者默認值
    """
    try:
        cache_file = os.path.join(CACHE_DIR, f"{key}.json")
        
        if not os.path.exists(cache_file):
            return default
            
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            
        # 檢查過期時間
        if "expiry" in cache_data:
            expiry_time = datetime.datetime.fromisoformat(cache_data["expiry"])
            
            if datetime.datetime.now() > expiry_time:
                print(f"[utils] ⚠️ 緩存已過期: {key}.json")
                return default
                
        print(f"[utils] ✅ 使用緩存: {key}.json")
        return cache_data.get("data", default)
        
    except Exception as e:
        print(f"[utils] ❌ 讀取緩存文件失敗 ({key}): {e}")
        return default

def check_module_dependencies():
    """
    檢查所需模組是否已安裝
    
    返回:
    - dict: 模組檢查結果
    """
    required_modules = [
        "pandas",
        "numpy",
        "requests",
        "bs4",
        "yfinance",
        "tqdm"
    ]
    
    results = {}
    print("[utils] 檢查模組依賴...")
    
    for module_name in required_modules:
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, "__version__", "未知")
            results[module_name] = {
                "installed": True,
                "version": version
            }
            print(f"  ✅ {module_name}: v{version}")
        except ImportError:
            results[module_name] = {
                "installed": False,
                "version": None
            }
            print(f"  ❌ {module_name}: 未安裝")
    
    # 檢查所有模組是否都已安裝
    all_installed = all(r["installed"] for r in results.values())
    
    if all_installed:
        print("[utils] ✅ 所有必要模組已安裝")
    else:
        missing = [name for name, result in results.items() if not result["installed"]]
        print(f"[utils] ⚠️ 缺少以下模組: {', '.join(missing)}")
        print("[utils] 請使用 pip install -r requirements.txt 安裝缺少的模組")
    
    return {
        "results": results,
        "all_installed": all_installed
    }

def check_system_health():
    """
    全面檢查系統健康狀態 (網路、模組、緩存目錄)
    
    返回:
    - dict: 系統健康狀態
    """
    print(f"[utils] 🔍 開始檢查系統健康狀態...")
    
    # 檢查 Python 版本
    python_version = sys.version
    print(f"[utils] Python 版本: {python_version}")
    
    # 檢查模組依賴
    module_check = check_module_dependencies()
    
    # 檢查網路連接
    network_check = check_network_connectivity()
    
    # 檢查緩存目錄
    cache_status = {"exists": False, "writeable": False, "size": 0, "files": 0}
    
    if os.path.exists(CACHE_DIR):
        cache_status["exists"] = True
        
        # 檢查目錄是否可寫
        test_file = os.path.join(CACHE_DIR, f"test_{random.randint(1000, 9999)}.tmp")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            cache_status["writeable"] = True
        except:
            cache_status["writeable"] = False
        
        # 計算緩存大小和文件數量
        try:
            cache_files = os.listdir(CACHE_DIR)
            cache_status["files"] = len(cache_files)
            
            total_size = 0
            for file_name in cache_files:
                file_path = os.path.join(CACHE_DIR, file_name)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
            
            cache_status["size"] = total_size
            cache_size_mb = total_size / (1024 * 1024)
            
            print(f"[utils] 緩存狀態: {cache_status['files']} 個文件, {cache_size_mb:.2f} MB")
        except Exception as e:
            print(f"[utils] ⚠️ 無法計算緩存大小: {e}")
    else:
        print(f"[utils] ⚠️ 緩存目錄不存在: {CACHE_DIR}")
    
    # 整體系統健康評估
    system_healthy = (
        module_check["all_installed"] and
        network_check["success_rate"] >= 60 and  # 至少有 60% 的網站可以連接
        cache_status["exists"] and
        cache_status["writeable"]
    )
    
    health_status = "✅ 健康" if system_healthy else "⚠️ 有問題"
    print(f"[utils] 系統健康狀態: {health_status}")
    
    return {
        "status": system_healthy,
        "python_version": python_version,
        "modules": module_check,
        "network": network_check,
        "cache": cache_status,
        "timestamp": datetime.datetime.now().isoformat()
    }

def backup_cache():
    """
    備份緩存目錄
    
    返回:
    - str: 備份文件路徑，或者 None 表示失敗
    """
    if not os.path.exists(CACHE_DIR) or not os.listdir(CACHE_DIR):
        print("[utils] ⚠️ 緩存目錄不存在或為空，無需備份")
        return None
    
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"cache_backup_{timestamp}.zip"
        backup_path = os.path.join(os.path.dirname(CACHE_DIR), backup_file)
        
        # 創建 ZIP 備份
        shutil.make_archive(
            os.path.splitext(backup_path)[0],  # 不包含擴展名的路徑
            'zip',                             # 壓縮格式
            CACHE_DIR                         # 要壓縮的目錄
        )
        
        print(f"[utils] ✅ 已創建緩存備份: {backup_file}")
        return backup_path
        
    except Exception as e:
        print(f"[utils] ❌ 創建緩存備份失敗: {e}")
        return None

def restore_cache_backup(backup_path):
    """
    從備份檔案恢復緩存
    
    參數:
    - backup_path: 備份文件路徑
    
    返回:
    - bool: 是否成功恢復
    """
    if not os.path.exists(backup_path):
        print(f"[utils] ❌ 備份檔案不存在: {backup_path}")
        return False
    
    try:
        # 重建緩存目錄
        if os.path.exists(CACHE_DIR):
            shutil.rmtree(CACHE_DIR)
        os.makedirs(CACHE_DIR)
        
        # 解壓縮備份檔案
        shutil.unpack_archive(backup_path, CACHE_DIR)
        
        print(f"[utils] ✅ 已從備份恢復緩存: {os.path.basename(backup_path)}")
        return True
        
    except Exception as e:
        print(f"[utils] ❌ 恢復緩存失敗: {e}")
        return False

def log_system_status():
    """
    記錄系統狀態到日誌檔案
    
    返回:
    - str: 日誌檔案路徑
    """
    try:
        log_dir = os.path.join(os.path.dirname(__file__), '../logs')
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"system_status_{timestamp}.json")
        
        # 獲取系統健康狀態
        status = check_system_health()
        
        # 寫入日誌檔案
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
            
        print(f"[utils] ✅ 已記錄系統狀態: {os.path.basename(log_file)}")
        return log_file
        
    except Exception as e:
        print(f"[utils] ❌ 記錄系統狀態失敗: {e}")
        return None

# 當模組被直接執行時
if __name__ == "__main__":
    print("台股分析系統工具模組")
    print("=" * 50)
    
    # 基於命令列參數執行功能
    import argparse
    
    parser = argparse.ArgumentParser(description='系統工具命令')
    parser.add_argument('--check', action='store_true', help='檢查系統健康狀態')
    parser.add_argument('--clear-cache', action='store_true', help='清理緩存')
    parser.add_argument('--backup', action='store_true', help='備份緩存')
    parser.add_argument('--restore', type=str, help='從指定備份檔案恢復緩存')
    parser.add_argument('--network', action='store_true', help='檢查網路連接')
    
    args = parser.parse_args()
    
    if args.check:
        check_system_health()
    elif args.clear_cache:
        clear_cache()
    elif args.backup:
        backup_cache()
    elif args.restore:
        restore_cache_backup(args.restore)
    elif args.network:
        check_network_connectivity()
    else:
        # 如果沒有參數，顯示幫助信息
        parser.print_help()

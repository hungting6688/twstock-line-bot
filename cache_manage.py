#!/usr/bin/env python3
"""
緩存管理工具 - 用於列出、備份和清理緩存
2025年版
"""

import os
import json
import glob
import time
import shutil
import argparse
from datetime import datetime, timedelta

# 設置緩存目錄
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache_backup')

def get_cache_info():
    """
    獲取緩存文件的信息
    
    返回:
    - 緩存信息的字典列表 [{文件名, 大小, 時間戳, 年齡}]
    """
    if not os.path.exists(CACHE_DIR):
        print(f"緩存目錄 {CACHE_DIR} 不存在")
        return []
    
    cache_files = glob.glob(os.path.join(CACHE_DIR, '*.json'))
    if not cache_files:
        print("沒有找到緩存文件")
        return []
    
    now = time.time()
    cache_info = []
    
    for file_path in cache_files:
        filename = os.path.basename(file_path)
        size = os.path.getsize(file_path)
        mtime = os.path.getmtime(file_path)
        age_seconds = now - mtime
        
        # 嘗試從文件中讀取時間戳
        timestamp_str = "未知"
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'timestamp' in data:
                    timestamp_str = data['timestamp']
        except:
            pass
        
        cache_info.append({
            'filename': filename,
            'size': size,
            'mtime': mtime,
            'age_seconds': age_seconds,
            'timestamp': timestamp_str
        })
    
    # 按修改時間排序
    cache_info.sort(key=lambda x: x['mtime'], reverse=True)
    
    return cache_info

def list_cache():
    """列出所有緩存文件"""
    cache_info = get_cache_info()
    
    if not cache_info:
        return
    
    print("緩存文件列表:")
    print("-" * 80)
    print(f"{'文件名':<30} {'大小(KB)':<10} {'修改時間':<20} {'年齡':<15} {'時間戳'}")
    print("-" * 80)
    
    for info in cache_info:
        mtime_str = datetime.fromtimestamp(info['mtime']).strftime('%Y-%m-%d %H:%M:%S')
        age_days = info['age_seconds'] / (24 * 3600)
        
        if age_days < 1:
            age_str = f"{int(info['age_seconds'] / 3600)}小時"
        else:
            age_str = f"{age_days:.1f}天"
        
        print(f"{info['filename']:<30} {info['size']/1024:<10.1f} {mtime_str:<20} {age_str:<15} {info['timestamp']}")

def backup_cache():
    """備份緩存文件"""
    if not os.path.exists(CACHE_DIR):
        print(f"緩存目錄 {CACHE_DIR} 不存在，無法備份")
        return False
    
    cache_files = glob.glob(os.path.join(CACHE_DIR, '*.json'))
    if not cache_files:
        print("沒有找到緩存文件，無需備份")
        return False
    
    # 創建備份目錄
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # 創建帶時間戳的備份子目錄
    backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_subdir = os.path.join(BACKUP_DIR, f'backup_{backup_timestamp}')
    os.makedirs(backup_subdir, exist_ok=True)
    
    # 備份文件
    success_count = 0
    for file_path in cache_files:
        try:
            filename = os.path.basename(file_path)
            shutil.copy2(file_path, os.path.join(backup_subdir, filename))
            success_count += 1
        except Exception as e:
            print(f"備份文件 {file_path} 失敗: {e}")
    
    print(f"成功備份 {success_count}/{len(cache_files)} 個緩存文件到 {backup_subdir}")
    return success_count > 0

def clean_old_cache(days=7):
    """
    清理過舊的緩存文件
    
    參數:
    - days: 保留的天數，超過這個天數的文件將被刪除
    """
    if not os.path.exists(CACHE_DIR):
        print(f"緩存目錄 {CACHE_DIR} 不存在，無需清理")
        return False
    
    now = time.time()
    cache_files = glob.glob(os.path.join(CACHE_DIR, '*.json'))
    
    deleted_count = 0
    excluded_files = [
        'eps_data_cache.json',        # 基本面數據
        'dividend_data_cache.json',   # 股息數據
        'twse_stocks_cache.json'      # 股票列表
    ]
    
    for file_path in cache_files:
        filename = os.path.basename(file_path)
        
        # 排除特定文件
        if filename in excluded_files:
            continue
        
        mtime = os.path.getmtime(file_path)
        age_days = (now - mtime) / (24 * 3600)
        
        if age_days > days:
            try:
                os.remove(file_path)
                deleted_count += 1
                print(f"已刪除過期緩存: {filename} (年齡: {age_days:.1f}天)")
            except Exception as e:
                print(f"刪除文件 {file_path} 失敗: {e}")
    
    print(f"清理完成，共刪除 {deleted_count} 個過期緩存文件")
    return deleted_count > 0

def run_system_check():
    """運行系統健康檢查"""
    print("開始系統健康檢查...")
    
    # 1. 檢查緩存目錄是否存在並且可讀寫
    print("\n1. 緩存目錄檢查:")
    if not os.path.exists(CACHE_DIR):
        print(f"  ❌ 緩存目錄 {CACHE_DIR} 不存在")
        try:
            os.makedirs(CACHE_DIR)
            print(f"  ✅ 已創建緩存目錄 {CACHE_DIR}")
        except Exception as e:
            print(f"  ❌ 創建緩存目錄失敗: {e}")
    else:
        print(f"  ✅ 緩存目錄 {CACHE_DIR} 存在")
        
        # 測試寫入權限
        test_file = os.path.join(CACHE_DIR, 'test_write.tmp')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print(f"  ✅ 緩存目錄可讀寫")
        except Exception as e:
            print(f"  ❌ 緩存目錄寫入測試失敗: {e}")
    
    # 2. 檢查網絡連接
    print("\n2. 網絡連接檢查:")
    import requests
    
    sites = [
        ("https://www.twse.com.tw", "台灣證交所"),
        ("https://mops.twse.com.tw", "公開資訊觀測站"),
        ("https://finance.yahoo.com", "Yahoo Finance")
    ]
    
    for url, name in sites:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"  ✅ {name} ({url}) 連接正常")
            else:
                print(f"  ⚠️ {name} ({url}) 返回狀態碼 {response.status_code}")
        except Exception as e:
            print(f"  ❌ {name} ({url}) 連接失敗: {e}")
    
    # 3. 檢查重要模組是否可導入
    print("\n3. 模組導入檢查:")
    modules_to_check = [
        ("yfinance", "股票數據獲取"),
        ("pandas", "數據處理"),
        ("numpy", "數值計算"),
        ("requests", "網絡請求"),
        ("beautifulsoup4", "網頁解析", "bs4"),
        ("concurrent.futures", "並行處理", "concurrent"),
        ("matplotlib", "圖表繪製"),
        ("LineNotify", "LINE通知", "lineNotify")
    ]
    
    for module_info in modules_to_check:
        module_name = module_info[0]
        module_desc = module_info[1]
        import_name = module_info[2] if len(module_info) > 2 else module_name
        
        try:
            __import__(import_name)
            print(f"  ✅ {module_name} ({module_desc}) 導入成功")
        except ImportError:
            print(f"  ❌ {module_name} ({module_desc}) 導入失敗")
        except Exception as e:
            print(f"  ⚠️ {module_name} ({module_desc}) 導入時出錯: {e}")
    
    # 4. 檢查環境變量
    print("\n4. 環境變量檢查:")
    env_vars = [
        ("GOOGLE_JSON_KEY", "Google服務認證"),
        ("FINMIND_TOKEN", "FinMind API Token"),
        ("LINE_CHANNEL_ACCESS_TOKEN", "LINE通知Token"),
        ("LINE_USER_ID", "LINE用戶ID"),
        ("EMAIL_SENDER", "郵件發件人"),
        ("EMAIL_PASSWORD", "郵件密碼"),
        ("EMAIL_RECEIVER", "郵件收件人")
    ]
    
    for var_name, var_desc in env_vars:
        value = os.getenv(var_name)
        if value:
            masked_value = value[:3] + '*' * (len(value) - 6) + value[-3:] if len(value) > 10 else '***'
            print(f"  ✅ {var_name} ({var_desc}) 已設置")
        else:
            print(f"  ❌ {var_name} ({var_desc}) 未設置")
    
    print("\n系統健康檢查完成")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='緩存管理工具')
    parser.add_argument('--list', action='store_true', help='列出所有緩存文件')
    parser.add_argument('--backup', action='store_true', help='備份緩存文件')
    parser.add_argument('--clean-old', type=int, metavar='DAYS', help='清理超過指定天數的緩存文件')
    parser.add_argument('--check', action='store_true', help='運行系統健康檢查')
    
    args = parser.parse_args()
    
    if args.list:
        list_cache()
    
    if args.backup:
        backup_cache()
    
    if args.clean_old is not None:
        clean_old_cache(args.clean_old)
    
    if args.check:
        run_system_check()
    
    # 如果沒有提供任何參數，顯示幫助
    if not (args.list or args.backup or args.clean_old is not None or args.check):
        parser.print_help()

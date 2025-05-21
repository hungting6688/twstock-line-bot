#!/usr/bin/env python3
"""
緩存管理工具 - 用於列出、備份和清理緩存
2025年增強版 - 支持定期備份和智能緩存管理
"""

import os
import json
import glob
import time
import shutil
import argparse
from datetime import datetime, timedelta
import hashlib
import logging
import traceback
import threading
import sys
import zipfile

# 設置緩存目錄
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
BACKUP_DIR = os.path.join(BASE_DIR, 'cache_backup')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# 確保目錄存在
for directory in [CACHE_DIR, BACKUP_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

# 設置日誌
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'cache_manage.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 緩存類型配置 - 不同類型的緩存有不同的保留期限和備份策略
CACHE_CONFIG = {
    'eps_data_cache.json': {
        'description': 'EPS 和基本財務數據緩存',
        'retention_days': 30,     # 保留天數
        'backup_interval': 7,     # 備份間隔（天）
        'backup_copies': 5,       # 保留的備份副本數量
        'critical': True,         # 是否為關鍵緩存
        'auto_clean': False       # 是否自動清理
    },
    'dividend_data_cache.json': {
        'description': '股息數據緩存',
        'retention_days': 30,
        'backup_interval': 7,
        'backup_copies': 5,
        'critical': True,
        'auto_clean': False
    },
    'twse_stocks_cache.json': {
        'description': '股票列表緩存',
        'retention_days': 90,
        'backup_interval': 30,
        'backup_copies': 3,
        'critical': True,
        'auto_clean': False
    },
    'multi_strategy_morning_cache.json': {
        'description': '早盤推薦緩存',
        'retention_days': 7,
        'backup_interval': 1,
        'backup_copies': 7,
        'critical': False,
        'auto_clean': True
    },
    'multi_strategy_afternoon_cache.json': {
        'description': '上午看盤推薦緩存',
        'retention_days': 3,
        'backup_interval': 1,
        'backup_copies': 3,
        'critical': False,
        'auto_clean': True
    },
    'multi_strategy_noon_cache.json': {
        'description': '午盤推薦緩存',
        'retention_days': 3,
        'backup_interval': 1,
        'backup_copies': 3,
        'critical': False,
        'auto_clean': True
    },
    'multi_strategy_evening_cache.json': {
        'description': '盤後分析緩存',
        'retention_days': 7,
        'backup_interval': 1,
        'backup_copies': 7,
        'critical': False,
        'auto_clean': True
    }
}

def log_event(message, level='info'):
    """記錄事件到日誌"""
    try:
        # 輸出到控制台
        if level == 'error':
            print(f"❌ {message}")
            logging.error(message)
        elif level == 'warning':
            print(f"⚠️ {message}")
            logging.warning(message)
        else:
            print(f"ℹ️ {message}")
            logging.info(message)
    except Exception as e:
        print(f"記錄日誌失敗: {e}")

def get_cache_info():
    """
    獲取緩存文件的信息
    
    返回:
    - 緩存信息的字典列表 [{文件名, 大小, 時間戳, 年齡}]
    """
    if not os.path.exists(CACHE_DIR):
        log_event(f"緩存目錄 {CACHE_DIR} 不存在", 'warning')
        return []
    
    cache_files = glob.glob(os.path.join(CACHE_DIR, '*.json'))
    if not cache_files:
        log_event("沒有找到緩存文件", 'warning')
        return []
    
    now = time.time()
    cache_info = []
    
    for file_path in cache_files:
        filename = os.path.basename(file_path)
        size = os.path.getsize(file_path)
        mtime = os.path.getmtime(file_path)
        age_seconds = now - mtime
        
        # 嘗試從文件中讀取時間戳和內容總結
        timestamp_str = "未知"
        content_summary = "未知"
        item_count = 0
        cache_type = "一般緩存"
        
        # 獲取檔案配置
        config = CACHE_CONFIG.get(filename, {
            "description": "一般緩存文件",
            "retention_days": 7,
            "backup_interval": 1,
            "backup_copies": 3,
            "critical": False,
            "auto_clean": True
        })
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 嘗試獲取時間戳
                if 'timestamp' in data:
                    timestamp_str = data['timestamp']
                
                # 嘗試獲取內容總結
                if 'data' in data and isinstance(data['data'], dict):
                    item_count = len(data['data'])
                    content_summary = f"{item_count} 項目"
                elif 'recommendations' in data and isinstance(data['recommendations'], dict):
                    strategies = data['recommendations']
                    items = sum(len(stocks) for stocks in strategies.values())
                    content_summary = f"{items} 檔股票推薦"
        except Exception as e:
            log_event(f"讀取緩存文件 {filename} 內容失敗: {e}", 'warning')
        
        # 計算 MD5 校驗和
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            file_hash = "計算失敗"
        
        cache_info.append({
            'filename': filename,
            'size': size,
            'mtime': mtime,
            'age_seconds': age_seconds,
            'timestamp': timestamp_str,
            'content_summary': content_summary,
            'item_count': item_count,
            'md5': file_hash,
            'description': config['description'],
            'retention_days': config['retention_days'],
            'critical': config['critical']
        })
    
    # 按修改時間排序
    cache_info.sort(key=lambda x: x['mtime'], reverse=True)
    
    return cache_info

def list_cache(verbose=False):
    """
    列出所有緩存文件
    
    參數:
    - verbose: 是否顯示詳細信息
    """
    cache_info = get_cache_info()
    
    if not cache_info:
        log_event("沒有找到緩存文件", 'warning')
        return
    
    print("\n緩存文件列表:")
    print("-" * 100)
    
    if verbose:
        print(f"{'文件名':<30} {'大小(KB)':<10} {'修改時間':<20} {'年齡':<15} {'項目數':<10} {'描述':<30}")
        print("-" * 100)
        
        for info in cache_info:
            mtime_str = datetime.fromtimestamp(info['mtime']).strftime('%Y-%m-%d %H:%M:%S')
            age_days = info['age_seconds'] / (24 * 3600)
            
            if age_days < 1:
                age_str = f"{int(info['age_seconds'] / 3600)}小時"
            else:
                age_str = f"{age_days:.1f}天"
            
            # 增加文件狀態指示
            is_critical = "🔒" if info['critical'] else ""
            
            print(f"{info['filename']:<30} {info['size']/1024:<10.1f} {mtime_str:<20} {age_str:<15} {info['item_count']:<10} {info['description']}{is_critical}")
    else:
        print(f"{'文件名':<30} {'大小(KB)':<10} {'修改時間':<20} {'年齡':<15}")
        print("-" * 80)
        
        for info in cache_info:
            mtime_str = datetime.fromtimestamp(info['mtime']).strftime('%Y-%m-%d %H:%M:%S')
            age_days = info['age_seconds'] / (24 * 3600)
            
            if age_days < 1:
                age_str = f"{int(info['age_seconds'] / 3600)}小時"
            else:
                age_str = f"{age_days:.1f}天"
            
            print(f"{info['filename']:<30} {info['size']/1024:<10.1f} {mtime_str:<20} {age_str:<15}")
    
    # 計算總佔用空間
    total_size = sum(info['size'] for info in cache_info)
    print(f"\n總計: {len(cache_info)} 個緩存文件，總共佔用 {total_size/1024/1024:.2f} MB 磁碟空間")

def backup_cache(specific_file=None):
    """
    備份緩存文件
    
    參數:
    - specific_file: 指定要備份的文件名，None表示備份所有文件
    
    返回:
    - bool: 是否成功備份
    """
    if not os.path.exists(CACHE_DIR):
        log_event(f"緩存目錄 {CACHE_DIR} 不存在，無法備份", 'error')
        return False
    
    # 如果指定了文件，檢查文件是否存在
    if specific_file:
        file_path = os.path.join(CACHE_DIR, specific_file)
        if not os.path.exists(file_path):
            log_event(f"指定的文件 {specific_file} 不存在，無法備份", 'error')
            return False
        cache_files = [file_path]
    else:
        cache_files = glob.glob(os.path.join(CACHE_DIR, '*.json'))
    
    if not cache_files:
        log_event("沒有找到緩存文件，無需備份", 'warning')
        return False
    
    # 創建備份目錄
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # 創建帶時間戳的備份子目錄
    backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_subdir = os.path.join(BACKUP_DIR, f'backup_{backup_timestamp}')
    os.makedirs(backup_subdir, exist_ok=True)
    
    # 備份文件
    success_count = 0
    backup_details = []
    
    for file_path in cache_files:
        try:
            filename = os.path.basename(file_path)
            
            # 檢查文件是否為空或損壞
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                log_event(f"跳過空文件 {filename}", 'warning')
                continue
                
            try:
                # 嘗試讀取文件確認是否為有效的JSON
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
            except json.JSONDecodeError:
                log_event(f"跳過無效的JSON文件 {filename}", 'warning')
                continue
            
            # 複製文件到備份目錄
            dest_path = os.path.join(backup_subdir, filename)
            shutil.copy2(file_path, dest_path)
            
            # 計算備份文件的MD5校驗和
            with open(dest_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            # 記錄備份詳情
            backup_details.append({
                'filename': filename,
                'original_path': file_path,
                'backup_path': dest_path,
                'size': file_size,
                'md5': file_hash,
                'backup_time': datetime.now().isoformat()
            })
            
            success_count += 1
            log_event(f"成功備份 {filename}")
            
        except Exception as e:
            log_event(f"備份文件 {file_path} 失敗: {e}", 'error')
    
    # 創建備份索引文件
    if backup_details:
        try:
            index_file = os.path.join(backup_subdir, 'backup_index.json')
            with open(index_file, 'w', encoding='utf-8') as f:
                backup_index = {
                    'timestamp': datetime.now().isoformat(),
                    'backup_id': backup_timestamp,
                    'files': backup_details
                }
                json.dump(backup_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_event(f"創建備份索引失敗: {e}", 'warning')
    
    # 建立壓縮備份
    try:
        zip_file = os.path.join(BACKUP_DIR, f'backup_{backup_timestamp}.zip')
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_subdir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, backup_subdir)
                    zipf.write(file_path, arcname)
        log_event(f"已創建壓縮備份: {zip_file}")
    except Exception as e:
        log_event(f"創建壓縮備份失敗: {e}", 'warning')
    
    log_event(f"成功備份 {success_count}/{len(cache_files)} 個緩存文件到 {backup_subdir}")
    return success_count > 0

def clean_old_cache(days=None, force=False):
    """
    清理過舊的緩存文件
    
    參數:
    - days: 保留的天數，None表示使用每個文件的配置
    - force: 是否強制清理（包括關鍵緩存）
    
    返回:
    - int: 刪除的文件數量
    """
    if not os.path.exists(CACHE_DIR):
        log_event(f"緩存目錄 {CACHE_DIR} 不存在，無需清理", 'warning')
        return 0
    
    now = time.time()
    cache_files = glob.glob(os.path.join(CACHE_DIR, '*.json'))
    
    deleted_count = 0
    
    for file_path in cache_files:
        filename = os.path.basename(file_path)
        
        # 獲取文件配置
        config = CACHE_CONFIG.get(filename, {
            "description": "一般緩存文件",
            "retention_days": 7,
            "critical": False,
            "auto_clean": True
        })
        
        # 如果文件是關鍵緩存且不強制清理，則跳過
        if config['critical'] and not force:
            log_event(f"跳過關鍵緩存文件: {filename}")
            continue
        
        # 確定保留天數
        retention_days = days if days is not None else config['retention_days']
        
        # 檢查文件年齡
        mtime = os.path.getmtime(file_path)
        age_days = (now - mtime) / (24 * 3600)
        
        if age_days > retention_days:
            try:
                # 在刪除前先進行一次備份
                backup_single_file(filename)
                
                # 刪除文件
                os.remove(file_path)
                deleted_count += 1
                log_event(f"已刪除過期緩存: {filename} (年齡: {age_days:.1f}天)")
            except Exception as e:
                log_event(f"刪除文件 {file_path} 失敗: {e}", 'error')
    
    log_event(f"清理完成，共刪除 {deleted_count} 個過期緩存文件")
    return deleted_count

def backup_single_file(filename):
    """
    備份單個緩存文件
    
    參數:
    - filename: 文件名
    
    返回:
    - bool: 是否成功備份
    """
    try:
        file_path = os.path.join(CACHE_DIR, filename)
        if not os.path.exists(file_path):
            log_event(f"文件 {filename} 不存在，無法備份", 'warning')
            return False
        
        # 創建備份目錄
        file_backup_dir = os.path.join(BACKUP_DIR, filename.replace('.json', ''))
        os.makedirs(file_backup_dir, exist_ok=True)
        
        # 創建帶時間戳的備份文件名
        backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(file_backup_dir, f"{filename.replace('.json', '')}_{backup_timestamp}.json")
        
        # 複製文件
        shutil.copy2(file_path, backup_file)
        log_event(f"已備份 {filename} 到 {backup_file}")
        
        # 維護備份的版本數量
        config = CACHE_CONFIG.get(filename, {
            "backup_copies": 3
        })
        max_copies = config.get("backup_copies", 3)
        
        # 獲取該文件的所有備份
        backups = glob.glob(os.path.join(file_backup_dir, f"{filename.replace('.json', '')}*.json"))
        backups.sort(key=os.path.getmtime, reverse=True)
        
        # 如果備份數量超過限制，刪除最舊的備份
        if len(backups) > max_copies:
            for old_backup in backups[max_copies:]:
                os.remove(old_backup)
                log_event(f"已刪除過舊的備份: {os.path.basename(old_backup)}")
        
        return True
    except Exception as e:
        log_event(f"備份文件 {filename} 失敗: {e}", 'error')
        return False

def run_system_check():
    """運行系統健康檢查"""
    log_event("開始系統健康檢查...")
    
    # 1. 檢查緩存目錄是否存在並且可讀寫
    log_event("\n1. 緩存目錄檢查:")
    if not os.path.exists(CACHE_DIR):
        log_event(f"緩存目錄 {CACHE_DIR} 不存在", 'warning')
        try:
            os.makedirs(CACHE_DIR)
            log_event(f"已創建緩存目錄 {CACHE_DIR}")
        except Exception as e:
            log_event(f"創建緩存目錄失敗: {e}", 'error')
    else:
        log_event(f"緩存目錄 {CACHE_DIR} 存在")
        
        # 測試寫入權限
        test_file = os.path.join(CACHE_DIR, 'test_write.tmp')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            log_event(f"緩存目錄可讀寫")
        except Exception as e:
            log_event(f"緩存目錄寫入測試失敗: {e}", 'error')
    
    # 2. 檢查備份目錄
    log_event("\n2. 備份目錄檢查:")
    if not os.path.exists(BACKUP_DIR):
        log_event(f"備份目錄 {BACKUP_DIR} 不存在", 'warning')
        try:
            os.makedirs(BACKUP_DIR)
            log_event(f"已創建備份目錄 {BACKUP_DIR}")
        except Exception as e:
            log_event(f"創建備份目錄失敗: {e}", 'error')
    else:
        log_event(f"備份目錄 {BACKUP_DIR} 存在")
        
        # 測試寫入權限
        test_file = os.path.join(BACKUP_DIR, 'test_write.tmp')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            log_event(f"備份目錄可讀寫")
        except Exception as e:
            log_event(f"備份目錄寫入測試失敗: {e}", 'error')
    
    # 3. 檢查緩存文件
    log_event("\n3. 緩存文件檢查:")
    cache_info = get_cache_info()
    if not cache_info:
        log_event("沒有找到緩存文件", 'warning')
    else:
        log_event(f"找到 {len(cache_info)} 個緩存文件")
        
        # 檢查關鍵緩存文件
        critical_files = [name for name, config in CACHE_CONFIG.items() if config.get('critical', False)]
        for filename in critical_files:
            file_path = os.path.join(CACHE_DIR, filename)
            if os.path.exists(file_path):
                # 檢查文件內容是否為有效的JSON
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    log_event(f"關鍵緩存 {filename} 存在且有效")
                except Exception as e:
                    log_event(f"關鍵緩存 {filename} 內容無效: {e}", 'error')
            else:
                log_event(f"關鍵緩存 {filename} 不存在", 'warning')
    
    # 4. 檢查磁盤空間
    log_event("\n4. 磁盤空間檢查:")
    try:
        import shutil
        total, used, free = shutil.disk_usage(BASE_DIR)
        free_gb = free / (1024**3)
        used_percent = used / total * 100
        
        log_event(f"總磁盤空間: {total / (1024**3):.2f} GB")
        log_event(f"已使用空間: {used / (1024**3):.2f} GB ({used_percent:.1f}%)")
        log_event(f"剩餘空間: {free_gb:.2f} GB")
        
        if free_gb < 1:
            log_event(f"磁盤空間不足，僅剩 {free_gb:.2f} GB", 'warning')
    except Exception as e:
        log_event(f"檢查磁盤空間失敗: {e}", 'error')
    
    log_event("\n系統健康檢查完成")

def auto_cleanup_backups():
    """
    自動清理過舊的備份
    
    返回:
    - int: 刪除的備份數量
    """
    if not os.path.exists(BACKUP_DIR):
        log_event(f"備份目錄 {BACKUP_DIR} 不存在，無需清理", 'warning')
        return 0
    
    # 獲取所有備份子目錄
    backup_dirs = [d for d in os.listdir(BACKUP_DIR) 
                   if os.path.isdir(os.path.join(BACKUP_DIR, d)) and d.startswith('backup_')]
    
    # 獲取所有壓縮備份
    backup_zips = [f for f in os.listdir(BACKUP_DIR) 
                   if os.path.isfile(os.path.join(BACKUP_DIR, f)) and f.startswith('backup_') and f.endswith('.zip')]
    
    # 保留的備份數量
    max_backups = 10
    
    # 刪除過舊的子目錄備份
    deleted_dirs = 0
    if len(backup_dirs) > max_backups:
        # 按時間排序
        backup_dirs.sort(key=lambda d: os.path.getmtime(os.path.join(BACKUP_DIR, d)), reverse=True)
        
        # 刪除多餘的備份
        for old_dir in backup_dirs[max_backups:]:
            dir_path = os.path.join(BACKUP_DIR, old_dir)
            try:
                shutil.rmtree(dir_path)
                deleted_dirs += 1
                log_event(f"已刪除過舊的備份目錄: {old_dir}")
            except Exception as e:
                log_event(f"刪除備份目錄 {old_dir} 失敗: {e}", 'error')
    
    # 刪除過舊的壓縮備份
    deleted_zips = 0
    if len(backup_zips) > max_backups:
        # 按時間排序
        backup_zips.sort(key=lambda f: os.path.getmtime(os.path.join(BACKUP_DIR, f)), reverse=True)
        
        # 刪除多餘的備份
        for old_zip in backup_zips[max_backups:]:
            zip_path = os.path.join(BACKUP_DIR, old_zip)
            try:
                os.remove(zip_path)
                deleted_zips += 1
                log_event(f"已刪除過舊的壓縮備份: {old_zip}")
            except Exception as e:
                log_event(f"刪除壓縮備份 {old_zip} 失敗: {e}", 'error')
    
    log_event(f"清理完成，共刪除 {deleted_dirs} 個備份目錄和 {deleted_zips} 個壓縮備份")
    return deleted_dirs + deleted_zips

def restore_backup(backup_id=None, filename=None):
    """
    從備份恢復緩存文件
    
    參數:
    - backup_id: 備份ID（時間戳），None表示最新的備份
    - filename: 要恢復的文件名，None表示所有文件
    
    返回:
    - bool: 是否成功恢復
    """
    if not os.path.exists(BACKUP_DIR):
        log_event(f"備份目錄 {BACKUP_DIR} 不存在，無法恢復", 'error')
        return False
    
    # 查找備份目錄
    backup_dirs = [d for d in os.listdir(BACKUP_DIR) 
                  if os.path.isdir(os.path.join(BACKUP_DIR, d)) and d.startswith('backup_')]
    
    if not backup_dirs:
        log_event("沒有找到備份目錄", 'error')
        return False
    
    # 如果沒有指定備份ID，使用最新的備份
    if backup_id is None:
        backup_dirs.sort(key=lambda d: os.path.getmtime(os.path.join(BACKUP_DIR, d)), reverse=True)
        backup_id = backup_dirs[0].replace('backup_', '')
    
    backup_dir = os.path.join(BACKUP_DIR, f'backup_{backup_id}')
    if not os.path.exists(backup_dir):
        log_event(f"指定的備份目錄 {backup_dir} 不存在", 'error')
        return False
    
    # 獲取備份索引文件
    index_file = os.path.join(backup_dir, 'backup_index.json')
    if os.path.exists(index_file):
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                backup_index = json.load(f)
            log_event(f"讀取備份索引成功，備份於 {backup_index.get('timestamp', '未知時間')}")
        except Exception as e:
            log_event(f"讀取備份索引失敗: {e}", 'warning')
            backup_index = None
    else:
        backup_index = None
    
    # 獲取備份文件列表
    if filename:
        backup_files = [os.path.join(backup_dir, filename)]
        if not os.path.exists(backup_files[0]):
            log_event(f"指定的備份文件 {filename} 不存在於備份 {backup_id}", 'error')
            return False
    else:
        backup_files = [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) 
                        if os.path.isfile(os.path.join(backup_dir, f)) and f.endswith('.json') and f != 'backup_index.json']
    
    if not backup_files:
        log_event(f"備份 {backup_id} 中沒有找到緩存文件", 'error')
        return False
    
    # 恢復前先備份當前緩存
    current_backup_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    current_backup_dir = os.path.join(BACKUP_DIR, f'pre_restore_{current_backup_id}')
    os.makedirs(current_backup_dir, exist_ok=True)
    
    # 備份當前緩存文件
    current_files = glob.glob(os.path.join(CACHE_DIR, '*.json'))
    for file_path in current_files:
        filename = os.path.basename(file_path)
        try:
            shutil.copy2(file_path, os.path.join(current_backup_dir, filename))
            log_event(f"已備份當前緩存文件 {filename}")
        except Exception as e:
            log_event(f"備份當前緩存文件 {filename} 失敗: {e}", 'warning')
    
    # 開始恢復
    success_count = 0
    for backup_file in backup_files:
        try:
            filename = os.path.basename(backup_file)
            dest_file = os.path.join(CACHE_DIR, filename)
            
            # 複製備份文件到緩存目錄
            shutil.copy2(backup_file, dest_file)
            success_count += 1
            log_event(f"成功恢復 {filename}")
        except Exception as e:
            log_event(f"恢復文件 {os.path.basename(backup_file)} 失敗: {e}", 'error')
    
    log_event(f"恢復完成，共恢復 {success_count}/{len(backup_files)} 個緩存文件")
    return success_count > 0

def automatic_backup():
    """
    自動備份緩存文件
    
    返回:
    - bool: 是否有文件需要備份
    """
    cache_info = get_cache_info()
    
    if not cache_info:
        log_event("沒有找到緩存文件，無需備份", 'warning')
        return False
    
    files_to_backup = []
    
    # 檢查每個緩存文件
    for info in cache_info:
        filename = info['filename']
        config = CACHE_CONFIG.get(filename, {
            "backup_interval": 7,
            "critical": False
        })
        
        # 獲取上次備份時間
        file_backup_dir = os.path.join(BACKUP_DIR, filename.replace('.json', ''))
        if os.path.exists(file_backup_dir):
            backups = glob.glob(os.path.join(file_backup_dir, f"{filename.replace('.json', '')}*.json"))
            if backups:
                backups.sort(key=os.path.getmtime, reverse=True)
                last_backup_time = os.path.getmtime(backups[0])
                age_days = (time.time() - last_backup_time) / (24 * 3600)
                
                # 檢查是否需要備份
                if age_days >= config['backup_interval']:
                    files_to_backup.append(filename)
            else:
                # 沒有備份，需要備份
                files_to_backup.append(filename)
        else:
            # 備份目錄不存在，需要備份
            files_to_backup.append(filename)
    
    # 執行備份
    if files_to_backup:
        log_event(f"將自動備份 {len(files_to_backup)} 個緩存文件")
        for filename in files_to_backup:
            backup_single_file(filename)
        return True
    else:
        log_event("所有緩存文件都在備份周期內，不需要自動備份")
        return False

def cache_health_check():
    """
    執行緩存健康檢查
    
    返回:
    - dict: 緩存健康狀態報告
    """
    cache_info = get_cache_info()
    
    if not cache_info:
        return {
            "status": "warning",
            "message": "沒有找到緩存文件",
            "timestamp": datetime.now().isoformat(),
            "details": {}
        }
    
    # 初始化健康報告
    health_report = {
        "status": "ok",
        "message": "緩存狀態正常",
        "timestamp": datetime.now().isoformat(),
        "cache_count": len(cache_info),
        "total_size_kb": sum(info['size'] for info in cache_info) / 1024,
        "critical_cache": {},
        "warnings": [],
        "details": {}
    }
    
    # 檢查每個緩存文件
    for info in cache_info:
        filename = info['filename']
        config = CACHE_CONFIG.get(filename, {
            "description": "一般緩存文件",
            "retention_days": 7,
            "critical": False
        })
        
        # 基本信息
        file_health = {
            "file_size_kb": info['size'] / 1024,
            "modified": datetime.fromtimestamp(info['mtime']).isoformat(),
            "age_days": info['age_seconds'] / (24 * 3600),
            "critical": config['critical'],
            "item_count": info['item_count'],
            "status": "ok"
        }
        
        # 檢查文件的健康狀態
        if config['critical']:
            # 檢查關鍵緩存
            health_report["critical_cache"][filename] = file_health
            
            # 檢查是否過期
            if file_health["age_days"] > config['retention_days'] * 2:
                file_health["status"] = "error"
                file_health["message"] = f"關鍵緩存 {filename} 已過期 {file_health['age_days']:.1f} 天"
                health_report["warnings"].append(file_health["message"])
                health_report["status"] = "error"
            elif file_health["age_days"] > config['retention_days']:
                file_health["status"] = "warning"
                file_health["message"] = f"關鍵緩存 {filename} 接近過期 {file_health['age_days']:.1f} 天"
                health_report["warnings"].append(file_health["message"])
                if health_report["status"] != "error":
                    health_report["status"] = "warning"
        
        # 檢查文件大小是否異常
        if info['size'] < 10:
            file_health["status"] = "error"
            file_health["message"] = f"緩存文件 {filename} 可能為空或損壞 ({info['size']} 字節)"
            health_report["warnings"].append(file_health["message"])
            health_report["status"] = "error"
        
        # 檢查項目數量是否異常
        if config['critical'] and info['item_count'] < 5:
            file_health["status"] = "warning"
            file_health["message"] = f"關鍵緩存 {filename} 項目數量異常 (僅 {info['item_count']} 項)"
            health_report["warnings"].append(file_health["message"])
            if health_report["status"] != "error":
                health_report["status"] = "warning"
        
        # 添加到詳細信息
        health_report["details"][filename] = file_health
    
    # 檢查是否缺少關鍵緩存
    for filename, config in CACHE_CONFIG.items():
        if config.get('critical', False) and filename not in health_report["critical_cache"]:
            warning = f"缺少關鍵緩存 {filename}"
            health_report["warnings"].append(warning)
            health_report["status"] = "error"
    
    # 更新總體狀態消息
    if health_report["status"] == "error":
        health_report["message"] = f"緩存存在嚴重問題 ({len(health_report['warnings'])} 個警告)"
    elif health_report["status"] == "warning":
        health_report["message"] = f"緩存存在潛在問題 ({len(health_report['warnings'])} 個警告)"
    
    return health_report

def print_cache_health(report=None):
    """
    打印緩存健康報告
    
    參數:
    - report: 緩存健康報告字典，None表示重新獲取
    """
    if report is None:
        report = cache_health_check()
    
    # 打印報告頭
    status_icon = "✅" if report["status"] == "ok" else "⚠️" if report["status"] == "warning" else "❌"
    print(f"\n{status_icon} 緩存健康報告 - {report['message']}")
    print(f"生成時間: {datetime.fromisoformat(report['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"緩存文件總數: {report['cache_count']} | 總大小: {report['total_size_kb']:.1f} KB")
    print("-" * 80)
    
    # 打印警告信息
    if report["warnings"]:
        print("\n⚠️ 警告:")
        for warning in report["warnings"]:
            print(f"  - {warning}")
        print("")
    
    # 打印關鍵緩存狀態
    print("🔒 關鍵緩存狀態:")
    if report["critical_cache"]:
        for filename, info in report["critical_cache"].items():
            status = "✅" if info["status"] == "ok" else "⚠️" if info["status"] == "warning" else "❌"
            print(f"  {status} {filename} - 年齡: {info['age_days']:.1f}天, 大小: {info['file_size_kb']:.1f}KB, 項目數: {info['item_count']}")
    else:
        print("  沒有找到關鍵緩存文件")
    
    # 打印缺失的關鍵緩存
    missing_critical = []
    for filename, config in CACHE_CONFIG.items():
        if config.get('critical', False) and filename not in report["critical_cache"]:
            missing_critical.append(filename)
    
    if missing_critical:
        print("\n❌ 缺失的關鍵緩存:")
        for filename in missing_critical:
            print(f"  - {filename}")
    
    print("\n建議操作:")
    if report["status"] == "ok":
        print("  系統運行正常，無需特殊操作")
    else:
        if "error" in report["status"]:
            print("  1. 執行緩存備份: python cache_manage.py --backup")
            print("  2. 檢查並恢復缺失的關鍵緩存: python cache_manage.py --restore")
            print("  3. 運行系統健康檢查: python cache_manage.py --check")
        else:
            print("  1. 執行緩存備份: python cache_manage.py --backup")
            print("  2. 清理過期緩存: python cache_manage.py --clean-old")

def init_cache():
    """
    初始化緩存目錄和結構
    
    返回:
    - bool: 是否成功初始化
    """
    try:
        # 確保緩存目錄存在
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        # 確保備份目錄存在
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # 確保日誌目錄存在
        os.makedirs(LOG_DIR, exist_ok=True)
        
        # 創建緩存配置文件
        config_file = os.path.join(CACHE_DIR, 'cache_config.json')
        if not os.path.exists(config_file):
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(CACHE_CONFIG, f, ensure_ascii=False, indent=2)
            log_event(f"已創建緩存配置文件: {config_file}")
        
        log_event("成功初始化緩存系統")
        return True
    except Exception as e:
        log_event(f"初始化緩存系統失敗: {e}", 'error')
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='緩存管理工具')
    parser.add_argument('--list', action='store_true', help='列出所有緩存文件')
    parser.add_argument('--verbose', action='store_true', help='顯示詳細信息')
    parser.add_argument('--backup', action='store_true', help='備份緩存文件')
    parser.add_argument('--backup-file', type=str, help='備份指定的緩存文件')
    parser.add_argument('--clean-old', type=int, metavar='DAYS', help='清理超過指定天數的緩存文件')
    parser.add_argument('--force-clean', action='store_true', help='強制清理（包括關鍵緩存）')
    parser.add_argument('--check', action='store_true', help='運行系統健康檢查')
    parser.add_argument('--health', action='store_true', help='檢查緩存健康狀態')
    parser.add_argument('--restore', action='store_true', help='從最新備份恢復緩存')
    parser.add_argument('--restore-backup', type=str, help='從指定備份恢復緩存')
    parser.add_argument('--restore-file', type=str, help='恢復指定的文件')
    parser.add_argument('--cleanup-backups', action='store_true', help='清理過舊的備份')
    parser.add_argument('--auto', action='store_true', help='執行自動化維護（備份+清理）')
    parser.add_argument('--init', action='store_true', help='初始化緩存系統')
    
    args = parser.parse_args()
    
    if args.init:
        init_cache()
    
    if args.list:
        list_cache(args.verbose)
    
    if args.backup:
        backup_cache()
    
    if args.backup_file:
        backup_single_file(args.backup_file)
    
    if args.clean_old is not None:
        clean_old_cache(args.clean_old, args.force_clean)
    
    if args.check:
        run_system_check()
    
    if args.health:
        print_cache_health()
    
    if args.restore:
        restore_backup()
    
    if args.restore_backup:
        if args.restore_file:
            restore_backup(args.restore_backup, args.restore_file)
        else:
            restore_backup(args.restore_backup)
    
    if args.cleanup_backups:
        auto_cleanup_backups()
    
    if args.auto:
        # 執行自動化維護
        print("\n=== 執行自動化緩存維護 ===")
        
        # 1. 執行健康檢查
        health_report = cache_health_check()
        print_cache_health(health_report)
        
        # 2. 自動備份需要備份的文件
        automatic_backup()
        
        # 3. 清理過舊的緩存
        for filename, config in CACHE_CONFIG.items():
            if config.get('auto_clean', True):
                file_path = os.path.join(CACHE_DIR, filename)
                if os.path.exists(file_path):
                    age_days = (time.time() - os.path.getmtime(file_path)) / (24 * 3600)
                    if age_days > config.get('retention_days', 7):
                        log_event(f"自動清理過期緩存: {filename}", 'info')
                        backup_single_file(filename)  # 先備份
                        os.remove(file_path)  # 再刪除
        
        # 4. 清理過舊的備份
        auto_cleanup_backups()
        
        print("\n=== 自動維護完成 ===")
    
    # 如果沒有提供任何參數，顯示幫助
    if not any([args.list, args.backup, args.backup_file, args.clean_old is not None, 
                args.check, args.health, args.restore, args.restore_backup, 
                args.cleanup_backups, args.auto, args.init]):
        parser.print_help()

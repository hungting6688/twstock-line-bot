"""
緩存管理腳本 - 提供手動清理和優化緩存的功能
"""

import os
import sys
import argparse
import time
import json
import datetime
import shutil

# 獲取緩存目錄路徑
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# 備份目錄路徑
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'cache_backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

def list_cache_files():
    """列出所有緩存文件"""
    if not os.path.exists(CACHE_DIR):
        print(f"緩存目錄不存在: {CACHE_DIR}")
        return
    
    files = os.listdir(CACHE_DIR)
    if not files:
        print("緩存目錄為空")
        return
    
    total_size = 0
    print("\n當前緩存文件:")
    print("-" * 80)
    print(f"{'文件名':<40} {'大小':<10} {'修改時間':<20} {'年齡':<10}")
    print("-" * 80)
    
    current_time = time.time()
    for filename in sorted(files):
        file_path = os.path.join(CACHE_DIR, filename)
        if os.path.isfile(file_path):
            # 獲取文件信息
            size = os.path.getsize(file_path)
            mod_time = os.path.getmtime(file_path)
            mod_time_str = datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
            age_days = (current_time - mod_time) / (24 * 60 * 60)
            
            # 格式化顯示
            size_str = f"{size / 1024:.1f} KB"
            age_str = f"{age_days:.1f} 天"
            
            print(f"{filename:<40} {size_str:<10} {mod_time_str:<20} {age_str:<10}")
            total_size += size
    
    print("-" * 80)
    print(f"緩存文件總數: {len(files)}, 總大小: {total_size / 1024:.1f} KB")
    print("")

def clean_old_cache(days=7, dry_run=False):
    """
    清理超過指定天數的緩存文件
    
    參數:
    - days: 清理超過多少天的文件
    - dry_run: 是否只顯示要清理的文件而不實際刪除
    
    返回:
    - (int, int): 成功刪除的文件數量，失敗的文件數量
    """
    if not os.path.exists(CACHE_DIR):
        print(f"緩存目錄不存在: {CACHE_DIR}")
        return 0, 0
    
    success = 0
    failed = 0
    current_time = time.time()
    
    print(f"{'尋找' if dry_run else '清理'}超過 {days} 天的舊緩存...")
    
    for filename in os.listdir(CACHE_DIR):
        file_path = os.path.join(CACHE_DIR, filename)
        if os.path.isfile(file_path):
            # 獲取文件修改時間
            mod_time = os.path.getmtime(file_path)
            age_days = (current_time - mod_time) / (24 * 60 * 60)
            
            # 如果文件超過指定天數
            if age_days > days:
                if dry_run:
                    print(f"將會刪除: {filename} (年齡: {age_days:.1f} 天)")
                else:
                    try:
                        os.remove(file_path)
                        print(f"已刪除: {filename} (年齡: {age_days:.1f} 天)")
                        success += 1
                    except Exception as e:
                        print(f"無法刪除 {filename}: {e}")
                        failed += 1
    
    if dry_run:
        print(f"\n模擬模式: 將會刪除 {success} 個文件")
    else:
        print(f"\n過期緩存清理完成: {success} 個文件已刪除，{failed} 個文件刪除失敗")
    
    return success, failed

def clean_all_cache(dry_run=False):
    """
    清理所有緩存文件
    
    參數:
    - dry_run: 是否只顯示要清理的文件而不實際刪除
    
    返回:
    - (int, int): 成功刪除的文件數量，失敗的文件數量
    """
    if not os.path.exists(CACHE_DIR):
        print(f"緩存目錄不存在: {CACHE_DIR}")
        return 0, 0
    
    success = 0
    failed = 0
    
    print(f"{'將會刪除' if dry_run else '刪除'}所有緩存文件...")
    
    for filename in os.listdir(CACHE_DIR):
        file_path = os.path.join(CACHE_DIR, filename)
        if os.path.isfile(file_path):
            if dry_run:
                print(f"將會刪除: {filename}")
                success += 1
            else:
                try:
                    os.remove(file_path)
                    print(f"已刪除: {filename}")
                    success += 1
                except Exception as e:
                    print(f"無法刪除 {filename}: {e}")
                    failed += 1
    
    if dry_run:
        print(f"\n模擬模式: 將會刪除 {success} 個文件")
    else:
        print(f"\n緩存清理完成: {success} 個文件已刪除，{failed} 個文件刪除失敗")
    
    return success, failed

def backup_cache():
    """
    備份緩存目錄
    
    返回:
    - str: 備份文件路徑，或者 None 表示失敗
    """
    if not os.path.exists(CACHE_DIR) or not os.listdir(CACHE_DIR):
        print("緩存目錄不存在或為空，無需備份")
        return None
    
    try:
        # 創建一個唯一的備份文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"cache_backup_{timestamp}.zip"
        backup_path = os.path.join(BACKUP_DIR, backup_file)
        
        # 創建 ZIP 備份
        shutil.make_archive(
            os.path.splitext(backup_path)[0],  # 不包含擴展名的路徑
            'zip',                             # 壓縮格式
            CACHE_DIR                          # 要壓縮的目錄
        )
        
        print(f"✅ 已創建緩存備份: {backup_file}")
        print(f"   位置: {backup_path}")
        
        return backup_path
        
    except Exception as e:
        print(f"❌ 創建緩存備份失敗: {e}")
        return None

def restore_cache_backup(backup_file=None):
    """
    從備份文件恢復緩存
    
    參數:
    - backup_file: 備份文件路徑，None 表示使用最新的備份
    
    返回:
    - bool: 是否成功恢復
    """
    if backup_file is None:
        # 獲取最新的備份文件
        backup_files = [f for f in os.listdir(BACKUP_DIR) if f.startswith("cache_backup_") and f.endswith(".zip")]
        if not backup_files:
            print("找不到可用的備份文件")
            return False
        
        # 按時間戳排序，獲取最新的備份
        backup_files.sort(reverse=True)
        backup_file = os.path.join(BACKUP_DIR, backup_files[0])
        
    if not os.path.exists(backup_file):
        print(f"備份文件不存在: {backup_file}")
        return False
    
    try:
        # 首先清理當前緩存目錄
        clean_all_cache()
        
        # 確保緩存目錄存在
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        # 解壓縮備份文件
        shutil.unpack_archive(backup_file, CACHE_DIR)
        
        print(f"✅ 已從備份恢復緩存: {os.path.basename(backup_file)}")
        return True
        
    except Exception as e:
        print(f"❌ 恢復緩存失敗: {e}")
        return False

def check_cache_integrity():
    """
    檢查緩存文件的完整性
    
    返回:
    - bool: 緩存是否正常
    """
    if not os.path.exists(CACHE_DIR):
        print("緩存目錄不存在")
        return False
    
    print("檢查緩存文件完整性...")
    corrupted_files = []
    
    for filename in os.listdir(CACHE_DIR):
        file_path = os.path.join(CACHE_DIR, filename)
        if os.path.isfile(file_path) and filename.endswith('.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)  # 嘗試解析 JSON 文件
            except json.JSONDecodeError:
                print(f"損壞的 JSON 文件: {filename}")
                corrupted_files.append(filename)
            except Exception as e:
                print(f"讀取文件 {filename} 時出現錯誤: {e}")
                corrupted_files.append(filename)
    
    if corrupted_files:
        print(f"\n發現 {len(corrupted_files)} 個損壞的緩存文件")
        return False
    else:
        print("\n所有緩存文件完整性正常")
        return True

def optimize_cache():
    """
    優化緩存: 移除不必要的臨時文件，整理重複數據
    
    返回:
    - bool: 是否成功
    """
    print("開始優化緩存...")
    
    # 首先檢查緩存文件完整性
    check_cache_integrity()
    
    # 預先備份，以防優化過程出錯
    backup_cache()
    
    # 移除可能冗餘的臨時文件
    temp_files = [f for f in os.listdir(CACHE_DIR) if f.startswith('temp_') or f.startswith('._')]
    for temp_file in temp_files:
        file_path = os.path.join(CACHE_DIR, temp_file)
        try:
            os.remove(file_path)
            print(f"已刪除臨時文件: {temp_file}")
        except Exception as e:
            print(f"無法刪除臨時文件 {temp_file}: {e}")
    
    print("\n緩存優化完成")
    return True

# 主入口點
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='台股分析系統緩存管理工具')
    parser.add_argument('--list', action='store_true', help='列出所有緩存文件')
    parser.add_argument('--clean-old', type=int, metavar='DAYS', help='清理超過指定天數的緩存文件')
    parser.add_argument('--clean-all', action='store_true', help='清理所有緩存文件')
    parser.add_argument('--backup', action='store_true', help='創建緩存備份')
    parser.add_argument('--restore', action='store_true', help='從最新備份恢復緩存')
    parser.add_argument('--restore-file', type=str, help='從指定備份文件恢復緩存')
    parser.add_argument('--check', action='store_true', help='檢查緩存文件完整性')
    parser.add_argument('--optimize', action='store_true', help='優化緩存')
    parser.add_argument('--dry-run', action='store_true', help='模擬模式(不實際刪除文件)')
    
    args = parser.parse_args()
    
    # 默認顯示所有緩存文件
    if len(sys.argv) == 1:
        list_cache_files()
        sys.exit(0)
    
    # 處理命令行參數
    if args.list:
        list_cache_files()
    elif args.clean_old is not None:
        clean_old_cache(args.clean_old, args.dry_run)
    elif args.clean_all:
        clean_all_cache(args.dry_run)
    elif args.backup:
        backup_cache()
    elif args.restore:
        restore_cache_backup()
    elif args.restore_file:
        restore_cache_backup(args.restore_file)
    elif args.check:
        check_cache_integrity()
    elif args.optimize:
        optimize_cache()

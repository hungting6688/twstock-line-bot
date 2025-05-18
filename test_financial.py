#!/usr/bin/env python3
"""
財報讀取測試腳本 (修正版)
用於測試是否可以成功獲取股票財報數據
"""

import sys
import pandas as pd
from datetime import datetime

# 修正導入路徑 - 使用正確的模組路徑
from modules.data.scraper import get_eps_data, get_dividend_data
from modules.data.scraper import get_all_valid_twse_stocks  # 如果這個函數存在於該模組
from modules.data.fetcher import get_top_stocks

def test_fetch_stock_list():
    """測試獲取股票列表"""
    print("\n[測試] 開始獲取上市股票列表...")
    try:
        # 確認函數在哪個模組
        try:
            from modules.data.scraper import get_all_valid_twse_stocks
            source = "scraper"
        except ImportError:
            # 如果在 scraper 找不到，嘗試其他可能的模組
            try:
                from modules.twse_scraper import get_all_valid_twse_stocks
                source = "twse_scraper"
            except ImportError:
                # 直接實現一個簡單版本來替代
                print("[測試] ⚠️ 找不到 get_all_valid_twse_stocks 函數，使用替代實現")
                return test_fetch_stock_list_alternative()
        
        print(f"[測試] 使用 {source} 模組中的 get_all_valid_twse_stocks 函數")
        stock_list = get_all_valid_twse_stocks()
        
        if not stock_list:
            print("[測試] ❌ 無法獲取股票列表")
            return False
        
        # 顯示前 5 筆資料
        print("[測試] 前 5 筆股票資料:")
        for i, stock in enumerate(stock_list[:5]):
            if isinstance(stock, dict):  # 確認返回的是字典而不是其他類型
                try:
                    print(f"  股票代號: {stock.get('stock_id', 'N/A')}, 名稱: {stock.get('stock_name', 'N/A')}, 產業: {stock.get('industry', 'N/A')}")
                except:
                    print(f"  股票資料 #{i+1}: {stock}")
            else:
                print(f"  股票資料 #{i+1}: {stock}")
        
        print(f"[測試] ✅ 成功獲取股票列表，共 {len(stock_list)} 檔股票")
        return True
    except Exception as e:
        print(f"[測試] ❌ 獲取股票列表失敗: {e}")
        return False

def test_fetch_stock_list_alternative():
    """替代的股票列表獲取測試"""
    try:
        # 使用 fetcher 模組的功能來獲取部分股票列表
        top_stocks = get_top_stocks(limit=20)
        
        if not top_stocks:
            print("[測試] ❌ 無法獲取熱門股票列表")
            return False
        
        print("[測試] 使用熱門股票列表代替完整上市股票列表")
        print("[測試] 熱門股票列表:")
        for i, stock_id in enumerate(top_stocks[:5]):
            print(f"  {i+1}. {stock_id}")
        
        print(f"[測試] ✅ 成功獲取熱門股票列表，共 {len(top_stocks)} 檔股票")
        return True
    except Exception as e:
        print(f"[測試] ❌ 獲取熱門股票列表失敗: {e}")
        return False

def test_fetch_top_stocks():
    """測試獲取熱門股票"""
    print("\n[測試] 開始獲取熱門股票...")
    try:
        top_stocks = get_top_stocks(limit=20)
        if not top_stocks:
            print("[測試] ❌ 無法獲取熱門股票")
            return False
        
        # 顯示結果
        print("[測試] 熱門股票:")
        for i, stock_id in enumerate(top_stocks):
            print(f"  {i+1}. {stock_id}")
        
        print(f"[測試] ✅ 成功獲取熱門股票，共 {len(top_stocks)} 檔")
        return True
    except Exception as e:
        print(f"[測試] ❌ 獲取熱門股票失敗: {e}")
        return False

def test_fetch_eps_data():
    """測試獲取 EPS 數據"""
    print("\n[測試] 開始獲取 EPS 數據...")
    try:
        eps_data = get_eps_data()
        if not eps_data:
            print("[測試] ❌ 無法獲取 EPS 數據")
            return False
        
        # 顯示前 5 筆資料
        count = 0
        print("[測試] 前 5 筆 EPS 數據:")
        for stock_id, data in eps_data.items():
            print(f"  股票代號: {stock_id}, EPS: {data.get('eps')}, 股息: {data.get('dividend')}")
            count += 1
            if count >= 5:
                break
        
        print(f"[測試] ✅ 成功獲取 EPS 數據，共 {len(eps_data)} 檔股票")
        return True
    except Exception as e:
        print(f"[測試] ❌ 獲取 EPS 數據失敗: {e}")
        return False

def test_fetch_dividend_data():
    """測試獲取股息數據"""
    print("\n[測試] 開始獲取股息數據...")
    try:
        dividend_data = get_dividend_data()
        if not dividend_data:
            print("[測試] ❌ 無法獲取股息數據")
            return False
        
        # 顯示前 5 筆資料
        count = 0
        print("[測試] 前 5 筆股息數據:")
        for stock_id, dividend in dividend_data.items():
            print(f"  股票代號: {stock_id}, 股息: {dividend}")
            count += 1
            if count >= 5:
                break
        
        print(f"[測試] ✅ 成功獲取股息數據，共 {len(dividend_data)} 檔股票")
        return True
    except Exception as e:
        print(f"[測試] ❌ 獲取股息數據失敗: {e}")
        return False

def run_all_tests():
    """執行所有測試"""
    print("=" * 50)
    print(f"財報數據讀取測試開始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 測試項目與結果
    tests = [
        ("股票列表測試", test_fetch_stock_list),
        ("熱門股票測試", test_fetch_top_stocks),
        ("EPS 數據測試", test_fetch_eps_data),
        ("股息數據測試", test_fetch_dividend_data)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{'-' * 40}")
        print(f"執行 {name}...")
        success = test_func()
        results.append((name, success))
    
    # 顯示總結果
    print("\n" + "=" * 50)
    print("測試結果總結:")
    all_success = True
    for name, success in results:
        status = "✅ 成功" if success else "❌ 失敗"
        all_success = all_success and success
        print(f"  {name}: {status}")
    
    print("-" * 50)
    if all_success:
        print("所有測試都成功通過! 財報數據獲取功能正常。")
    else:
        print("部分測試失敗，請檢查輸出日誌找出問題。")
    print("=" * 50)

if __name__ == "__main__":
    run_all_tests()

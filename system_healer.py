"""
system_healer.py - 系統自我修復整合
"""
import os
import time
import json
import logging
from datetime import datetime
import traceback
import threading

# 確保日誌目錄存在
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 配置日誌
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'system_healer.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SystemHealer:
    """系統自我修復整合"""
    
    # 單例模式
    _instance = None
    
    @staticmethod
    def get_instance():
        """獲取系統修復器單例"""
        if SystemHealer._instance is None:
            SystemHealer._instance = SystemHealer()
        return SystemHealer._instance
    
    def __init__(self):
        """初始化系統修復器"""
        self.last_check_time = None
        self.last_heal_time = None
        self.running = False
        self.check_interval = 3600  # 每小時檢查一次
        self.background_thread = None
        self.repair_history = []
        
        # 註冊系統組件及其檢查與修復函數
        # 組件名稱 -> {check_func, heal_func, priority, enabled}
        self.components = {}
        
        # 註冊默認組件處理
        self._register_default_components()
        
    def _register_default_components(self):
        """註冊默認組件處理"""
        # 緩存服務
        self.register_component(
            'cache', 
            check_func=self._check_cache,
            heal_func=self._heal_cache,
            priority=10,  # 高優先級
            enabled=True
        )
        
        # 網路服務
        self.register_component(
            'network', 
            check_func=self._check_network,
            heal_func=self._heal_network,
            priority=20,
            enabled=True
        )
        
        # 通知服務
        self.register_component(
            'notifications', 
            check_func=self._check_notifications,
            heal_func=self._heal_notifications,
            priority=15,
            enabled=True
        )
        
        # 熔斷器服務
        self.register_component(
            'circuit_breakers', 
            check_func=self._check_circuit_breakers,
            heal_func=self._heal_circuit_breakers,
            priority=5,
            enabled=True
        )
        
        # 緩存備份服務
        self.register_component(
            'cache_backup', 
            check_func=self._check_cache_backup,
            heal_func=self._heal_cache_backup,
            priority=30,
            enabled=True
        )
    
    def register_component(self, name, check_func, heal_func, priority=50, enabled=True):
        """
        註冊系統組件
        
        參數:
        - name: 組件名稱
        - check_func: 檢查函數 (無參數,返回檢查結果字典)
        - heal_func: 修復函數 (參數為檢查結果,返回修復結果)
        - priority: 優先級 (數字越小優先級越高)
        - enabled: 是否啟用
        """
        self.components[name] = {
            'check_func': check_func,
            'heal_func': heal_func,
            'priority': priority,
            'enabled': enabled
        }
        logging.info(f"註冊系統組件: {name}, 優先級: {priority}, 已啟用: {enabled}")
    
    def check_all(self):
        """
        檢查所有系統組件
        
        返回:
        - dict: 檢查結果 {組件名稱: 檢查結果}
        """
        if self.running:
            logging.warning("已有檢查正在運行，跳過本次檢查")
            return {"status": "skipped", "reason": "already_running"}
        
        self.running = True
        self.last_check_time = time.time()
        results = {
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }
        
        try:
            logging.info("開始系統健康檢查...")
            print("[system_healer] 開始系統健康檢查...")
            
            # 按優先級排序組件
            sorted_components = sorted(
                [
                    (name, comp) 
                    for name, comp in self.components.items() 
                    if comp['enabled']
                ],
                key=lambda x: x[1]['priority']
            )
            
            # 執行檢查
            for name, component in sorted_components:
                try:
                    logging.info(f"檢查組件: {name}")
                    print(f"[system_healer] 檢查組件: {name}")
                    
                    # 執行檢查函數
                    check_result = component['check_func']()
                    results['components'][name] = check_result
                    
                    # 記錄結果
                    status = check_result.get('status', 'unknown')
                    
                    if status == 'ok':
                        logging.info(f"組件 {name} 檢查通過")
                    else:
                        severity = check_result.get('severity', 'warning')
                        msg = check_result.get('message', '未知問題')
                        logging.warning(f"組件 {name} 檢查失敗 (嚴重度: {severity}): {msg}")
                    
                except Exception as e:
                    error = str(e)
                    logging.error(f"檢查組件 {name} 時出錯: {error}")
                    traceback.print_exc()
                    
                    results['components'][name] = {
                        'status': 'error',
                        'message': f"檢查時出錯: {error}",
                        'severity': 'critical',
                        'exception': error,
                        'traceback': traceback.format_exc()
                    }
            
            # 確定整體狀態
            component_statuses = [
                comp.get('status', 'unknown') 
                for comp in results['components'].values()
            ]
            
            if all(status == 'ok' for status in component_statuses):
                results['status'] = 'ok'
                results['message'] = '所有組件正常'
            elif any(status == 'error' for status in component_statuses):
                results['status'] = 'error'
                results['message'] = '部分組件出錯'
            else:
                results['status'] = 'warning'
                results['message'] = '部分組件有警告'
            
            logging.info(f"系統健康檢查完成，狀態: {results['status']}")
            print(f"[system_healer] 系統健康檢查完成，狀態: {results['status']}")
            
            # 保存檢查結果
            self._save_check_results(results)
            
        except Exception as e:
            error = str(e)
            logging.error(f"健康檢查過程中發生錯誤: {error}")
            traceback.print_exc()
            
            results['status'] = 'error'
            results['message'] = f"健康檢查錯誤: {error}"
            results['exception'] = error
            results['traceback'] = traceback.format_exc()
        
        finally:
            self.running = False
            
        return results
    
    def heal_all(self, check_results=None, auto_check=True):
        """
        嘗試修復所有問題
        
        參數:
        - check_results: 檢查結果，None則自動執行檢查
        - auto_check: 如果check_results為None，是否自動執行檢查
        
        返回:
        - dict: 修復結果
        """
        if self.running:
            logging.warning("已有修復正在運行，跳過本次修復")
            return {"status": "skipped", "reason": "already_running"}
        
        self.running = True
        self.last_heal_time = time.time()
        
        if check_results is None and auto_check:
            check_results = self.check_all()
        
        if check_results is None:
            logging.error("無檢查結果可用，無法執行修復")
            self.running = False
            return {
                "status": "error", 
                "message": "無檢查結果可用，無法執行修復"
            }
        
        healed = {
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'overall_status': 'ok',
            'actions_taken': []
        }
        
        try:
            logging.info("開始系統修復...")
            print("[system_healer] 開始系統修復...")
            
            # 篩選需要修復的組件
            components_to_heal = []
            
            for name, result in check_results.get('components', {}).items():
                if name not in self.components:
                    continue
                    
                component = self.components[name]
                
                if not component['enabled']:
                    continue
                    
                if result.get('status') != 'ok':
                    components_to_heal.append((name, component, result))
            
            # 按優先級排序
            components_to_heal.sort(key=lambda x: x[1]['priority'])
            
            # 執行修復
            for name, component, result in components_to_heal:
                try:
                    logging.info(f"修復組件: {name}")
                    print(f"[system_healer] 修復組件: {name}")
                    
                    # 執行修復函數
                    heal_result = component['heal_func'](result)
                    healed['components'][name] = heal_result
                    
                    # 記錄結果
                    success = heal_result.get('success', False)
                    actions = heal_result.get('actions', [])
                    
                    if success:
                        logging.info(f"組件 {name} 修復成功")
                        print(f"[system_healer] 組件 {name} 修復成功")
                    else:
                        reason = heal_result.get('reason', '未知原因')
                        logging.warning(f"組件 {name} 修復失敗: {reason}")
                        print(f"[system_healer] 組件 {name} 修復失敗: {reason}")
                        healed['overall_status'] = 'partial'
                    
                    # 記錄所有執行的動作
                    for action in actions:
                        healed['actions_taken'].append({
                            "component": name,
                            "action": action.get("action"),
                            "target": action.get("target"),
                            "success": action.get("success", False),
                            "message": action.get("message", ""),
                            "timestamp": action.get("timestamp", datetime.now().isoformat())
                        })
                    
                except Exception as e:
                    error = str(e)
                    logging.error(f"修復組件 {name} 時出錯: {error}")
                    traceback.print_exc()
                    
                    healed['components'][name] = {
                        'success': False,
                        'message': f"修復時出錯: {error}",
                        'exception': error,
                        'traceback': traceback.format_exc()
                    }
                    
                    healed['overall_status'] = 'partial'
            
            # 如果沒有需要修復的組件
            if not components_to_heal:
                logging.info("所有組件狀態正常，無需修復")
                print("[system_healer] 所有組件狀態正常，無需修復")
                healed['message'] = "所有組件狀態正常，無需修復"
            else:
                # 總結修復情況
                success_count = sum(
                    1 for result in healed['components'].values() 
                    if result.get('success', False)
                )
                total_count = len(components_to_heal)
                
                healed['message'] = f"修復了 {success_count}/{total_count} 個組件"
                if success_count == total_count:
                    healed['overall_status'] = 'ok'
                elif success_count == 0:
                    healed['overall_status'] = 'failed'
                
                logging.info(f"系統修復完成: {healed['message']}")
                print(f"[system_healer] 系統修復完成: {healed['message']}")
            
            # 保存修復記錄
            self._save_heal_results(healed)
            
            # 添加到修復歷史
            self.repair_history.append({
                'timestamp': datetime.now().isoformat(),
                'fixed_components': success_count,
                'total_components': total_count,
                'actions_taken': len(healed['actions_taken'])
            })
            
            # 限制歷史記錄數量
            if len(self.repair_history) > 100:
                self.repair_history = self.repair_history[-100:]
            
        except Exception as e:
            error = str(e)
            logging.error(f"修復過程中發生錯誤: {error}")
            traceback.print_exc()
            
            healed['overall_status'] = 'error'
            healed['message'] = f"修復過程錯誤: {error}"
            healed['exception'] = error
            healed['traceback'] = traceback.format_exc()
        
        finally:
            self.running = False
        
        return healed
    
    def start_background_monitoring(self, interval=3600):
        """
        啟動背景監控
        
        參數:
        - interval: 檢查間隔(秒)，默認1小時
        """
        if self.background_thread and self.background_thread.is_alive():
            logging.warning("背景監控已經在運行")
            return False
        
        self.check_interval = interval
        self.background_thread = threading.Thread(target=self._background_monitoring, daemon=True)
        self.background_thread.start()
        
        logging.info(f"啟動背景監控，間隔: {interval}秒")
        print(f"[system_healer] 啟動背景監控，間隔: {interval}秒")
        return True
    
    def stop_background_monitoring(self):
        """停止背景監控"""
        if not self.background_thread or not self.background_thread.is_alive():
            logging.warning("背景監控未運行")
            return False
        
        # 設置終止標誌
        self.running = False
        
        # 等待線程終止
        self.background_thread.join(timeout=5)
        
        logging.info("已停止背景監控")
        print("[system_healer] 已停止背景監控")
        return True
    
    def _background_monitoring(self):
        """背景監控執行函數"""
        logging.info("背景監控開始運行")
        
        while True:
            try:
                # 檢查系統狀態
                check_results = self.check_all()
                
                # 如果有問題，嘗試修復
                if check_results.get('status') != 'ok':
                    logging.info("檢測到系統問題，自動修復...")
                    print("[system_healer] 檢測到系統問題，自動修復...")
                    self.heal_all(check_results=check_results)
                
                # 等待下一次檢查
                for _ in range(self.check_interval):
                    time.sleep(1)
                    # 檢查是否應該終止線程
                    if not self.running:
                        logging.info("背景監控被終止")
                        return
                
            except Exception as e:
                logging.error(f"背景監控出錯: {e}")
                traceback.print_exc()
                
                # 出錯後等待一段時間再繼續
                for _ in range(60):  # 等待1分鐘
                    time.sleep(1)
                    if not self.running:
                        logging.info("背景監控被終止")
                        return
    
    def _save_check_results(self, results):
        """保存檢查結果"""
        try:
            check_dir = os.path.join(LOG_DIR, 'health_checks')
            os.makedirs(check_dir, exist_ok=True)
            
            # 帶時間戳的文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            check_file = os.path.join(check_dir, f"check_{timestamp}.json")
            
            # 保存結果
            with open(check_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 更新最新結果鏈接
            latest_file = os.path.join(check_dir, "latest_check.json")
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
                
            logging.info(f"檢查結果已保存至 {check_file}")
            
        except Exception as e:
            logging.error(f"保存檢查結果失敗: {e}")
    
    def _save_heal_results(self, results):
        """保存修復結果"""
        try:
            heal_dir = os.path.join(LOG_DIR, 'healing')
            os.makedirs(heal_dir, exist_ok=True)
            
            # 帶時間戳的文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            heal_file = os.path.join(heal_dir, f"heal_{timestamp}.json")
            
            # 保存結果
            with open(heal_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 更新最新結果鏈接
            latest_file = os.path.join(heal_dir, "latest_heal.json")
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
                
            logging.info(f"修復結果已保存至 {heal_file}")
            
        except Exception as e:
            logging.error(f"保存修復結果失敗: {e}")
    
    # 默認的檢查和修復函數
    def _check_cache(self):
        """檢查緩存系統"""
        try:
            # 導入緩存管理模塊
            from cache_manage import cache_health_check, get_cache_info
            
            # 使用緩存健康檢查函數
            health_report = cache_health_check()
            
            # 轉換檢查結果為統一格式
            result = {
                'status': 'ok' if health_report['status'] == 'ok' else 'warning',
                'message': health_report['message'],
                'details': health_report
            }
            
            # 如果狀態是錯誤，更改嚴重度
            if health_report['status'] == 'error':
                result['status'] = 'error'
                result['severity'] = 'high'
                
            return result
            
        except ImportError:
            return {
                'status': 'warning',
                'message': '無法導入緩存管理模塊',
                'severity': 'medium'
            }
        except Exception as e:
            logging.error(f"檢查緩存時出錯: {e}")
            return {
                'status': 'error',
                'message': f'檢查緩存時出錯: {e}',
                'severity': 'critical',
                'exception': str(e)
            }
    
    def _heal_cache(self, check_result):
        """修復緩存問題"""
        try:
            # 導入緩存管理模塊
            from cache_manage import (
                restore_backup, backup_cache, 
                clean_old_cache, automatic_backup
            )
            
            status = check_result.get('status', 'unknown')
            details = check_result.get('details', {})
            actions_taken = []
            success = False
            
            # 檢查關鍵緩存問題
            if status in ['error', 'warning']:
                # 尋找缺失的關鍵緩存
                missing_critical = []
                for warning in details.get('warnings', []):
                    if '缺少關鍵緩存' in warning:
                        # 從警告訊息中提取緩存名稱
                        parts = warning.split(' ')
                        cache_name = parts[-1] if parts else None
                        if cache_name:
                            missing_critical.append(cache_name)
                
                # 恢復缺失的關鍵緩存
                if missing_critical:
                    for cache_name in missing_critical:
                        try:
                            restore_result = restore_backup(filename=cache_name)
                            actions_taken.append({
                                "action": "restore_cache",
                                "target": cache_name,
                                "success": restore_result,
                                "message": f"{'成功' if restore_result else '失敗'}恢復緩存 {cache_name}",
                                "timestamp": datetime.now().isoformat()
                            })
                        except Exception as e:
                            actions_taken.append({
                                "action": "restore_cache",
                                "target": cache_name,
                                "success": False,
                                "message": f"恢復緩存 {cache_name} 時出錯: {e}",
                                "timestamp": datetime.now().isoformat()
                            })
                
                # 檢查並處理可能損壞的緩存文件
                for filename, file_details in details.get('details', {}).items():
                    if isinstance(file_details, dict) and file_details.get('status') in ['error', 'warning']:
                        message = file_details.get('message', '')
                        
                        if '可能為空或損壞' in message:
                            try:
                                # 備份然後刪除損壞的文件
                                import os
                                from cache_manage import CACHE_DIR, backup_single_file, log_event
                                
                                # 先備份
                                backup_single_file(filename)
                                
                                # 刪除損壞文件
                                file_path = os.path.join(CACHE_DIR, filename)
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                    log_event(f"已刪除損壞的緩存文件: {filename}")
                                    
                                    actions_taken.append({
                                        "action": "delete_corrupt_cache",
                                        "target": filename,
                                        "success": True,
                                        "message": f"已刪除損壞的緩存文件 {filename}",
                                        "timestamp": datetime.now().isoformat()
                                    })
                            except Exception as e:
                                actions_taken.append({
                                    "action": "delete_corrupt_cache",
                                    "target": filename,
                                    "success": False,
                                    "message": f"刪除損壞的緩存文件 {filename} 時出錯: {e}",
                                    "timestamp": datetime.now().isoformat()
                                })
                
                # 執行自動備份
                try:
                    backup_result = backup_cache()
                    actions_taken.append({
                        "action": "backup_cache",
                        "target": "all",
                        "success": backup_result,
                        "message": f"{'成功' if backup_result else '失敗'}建立緩存備份",
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    actions_taken.append({
                        "action": "backup_cache",
                        "target": "all",
                        "success": False,
                        "message": f"建立緩存備份時出錯: {e}",
                        "timestamp": datetime.now().isoformat()
                    })
                
                # 執行自動緩存維護
                try:
                    auto_result = automatic_backup()
                    actions_taken.append({
                        "action": "automatic_maintenance",
                        "target": "cache",
                        "success": auto_result,
                        "message": f"{'成功' if auto_result else '無需'}執行自動緩存維護",
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    actions_taken.append({
                        "action": "automatic_maintenance",
                        "target": "cache",
                        "success": False,
                        "message": f"執行自動緩存維護時出錯: {e}",
                        "timestamp": datetime.now().isoformat()
                    })
                
                # 確定是否成功修復
                success_count = sum(1 for action in actions_taken if action.get('success', False))
                success = success_count > 0
            
            else:
                # 如果沒有問題，只執行例行維護
                success = True
                # 清理過舊的緩存
                clean_old_cache(days=None, force=False)
                actions_taken.append({
                    "action": "clean_old_cache",
                    "target": "all",
                    "success": True,
                    "message": "執行例行緩存清理",
                    "timestamp": datetime.now().isoformat()
                })
            
            return {
                'success': success,
                'message': f"已執行 {len(actions_taken)} 個修復操作" if actions_taken else "無需修復",
                'actions': actions_taken
            }
            
        except ImportError:
            return {
                'success': False,
                'message': '無法導入緩存管理模塊',
                'actions': []
            }
        except Exception as e:
            logging.error(f"修復緩存時出錯: {e}")
            return {
                'success': False,
                'message': f'修復緩存時出錯: {e}',
                'actions': [],
                'exception': str(e)
            }
    
    def _check_network(self):
        """檢查網路連接"""
        try:
            # 導入網路測試模塊
            from utils import check_network_connectivity
            
            # 使用連接檢查函數
            network_status = check_network_connectivity()
            
            # 轉換檢查結果為統一格式
            success_rate = network_status.get('success_rate', 0)
            
            if success_rate == 100:
                status = 'ok'
                message = '所有網站連接正常'
                severity = 'low'
            elif success_rate >= 60:
                status = 'warning'
                message = f'部分網站連接問題，成功率 {success_rate}%'
                severity = 'medium'
            else:
                status = 'error'
                message = f'嚴重網路連接問題，成功率僅 {success_rate}%'
                severity = 'high'
            
            return {
                'status': status,
                'message': message,
                'severity': severity,
                'details': network_status
            }
            
        except ImportError:
            return {
                'status': 'warning',
                'message': '無法導入網路測試模塊',
                'severity': 'medium'
            }
        except Exception as e:
            logging.error(f"檢查網路連接時出錯: {e}")
            return {
                'status': 'error',
                'message': f'檢查網路連接時出錯: {e}',
                'severity': 'critical',
                'exception': str(e)
            }
    
    def _heal_network(self, check_result):
        """修復網路問題"""
        try:
            actions_taken = []
            
            status = check_result.get('status', 'unknown')
            details = check_result.get('details', {})
            
            # 網路問題通常無法通過軟件自動修復
            # 但可以嘗試一些簡單的操作
            
            if status in ['error', 'warning']:
                # 嘗試重置連接管理器的統計
                try:
                    from connection_manager import reset_connection_stats
                    
                    reset_connection_stats()
                    actions_taken.append({
                        "action": "reset_connection_stats",
                        "target": "all",
                        "success": True,
                        "message": "重置連接管理器統計",
                        "timestamp": datetime.now().isoformat()
                    })
                except ImportError:
                    actions_taken.append({
                        "action": "reset_connection_stats",
                        "target": "all",
                        "success": False,
                        "message": "無法導入連接管理器模塊",
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    actions_taken.append({
                        "action": "reset_connection_stats",
                        "target": "all",
                        "success": False,
                        "message": f"重置連接統計時出錯: {e}",
                        "timestamp": datetime.now().isoformat()
                    })
                
                # 重置熔斷器
                try:
                    from circuit_breaker import CircuitBreaker
                    
                    CircuitBreaker.reset_all()
                    actions_taken.append({
                        "action": "reset_circuit_breakers",
                        "target": "all",
                        "success": True,
                        "message": "重置所有熔斷器",
                        "timestamp": datetime.now().isoformat()
                    })
                except ImportError:
                    actions_taken.append({
                        "action": "reset_circuit_breakers",
                        "target": "all",
                        "success": False,
                        "message": "無法導入熔斷器模塊",
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    actions_taken.append({
                        "action": "reset_circuit_breakers",
                        "target": "all",
                        "success": False,
                        "message": f"重置熔斷器時出錯: {e}",
                        "timestamp": datetime.now().isoformat()
                    })
            
            # 確定是否成功修復
            success_count = sum(1 for action in actions_taken if action.get('success', False))
            success = success_count > 0
            
            return {
                'success': success,
                'message': "網路問題可能需要手動干預" if status in ['error', 'warning'] else "網路正常，無需修復",
                'actions': actions_taken
            }
            
        except Exception as e:
            logging.error(f"修復網路時出錯: {e}")
            return {
                'success': False,
                'message': f'修復網路時出錯: {e}',
                'actions': [],
                'exception': str(e)
            }
    
    def _check_notifications(self):
        """檢查通知系統"""
        try:
            # 導入通知統計模塊
            from dual_notifier import get_notification_stats
            
            # 獲取通知系統統計
            notification_stats = get_notification_stats()
            
            # 計算郵件和LINE的成功率
            email_success_rate = notification_stats.get('email', {}).get('success_rate', 0)
            line_success_rate = notification_stats.get('line', {}).get('success_rate', 0)
            pending_count = notification_stats.get('failed_notifications', {}).get('pending', 0)
            
            # 判斷狀態
            if email_success_rate >= 80 and line_success_rate >= 80 and pending_count == 0:
                status = 'ok'
                message = '通知系統運作正常'
                severity = 'low'
            elif email_success_rate >= 50 and line_success_rate >= 50:
                status = 'warning'
                message = '通知系統部分異常'
                severity = 'medium'
            else:
                status = 'error'
                message = '通知系統嚴重異常'
                severity = 'high'
            
            return {
                'status': status,
                'message': message,
                'severity': severity,
                'details': notification_stats
            }
            
        except ImportError:
            return {
                'status': 'warning',
                'message': '無法導入通知模塊',
                'severity': 'medium'
            }
        except Exception as e:
            logging.error(f"檢查通知系統時出錯: {e}")
            return {
                'status': 'error',
                'message': f'檢查通知系統時出錯: {e}',
                'severity': 'critical',
                'exception': str(e)
            }
    
    def _heal_notifications(self, check_result):
        """修復通知系統問題"""
        try:
            actions_taken = []
            
            status = check_result.get('status', 'unknown')
            details = check_result.get('details', {})
            
            if status in ['error', 'warning']:
                # 嘗試重試失敗的通知
                try:
                    from dual_notifier import retry_failed_notifications, cleanup_old_failed_notifications
                    
                    # 重試失敗的通知
                    retry_count, success_count = retry_failed_notifications()
                    
                    actions_taken.append({
                        "action": "retry_notifications",
                        "target": "failed",
                        "success": success_count > 0,
                        "message": f"重試了 {retry_count} 個失敗通知，成功 {success_count} 個",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # 清理過舊的失敗通知記錄
                    cleaned_count = cleanup_old_failed_notifications()
                    
                    actions_taken.append({
                        "action": "cleanup_notifications",
                        "target": "old_failed",
                        "success": True,
                        "message": f"清理了 {cleaned_count} 個過舊的失敗通知記錄",
                        "timestamp": datetime.now().isoformat()
                    })
                except ImportError:
                    actions_taken.append({
                        "action": "retry_notifications",
                        "target": "failed",
                        "success": False,
                        "message": "無法導入通知模塊",
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    actions_taken.append({
                        "action": "retry_notifications",
                        "target": "failed",
                        "success": False,
                        "message": f"重試失敗通知時出錯: {e}",
                        "timestamp": datetime.now().isoformat()
                    })
            else:
                # 如果通知系統正常，執行例行清理
                try:
                    from dual_notifier import cleanup_old_failed_notifications
                    
                    cleaned_count = cleanup_old_failed_notifications()
                    
                    actions_taken.append({
                        "action": "cleanup_notifications",
                        "target": "old_failed",
                        "success": True,
                        "message": f"例行清理了 {cleaned_count} 個過舊的失敗通知記錄",
                        "timestamp": datetime.now().isoformat()
                    })
                except ImportError:
                    pass  # 忽略導入錯誤
                except Exception as e:
                    logging.error(f"例行清理失敗通知時出錯: {e}")
            
            # 確定是否成功修復
            success_count = sum(1 for action in actions_taken if action.get('success', False))
            success = success_count > 0
            
            return {
                'success': success,
                'message': "已執行通知系統維護操作" if actions_taken else "無需修復",
                'actions': actions_taken
            }
            
        except Exception as e:
            logging.error(f"修復通知系統時出錯: {e}")
            return {
                'success': False,
                'message': f'修復通知系統時出錯: {e}',
                'actions': [],
                'exception': str(e)
            }
    
    def _check_circuit_breakers(self):
        """檢查熔斷器狀態"""
        try:
            # 導入熔斷器模塊
            from circuit_breaker import CircuitBreaker
            
            # 獲取所有熔斷器狀態
            circuit_states = CircuitBreaker.get_all_states()
            
            # 檢查是否有打開的熔斷器
            open_circuits = [
                name for name, state in circuit_states.items()
                if state.get('state') in ['OPEN', 'HALF-OPEN']
            ]
            
            if not open_circuits:
                status = 'ok'
                message = '所有熔斷器處於正常關閉狀態'
                severity = 'low'
            else:
                status = 'warning'
                message = f'{len(open_circuits)} 個熔斷器處於打開或半開狀態'
                severity = 'medium'
            
            return {
                'status': status,
                'message': message,
                'severity': severity,
                'details': circuit_states,
                'open_circuits': open_circuits
            }
            
        except ImportError:
            return {
                'status': 'warning',
                'message': '無法導入熔斷器模塊',
                'severity': 'low'
            }
        except Exception as e:
            logging.error(f"檢查熔斷器時出錯: {e}")
            return {
                'status': 'error',
                'message': f'檢查熔斷器時出錯: {e}',
                'severity': 'medium',
                'exception': str(e)
            }
    
    def _heal_circuit_breakers(self, check_result):
        """修復熔斷器問題"""
        try:
            actions_taken = []
            
            status = check_result.get('status', 'unknown')
            details = check_result.get('details', {})
            open_circuits = check_result.get('open_circuits', [])
            
            if status in ['error', 'warning'] and open_circuits:
                # 檢查每個打開的熔斷器是否已經過久
                try:
                    from circuit_breaker import CircuitBreaker
                    
                    for circuit_name in open_circuits:
                        # 獲取熔斷器實例
                        circuit = CircuitBreaker.get_instance(circuit_name)
                        circuit_state = circuit.get_state()
                        
                        # 檢查熔斷器是否應該被重置
                        state = circuit_state.get('state')
                        last_failure_time = circuit_state.get('last_failure')
                        
                        # 如果熔斷器已開啟超過一天，嘗試重置
                        if last_failure_time:
                            if 'time_since_failure' in circuit_state and circuit_state['time_since_failure'] > 86400:  # 24小時
                                circuit.reset()
                                actions_taken.append({
                                    "action": "reset_circuit_breaker",
                                    "target": circuit_name,
                                    "success": True,
                                    "message": f"重置長時間打開的熔斷器 {circuit_name}",
                                    "timestamp": datetime.now().isoformat()
                                })
                except ImportError:
                    actions_taken.append({
                        "action": "reset_circuit_breakers",
                        "target": "all",
                        "success": False,
                        "message": "無法導入熔斷器模塊",
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    actions_taken.append({
                        "action": "reset_circuit_breakers",
                        "target": "open",
                        "success": False,
                        "message": f"重置熔斷器時出錯: {e}",
                        "timestamp": datetime.now().isoformat()
                    })
            
            # 確定是否成功修復
            success_count = sum(1 for action in actions_taken if action.get('success', False))
            success = success_count > 0 or status == 'ok'
            
            return {
                'success': success,
                'message': "已重置長時間打開的熔斷器" if actions_taken else "無需修復或無法修復",
                'actions': actions_taken
            }
            
        except Exception as e:
            logging.error(f"修復熔斷器時出錯: {e}")
            return {
                'success': False,
                'message': f'修復熔斷器時出錯: {e}',
                'actions': [],
                'exception': str(e)
            }
    
    def _check_cache_backup(self):
        """檢查緩存備份系統"""
        try:
            # 導入緩存管理模塊
            from cache_manage import CACHE_DIR, BACKUP_DIR
            import os
            import glob
            from datetime import datetime, timedelta
            
            # 檢查備份目錄是否存在
            if not os.path.exists(BACKUP_DIR):
                return {
                    'status': 'warning',
                    'message': '緩存備份目錄不存在',
                    'severity': 'medium'
                }
            
            # 獲取所有備份文件
            backup_zips = glob.glob(os.path.join(BACKUP_DIR, 'backup_*.zip'))
            backup_dirs = [d for d in os.listdir(BACKUP_DIR) 
                        if os.path.isdir(os.path.join(BACKUP_DIR, d)) and d.startswith('backup_')]
            
            # 如果沒有備份
            if not backup_zips and not backup_dirs:
                return {
                    'status': 'warning',
                    'message': '沒有找到緩存備份',
                    'severity': 'medium'
                }
            
            # 獲取最近一次備份時間
            if backup_zips:
                backup_zips.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                last_backup_time = datetime.fromtimestamp(os.path.getmtime(backup_zips[0]))
            elif backup_dirs:
                backup_dirs_full = [os.path.join(BACKUP_DIR, d) for d in backup_dirs]
                backup_dirs_full.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                last_backup_time = datetime.fromtimestamp(os.path.getmtime(backup_dirs_full[0]))
            else:
                last_backup_time = None
            
            # 檢查最近備份是否過期
            if last_backup_time:
                now = datetime.now()
                days_since_backup = (now - last_backup_time).days
                
                if days_since_backup > 7:
                    status = 'warning'
                    message = f'最近的緩存備份已 {days_since_backup} 天未更新'
                    severity = 'medium'
                elif days_since_backup > 3:
                    status = 'warning'
                    message = f'最近的緩存備份已 {days_since_backup} 天未更新'
                    severity = 'low'
                else:
                    status = 'ok'
                    message = f'最近的緩存備份在 {days_since_backup} 天前'
                    severity = 'low'
            else:
                status = 'warning'
                message = '無法確定最近備份時間'
                severity = 'medium'
            
            return {
                'status': status,
                'message': message,
                'severity': severity,
                'details': {
                    'backup_count': len(backup_zips) + len(backup_dirs),
                    'backup_zips': len(backup_zips),
                    'backup_dirs': len(backup_dirs),
                    'last_backup_time': last_backup_time.isoformat() if last_backup_time else None
                }
            }
            
        except ImportError:
            return {
                'status': 'warning',
                'message': '無法導入緩存管理模塊',
                'severity': 'low'
            }
        except Exception as e:
            logging.error(f"檢查緩存備份時出錯: {e}")
            return {
                'status': 'error',
                'message': f'檢查緩存備份時出錯: {e}',
                'severity': 'medium',
                'exception': str(e)
            }
    
    def _heal_cache_backup(self, check_result):
        """修復緩存備份問題"""
        try:
            actions_taken = []
            
            status = check_result.get('status', 'unknown')
            details = check_result.get('details', {})
            
            if status in ['error', 'warning']:
                # 創建新的備份
                try:
                    from cache_manage import backup_cache, auto_cleanup_backups
                    
                    # 建立新備份
                    backup_result = backup_cache()
                    
                    actions_taken.append({
                        "action": "create_backup",
                        "target": "cache",
                        "success": backup_result,
                        "message": f"{'成功' if backup_result else '失敗'}建立新緩存備份",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # 清理過舊的備份
                    if backup_result:
                        cleanup_count = auto_cleanup_backups()
                        
                        actions_taken.append({
                            "action": "cleanup_backups",
                            "target": "old",
                            "success": True,
                            "message": f"清理了 {cleanup_count} 個過舊的備份",
                            "timestamp": datetime.now().isoformat()
                        })
                except ImportError:
                    actions_taken.append({
                        "action": "create_backup",
                        "target": "cache",
                        "success": False,
                        "message": "無法導入緩存管理模塊",
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    actions_taken.append({
                        "action": "create_backup",
                        "target": "cache",
                        "success": False,
                        "message": f"建立備份時出錯: {e}",
                        "timestamp": datetime.now().isoformat()
                    })
            else:
                # 如果備份系統正常，執行例行清理
                try:
                    from cache_manage import auto_cleanup_backups
                    
                    cleanup_count = auto_cleanup_backups()
                    
                    actions_taken.append({
                        "action": "cleanup_backups",
                        "target": "old",
                        "success": True,
                        "message": f"例行清理了 {cleanup_count} 個過舊的備份",
                        "timestamp": datetime.now().isoformat()
                    })
                except ImportError:
                    pass  # 忽略導入錯誤
                except Exception as e:
                    logging.error(f"例行清理備份時出錯: {e}")
            
            # 確定是否成功修復
            success_count = sum(1 for action in actions_taken if action.get('success', False))
            success = success_count > 0
            
            return {
                'success': success,
                'message': "已執行備份系統維護操作" if actions_taken else "無需修復",
                'actions': actions_taken
            }
            
        except Exception as e:
            logging.error(f"修復緩存備份時出錯: {e}")
            return {
                'success': False,
                'message': f'修復緩存備份時出錯: {e}',
                'actions': [],
                'exception': str(e)
            }

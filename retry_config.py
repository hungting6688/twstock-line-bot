"""
retry_config.py - 集中管理重試設定的模塊
"""
import random

class RetryConfig:
    """重試設定集中管理類"""
    
    # 默認配置
    DEFAULT = {
        'max_attempts': 3,
        'base_delay': 2.0,
        'backoff_factor': 2.0,
        'jitter': 0.5,
        'max_delay': 60
    }
    
    # 特定服務配置
    SERVICES = {
        'yahoo_finance': {
            'max_attempts': 4, 
            'base_delay': 5.0,
            'backoff_factor': 1.5
        },
        'line_notify': {
            'max_attempts': 3, 
            'max_delay': 120,
            'jitter': 0.3
        },
        'twse': {
            'max_attempts': 2, 
            'base_delay': 1.0,
            'backoff_factor': 3.0
        },
        'mops': {
            'max_attempts': 2,
            'base_delay': 2.0
        },
        'email': {
            'max_attempts': 3,
            'base_delay': 3.0,
            'backoff_factor': 2.5
        }
    }
    
    # 錯誤類型特定配置
    ERROR_TYPES = {
        'network': {
            'max_attempts': 5,
            'base_delay': 2.0,
            'backoff_factor': 1.5
        },
        'timeout': {
            'max_attempts': 3,
            'base_delay': 5.0,
            'backoff_factor': 2.0
        },
        'rate_limit': {
            'max_attempts': 2,
            'base_delay': 30.0,
            'backoff_factor': 3.0
        },
        'auth': {
            'max_attempts': 2,
            'base_delay': 10.0
        },
        'server': {
            'max_attempts': 4,
            'base_delay': 3.0
        },
        'client': {
            'max_attempts': 1,  # 客戶端錯誤一般不需要重試
            'base_delay': 1.0
        },
        'data': {
            'max_attempts': 2,
            'base_delay': 2.0
        }
    }
    
    @staticmethod
    def get(service_name=None, error_type=None):
        """
        獲取指定服務或錯誤類型的重試配置
        
        參數:
        - service_name: 服務名稱
        - error_type: 錯誤類型
        
        返回:
        - dict: 重試配置字典
        """
        config = RetryConfig.DEFAULT.copy()
        
        # 首先應用服務特定設置
        if service_name and service_name in RetryConfig.SERVICES:
            config.update(RetryConfig.SERVICES[service_name])
            
        # 然後應用錯誤類型設置，優先級更高
        if error_type and error_type in RetryConfig.ERROR_TYPES:
            config.update(RetryConfig.ERROR_TYPES[error_type])
            
        return config
    
    @staticmethod
    def calculate_delay(attempt, config=None, error_type=None, service_name=None):
        """
        計算重試延遲時間
        
        參數:
        - attempt: 當前嘗試次數 (從1開始)
        - config: 重試配置字典，None表示使用默認配置
        - error_type: 錯誤類型，用於自動獲取配置
        - service_name: 服務名稱，用於自動獲取配置
        
        返回:
        - float: 延遲時間(秒)
        """
        if config is None:
            config = RetryConfig.get(service_name, error_type)
        
        base_delay = config.get('base_delay', 2.0)
        backoff_factor = config.get('backoff_factor', 2.0)
        jitter = config.get('jitter', 0.5)
        max_delay = config.get('max_delay', 60)
        
        # 計算指數退避延遲
        delay = base_delay * (backoff_factor ** (attempt - 1))
        # 加入隨機抖動
        delay = delay * (1 + random.uniform(-jitter, jitter))
        # 限制最大延遲
        delay = min(delay, max_delay)
        
        return delay

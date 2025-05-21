"""
error_category.py - 錯誤分類與處理策略
"""
import re

class ErrorCategory:
    """錯誤分類與處理策略"""
    
    # 錯誤類型定義
    NETWORK = "network"   # 網路連接錯誤
    TIMEOUT = "timeout"   # 超時錯誤
    RATE_LIMIT = "rate_limit"  # 速率限制錯誤
    AUTH = "auth"         # 授權/認證錯誤
    SERVER = "server"     # 服務器錯誤
    CLIENT = "client"     # 客戶端錯誤
    DATA = "data"         # 數據錯誤
    VALIDATION = "validation"  # 驗證錯誤
    UNKNOWN = "unknown"   # 未知錯誤
    
    # 錯誤模式匹配規則 - 用於自動分類錯誤
    ERROR_PATTERNS = {
        NETWORK: [
            r'connection.*refused', 
            r'connection.*reset', 
            r'network.*unreachable',
            r'host.*unreachable',
            r'socket',
            r'eof.*error',
            r'connect\w*error',
            r'dns.*resolve',
            r'no route to host'
        ],
        TIMEOUT: [
            r'timeout', 
            r'timed out', 
            r'deadline exceeded'
        ],
        RATE_LIMIT: [
            r'429', 
            r'too many requests', 
            r'rate limit', 
            r'throttl',
            r'quota exceeded'
        ],
        AUTH: [
            r'401', 
            r'403', 
            r'authenticate', 
            r'authorization', 
            r'forbidden',
            r'permission denied',
            r'access denied',
            r'not authorized'
        ],
        SERVER: [
            r'5\d\d', 
            r'server error', 
            r'bad gateway', 
            r'service unavailable',
            r'internal server'
        ],
        CLIENT: [
            r'4\d\d', 
            r'client error', 
            r'bad request', 
            r'not found',
            r'method not allowed'
        ],
        DATA: [
            r'json.*error', 
            r'parse.*error', 
            r'invalid.*format',
            r'decode.*error',
            r'encode.*error',
            r'data.*missing'
        ],
        VALIDATION: [
            r'validation', 
            r'invalid.*input', 
            r'schema.*error',
            r'constraint',
            r'required.*field'
        ]
    }
    
    # 錯誤處理策略 - 按錯誤類型定義不同的重試策略
    STRATEGIES = {
        NETWORK: {
            'max_attempts': 5,
            'base_delay': 2.0,
            'backoff_factor': 1.5,
            'recoverable': True,
            'description': '網路連接錯誤 - 可能是暫時性問題，應該多次重試'
        },
        TIMEOUT: {
            'max_attempts': 3,
            'base_delay': 5.0,
            'backoff_factor': 2.0,
            'recoverable': True,
            'description': '超時錯誤 - 服務器可能忙碌，使用更長間隔重試'
        },
        RATE_LIMIT: {
            'max_attempts': 2,
            'base_delay': 30.0,
            'backoff_factor': 3.0,
            'recoverable': True,
            'description': '速率限制錯誤 - 需要較長等待時間後重試'
        },
        AUTH: {
            'max_attempts': 2,
            'base_delay': 10.0,
            'backoff_factor': 1.0,
            'recoverable': False,
            'description': '授權錯誤 - 可能需要更新憑據，有限重試'
        },
        SERVER: {
            'max_attempts': 4,
            'base_delay': 3.0,
            'backoff_factor': 1.8,
            'recoverable': True,
            'description': '服務器錯誤 - 伺服器問題，重試幾次'
        },
        CLIENT: {
            'max_attempts': 1,
            'base_delay': 1.0,
            'backoff_factor': 1.0,
            'recoverable': False,
            'description': '客戶端錯誤 - 通常是請求有問題，不重試'
        },
        DATA: {
            'max_attempts': 2,
            'base_delay': 2.0,
            'backoff_factor': 1.5,
            'recoverable': True,
            'description': '數據錯誤 - 可能是臨時數據問題，少量重試'
        },
        VALIDATION: {
            'max_attempts': 1,
            'base_delay': 1.0,
            'backoff_factor': 1.0,
            'recoverable': False,
            'description': '驗證錯誤 - 輸入數據有問題，不重試'
        },
        UNKNOWN: {
            'max_attempts': 3,
            'base_delay': 3.0,
            'backoff_factor': 2.0,
            'recoverable': True,
            'description': '未知錯誤 - 適度重試，以防萬一'
        }
    }
    
    @staticmethod
    def classify(error):
        """
        將錯誤分類
        
        參數:
        - error: 錯誤對象或錯誤訊息
        
        返回:
        - str: 錯誤類型
        """
        if error is None:
            return ErrorCategory.UNKNOWN
            
        # 將錯誤轉換為小寫字符串
        error_str = str(error).lower()
        
        # 檢查每個分類的模式
        for category, patterns in ErrorCategory.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, error_str):
                    return category
        
        # 特殊處理 HTTP 錯誤碼
        if re.search(r'(^|\D)5\d\d(\D|$)', error_str):
            return ErrorCategory.SERVER
        elif re.search(r'(^|\D)4\d\d(\D|$)', error_str):
            return ErrorCategory.CLIENT
        
        # 無法分類則返回未知
        return ErrorCategory.UNKNOWN
    
    @staticmethod
    def get_strategy(error_type):
        """
        獲取指定錯誤類型的處理策略
        
        參數:
        - error_type: 錯誤類型
        
        返回:
        - dict: 處理策略
        """
        if error_type in ErrorCategory.STRATEGIES:
            return ErrorCategory.STRATEGIES[error_type]
        return ErrorCategory.STRATEGIES[ErrorCategory.UNKNOWN]
    
    @staticmethod
    def is_recoverable(error_or_type):
        """
        檢查錯誤是否可恢復
        
        參數:
        - error_or_type: 錯誤對象、錯誤訊息或錯誤類型
        
        返回:
        - bool: 是否可恢復
        """
        # 如果輸入已經是錯誤類型字符串
        if isinstance(error_or_type, str) and error_or_type in ErrorCategory.STRATEGIES:
            error_type = error_or_type
        else:
            # 否則分類錯誤
            error_type = ErrorCategory.classify(error_or_type)
            
        return ErrorCategory.STRATEGIES[error_type].get('recoverable', True)
    
    @staticmethod
    def get_max_attempts(error_or_type):
        """
        獲取錯誤類型的最大重試次數
        
        參數:
        - error_or_type: 錯誤對象、錯誤訊息或錯誤類型
        
        返回:
        - int: 最大重試次數
        """
        # 如果輸入已經是錯誤類型字符串
        if isinstance(error_or_type, str) and error_or_type in ErrorCategory.STRATEGIES:
            error_type = error_or_type
        else:
            # 否則分類錯誤
            error_type = ErrorCategory.classify(error_or_type)
            
        return ErrorCategory.STRATEGIES[error_type].get('max_attempts', 3)
    
    @staticmethod
    def describe(error_or_type):
        """
        獲取錯誤類型的描述
        
        參數:
        - error_or_type: 錯誤對象、錯誤訊息或錯誤類型
        
        返回:
        - str: 錯誤類型描述
        """
        # 如果輸入已經是錯誤類型字符串
        if isinstance(error_or_type, str) and error_or_type in ErrorCategory.STRATEGIES:
            error_type = error_or_type
        else:
            # 否則分類錯誤
            error_type = ErrorCategory.classify(error_or_type)
            
        return ErrorCategory.STRATEGIES[error_type].get('description', '未知錯誤類型')

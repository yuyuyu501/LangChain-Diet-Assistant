from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class DatabaseBase(ABC):
    """数据库操作基类"""
    
    @abstractmethod
    async def connect(self) -> None:
        """建立数据库连接"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开数据库连接"""
        pass
    
    @abstractmethod
    async def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """执行SQL查询"""
        pass
    
    @abstractmethod
    async def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict]:
        """获取单条记录"""
        pass
    
    @abstractmethod
    async def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """获取多条记录"""
        pass
    
    @abstractmethod
    async def begin(self) -> None:
        """开始事务"""
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """提交事务"""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """回滚事务"""
        pass 
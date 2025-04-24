from pydantic import BaseModel
from datetime import datetime

class SessionBase(BaseModel):
    """会话基础模型"""
    user_id: int
    session_name: str

class SessionCreate(SessionBase):
    """会话创建模型"""
    pass

class SessionInDB(SessionBase):
    """数据库中的会话模型"""
    session_id: int
    created_at: datetime
    last_message_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True 
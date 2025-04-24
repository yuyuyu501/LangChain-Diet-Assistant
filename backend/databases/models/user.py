from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: str
    
class UserCreate(UserBase):
    """用户创建模型"""
    password: str
    
class UserInDB(UserBase):
    """数据库中的用户模型"""
    user_id: int
    hashed_password: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    
    class Config:
        from_attributes = True 
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from pydantic import BaseModel, Field  # 添加Field导入
from typing import List, Optional  # 确保导入List类型

class ChatRecordBase(BaseModel):
    """聊天记录基础模型"""
    session_id: int
    user_message: str
    
class ChatRecordCreate(ChatRecordBase):
    """聊天记录创建模型"""
    pass

class ChatRecordInDB(ChatRecordBase):
    """数据库中的聊天记录模型"""
    record_id: int
    bot_response: Optional[str] = None
    created_at: datetime
    response_at: Optional[datetime] = None

    class Config:
        from_attributes = True 

class ChatImageBase(BaseModel):
    record_id: int
    images: List[bytes] = Field(..., max_items=5)

class ChatImageCreate(ChatImageBase):
    pass

class ChatImageInDB(ChatImageBase):
    class Config:
        orm_mode = True
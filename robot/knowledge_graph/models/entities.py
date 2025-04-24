from typing import List, Dict, Optional
from pydantic import BaseModel

class FoodEntity(BaseModel):
    """食材实体 - 对应food_base表"""
    id: int
    name: str
    category: str
    properties: Dict[str, str]  # JSON格式存储的性质（寒热温凉）
    season: List[str]  # JSON格式存储的适用季节
    created_at: Optional[str]
    updated_at: Optional[str]

class EffectEntity(BaseModel):
    """功效实体 - 对应effects表"""
    id: int
    name: str
    description: str
    related_symptoms: List[str]  # JSON格式存储的相关症状
    created_at: Optional[str]
    updated_at: Optional[str] 
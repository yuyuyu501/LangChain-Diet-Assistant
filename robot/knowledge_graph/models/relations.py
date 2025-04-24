from typing import List, Dict, Optional
from pydantic import BaseModel

class FoodRelation(BaseModel):
    """食材关系 - 对应food_relations表"""
    id: int
    source_id: int
    target_id: int
    relation_type: str  # ENUM('相生', '相克', '营养互补')
    weight: float  # 关系强度
    evidence: str  # 依据
    created_at: Optional[str]
    updated_at: Optional[str]

class NutrientRelation(BaseModel):
    """营养成分关系 - 对应food_nutrients表"""
    id: int
    food_id: int
    nutrient_name: str
    amount: float
    unit: str
    created_at: Optional[str]

class EffectRelation(BaseModel):
    """功效关系 - 对应food_effects表"""
    id: int
    food_id: int
    effect_id: int
    confidence: float
    reference_info: Optional[str]  # 参考依据
    created_at: Optional[str] 
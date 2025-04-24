"""
全局变量模块
"""
from .llms import model

# 当前用户ID
current_user_id = None  # 初始化为 None，在需要时设置具体值

# 当前会话ID
current_session_id = None 

# 当前使用的模型
current_model = model  # 默认使用 llms 中的默认模型 

# 当前AI规则
current_ai_rules = None  # 存储用户的个性化AI规则

# 当前规则启用状态
current_rules_enabled = False  # 存储规则是否启用的状态 
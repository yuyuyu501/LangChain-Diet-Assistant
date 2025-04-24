from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    """应用配置"""
    # Neo4j配置
    NEO4J_URI: str = "neo4j+s://6ffdfd27.databases.neo4j.io"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "Ci--01lfzgrxOFanTMt3IKh_ENvCe85hpd1h5x4iFy8"
    
    # LangChain配置
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "default-project"
    
    # API密钥
    TAVILY_API_KEY: Optional[str] = None
    ZHIPUAI_API_KEY: Optional[str] = None
    
    # 数据库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "root123"
    MYSQL_DATABASE: str = "robot"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # JWT配置
    JWT_SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 邮件配置
    SMTP_SERVER: str = "smtp.qq.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "yuyuyu_501@qq.com"
    EMAIL_PASSWORD: str = "ikrdcgvfyktwbieh"
    SMTP_SENDER: str = "yuyuyu_501@qq.com"
    
    # 其他配置
    SESSION_TIMEOUT: int = 3600

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """获取应用配置单例"""
    return Settings() 
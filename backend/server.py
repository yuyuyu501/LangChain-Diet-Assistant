from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
import aiomysql
from datetime import datetime, timedelta
import os
import uvicorn
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import sys
from pathlib import Path
import jwt
import bcrypt
import random
import string
from email.mime.text import MIMEText
import smtplib
from .utils.config import get_settings
from .utils.email.sender import email_sender
from .utils.logger import default_logger as logger
import base64
from uuid import uuid4
import json
from .utils.feed.feedback_processor import process_feedback

import sys
import os
from pathlib import Path

# 确保 backend 目录在 sys.path 中
ROOT_DIR = Path(__file__).resolve().parent  # 这个应该是 backend 目录
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

if str(ROOT_DIR.parent) not in sys.path:  # 确保父目录（代码根目录）也在 sys.path 里
    sys.path.append(str(ROOT_DIR.parent))


# 加载环境变量
env_path = os.path.join(ROOT_DIR, '.env')
load_dotenv(env_path)

# JWT配置
settings = get_settings()
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# 数据库连接池
pool = None

# 验证码存储（实际应用中应该使用Redis等）
verification_codes: Dict[str, str] = {}

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    global pool
    try:
        settings = get_settings()
        pool = await aiomysql.create_pool(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            db=settings.MYSQL_DATABASE,
            charset='utf8mb4',
            autocommit=True,
            minsize=1,
            maxsize=10
        )
        print("数据库连接池创建成功")
    except Exception as e:
        print(f"数据库连接池创建失败: {str(e)}")
        raise
    yield
    # 关闭时执行
    if pool:
        pool.close()
        await pool.wait_closed()
        print("数据库连接池已关闭")

# 创建 FastAPI 应用
app = FastAPI(lifespan=lifespan)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr
    verification_code: str

# 添加饮食记录模型
class DietaryRecord(BaseModel):
    meal_type: str  # varchar(20)
    food_items: Any  # json
    calories: float = 0.0  # float
    protein: float = 0.0  # float
    carbs: float = 0.0  # float
    fat: float = 0.0  # float
    satisfaction: int = 3  # int
    notes: Optional[str] = None  # text
    recorded_at: datetime  # timestamp

class UserLogin(BaseModel):
    identifier: str  # 可以是用户名或邮箱
    password: str

class EmailVerification(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    email: EmailStr
    new_password: str
    verification_code: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class SessionCreate(BaseModel):
    session_name: str = "新对话"

class UserPreferences(BaseModel):
    theme: str
    language: str
    model: str
    ai_rules: Optional[str] = None
    is_rules_enabled: Optional[bool] = False

class SessionNameUpdate(BaseModel):
    new_name: str

# 用户资料模型
class UserProfile(BaseModel):
    user_id: int
    age: int
    gender: str
    height: float
    weight: float
    health_conditions: str
    allergies: str
    diet_type: str
    spicy_level: str
    favorite_ingredients: str
    disliked_ingredients: str
    cooking_time_preference: int
    calorie_target: int
    protein_target: int
    carb_target: int
    fat_target: int
    weight_goal: float

# 健康建议相关模型
class HealthAdviceResponse(BaseModel):
    id: int
    user_id: int
    content: str
    symptoms: Optional[str]
    recommended_foods: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_favorite: Optional[bool]
    rating: Optional[float]
    feedback: Optional[str]

# 工具函数
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

async def send_verification_email(email: str, code: str):
    """发送验证码邮件"""
    try:
        # 直接使用专门的验证码发送方法
        success = await email_sender.send_verification_code(email, code)
        if not success:
            logger.error("发送验证码邮件失败")
            return False
        return True
    except Exception as e:
        logger.error(f"发送验证码邮件时出错: {str(e)}")
        return False

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="无效的认证凭据")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="无效的认证凭据")

    if pool is None:
        raise HTTPException(status_code=500, detail="数据库连接未初始化")
        
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = await cur.fetchone()
                if user is None:
                    raise HTTPException(status_code=401, detail="用户不存在")
                return user
    except Exception as e:
        print(f"数据库查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

# 修改验证码相关函数
async def save_verification_code(email: str, code: str):
    """将验证码保存到数据库"""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 先将MySQL会话时区设置为北京时间
                await cur.execute("SET time_zone = '+08:00'")
                
                # 使用MySQL的时间函数来处理时间，确保时区一致
                await cur.execute(
                    """
                    INSERT INTO verification_codes (email, code, created_at, expires_at, is_used)
                    VALUES (%s, %s, NOW(), DATE_ADD(NOW(), INTERVAL 5 MINUTE), 0)
                    """,
                    (email, code)
                )
                await conn.commit()
                logger.info(f"验证码保存成功: email={email}")
    except Exception as e:
        logger.error(f"保存验证码失败: email={email}, error={str(e)}")
        raise

async def verify_code(email: str, code: str) -> bool:
    """验证验证码是否有效"""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 设置时区为北京时间
                await cur.execute("SET time_zone = '+08:00'")
                
                # 验证码验证
                await cur.execute(
                    """
                    SELECT id 
                    FROM verification_codes
                    WHERE email = %s 
                    AND code = %s 
                    AND expires_at > NOW()
                    AND is_used = 0
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (email, code)
                )
                result = await cur.fetchone()
                
                if result:
                    # 标记验证码为已使用
                    await cur.execute(
                        "UPDATE verification_codes SET is_used = 1 WHERE id = %s",
                        (result[0],)
                    )
                    await conn.commit()
                    logger.info(f"验证码验证成功: email={email}")
                    return True
                    
                logger.error(f"验证码验证失败: email={email}")
                return False
                
    except Exception as e:
        logger.error(f"验证码验证过程出错: {str(e)}")
        return False

# 修改注册路由
@app.post("/auth/register")
async def register(user: UserCreate):
    """用户注册"""
    # 验证验证码
    if not await verify_code(user.email, user.verification_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误或已过期"
        )

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # 检查用户名是否已存在
            await cur.execute(
                "SELECT user_id FROM users WHERE username = %s",
                (user.username,)
            )
            if await cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已存在"
                )

            # 检查邮箱是否已存在
            await cur.execute(
                "SELECT user_id FROM users WHERE email = %s",
                (user.email,)
            )
            if await cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已被注册"
                )

            # 创建新用户
            password_hash = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
            await cur.execute(
                """
                INSERT INTO users (username, password_hash, email)
                VALUES (%s, %s, %s)
                """,
                (user.username, password_hash.decode(), user.email)
            )
            await conn.commit()
            
            return {
                "success": True,
                "message": "注册成功"
            }

@app.post("/auth/login")
async def login(form_data: UserLogin):
    """用户登录（支持用户名或邮箱登录）"""
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            is_email = '@' in form_data.identifier
            if is_email:
                await cur.execute(
                    "SELECT * FROM users WHERE email = %s",
                    (form_data.identifier,)
                )
            else:
                await cur.execute(
                    "SELECT * FROM users WHERE username = %s",
                    (form_data.identifier,)
                )
            user = await cur.fetchone()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名/邮箱或密码错误"
                )
            if not bcrypt.checkpw(
                form_data.password.encode('utf-8'),
                user['password_hash'].encode('utf-8')
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名/邮箱或密码错误"
                )
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user['username']},
                expires_delta=access_token_expires
            )
            await cur.execute(
                "SELECT device_id FROM user_devices WHERE user_id = %s",
                (user['user_id'],)
            )
            device = await cur.fetchone()
            if device:
                device_id = device['device_id']
            else:
                device_id = str(uuid4())
                device_name = "Web Browser"
                device_type = "web"
                await cur.execute(
                    "INSERT INTO user_devices (user_id, device_id, device_name, device_type, last_active_at) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)",
                    (user['user_id'], device_id, device_name, device_type)
                )
                await conn.commit()
            return {
                "success": True,
                "message": "登录成功",
                "data": {
                    "token": access_token,
                    "user": {
                        "user_id": user['user_id'],
                        "username": user['username'],
                        "email": user['email'],
                        "device_id": device_id  # 返回设备ID
                    }
                }
            }

# 发送验证码路由
@app.post("/auth/send-verification")
async def send_verification(email_data: EmailVerification):
    """发送验证码"""
    try:
        # 生成6位数字验证码
        code = generate_verification_code()
        
        # 发送验证码邮件
        if await send_verification_email(email_data.email, code):
            # 保存验证码到数据库
            await save_verification_code(email_data.email, code)
            return {
                "success": True,
                "message": "验证码已发送，请查收邮件"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="验证码发送失败，请稍后重试"
            )
    except Exception as e:
        logger.error(f"发送验证码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证码发送失败，请稍后重试"
        )

# 修改重置密码路由
@app.post("/auth/reset-password")
async def reset_password(reset_data: PasswordReset):
    """重置密码"""
    try:
        # 1. 验证验证码
        logger.info(f"正在验证邮箱 {reset_data.email} 的验证码")
        valid = await verify_code(reset_data.email, reset_data.verification_code)
        if not valid:
            logger.error(f"验证码验证失败: email={reset_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误或已过期"
            )
        
        # 2. 更新密码
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 先检查用户是否存在
                await cur.execute(
                    "SELECT user_id FROM users WHERE email = %s",
                    (reset_data.email,)
                )
                if not await cur.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="该邮箱未注册"
                    )
                
                # 更新密码
                password_hash = bcrypt.hashpw(reset_data.new_password.encode(), bcrypt.gensalt())
                await cur.execute(
                    """
                    UPDATE users 
                    SET password_hash = %s 
                    WHERE email = %s
                    """,
                    (password_hash.decode(), reset_data.email)
                )
                await conn.commit()
                
        logger.info(f"密码重置成功: email={reset_data.email}")
        return {"success": True, "message": "密码重置成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置密码过程出错: email={reset_data.email}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重置密码失败，请稍后重试"
        )

@app.get("/auth/user-info")
async def get_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "data": {
            "id": current_user['user_id'],
            "username": current_user['username'],
            "email": current_user['email']
        }
    }

@app.put("/auth/user-info")
async def update_user_info(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            updates = []
            values = []
            if user_update.username:
                updates.append("username = %s")
                values.append(user_update.username)
            if user_update.email:
                updates.append("email = %s")
                values.append(user_update.email)
            
            if not updates:
                return {"success": True, "message": "无更新内容"}

            values.append(current_user['user_id'])
            query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s"
            await cur.execute(query, values)
            await conn.commit()

            return {"success": True, "message": "用户信息更新成功"}

@app.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    # 这里可以添加token黑名单等逻辑
    return {"success": True, "message": "登出成功"}

# 会话相关路由
@app.post("/sessions/create")
async def create_session(
    current_user: dict = Depends(get_current_user)
):
    """创建新会话"""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 创建新会话
                await cur.execute(
                    """
                    INSERT INTO robot_sessions (user_id, session_name)
                    VALUES (%s, %s)
                    """,
                    (current_user['user_id'], "新对话")
                )
                session_id = cur.lastrowid
                await conn.commit()

                # 获取创建的会话信息
                await cur.execute(
                    """
                    SELECT session_id, session_name, created_at
                    FROM robot_sessions
                    WHERE session_id = %s
                    """,
                    (session_id,)
                )
                session = await cur.fetchone()
                
                return {
                    "success": True,
                    "message": "会话创建成功",
                    "data": {
                        "session_id": session[0],
                        "session_name": session[1],
                        "created_at": session[2]
                    }
                }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions")
async def list_sessions(current_user: dict = Depends(get_current_user)):
    """获取用户的所有会话"""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT session_id, session_name, created_at,
                           COALESCE(
                               (SELECT MAX(created_at)
                                FROM chat_records
                                WHERE session_id = s.session_id),
                               s.created_at
                           ) as last_message_at
                    FROM robot_sessions s
                    WHERE user_id = %s
                    ORDER BY last_message_at DESC
                    """,
                    (current_user['user_id'],)
                )
                sessions = await cur.fetchall()
                
                return {
                    "success": True,
                    "data": {
                        "sessions": [
                            {
                                "session_id": session[0],
                                "session_name": session[1],
                                "created_at": session[2],
                                "last_message_at": session[3]
                            }
                            for session in sessions
                        ]
                    }
                }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    current_user: dict = Depends(get_current_user)
):
    """删除指定会话"""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 验证会话所有权
                await cur.execute(
                    "SELECT 1 FROM robot_sessions WHERE session_id = %s AND user_id = %s",
                    (session_id, current_user['user_id'])
                )
                if not await cur.fetchone():
                    raise HTTPException(status_code=404, detail="会话不存在或无权访问")
                
                # 先删除聊天记录
                await cur.execute(
                    "DELETE FROM chat_records WHERE session_id = %s",
                    (session_id,)
                )
                await conn.commit()
                
                # 删除会话
                await cur.execute(
                    "DELETE FROM robot_sessions WHERE session_id = %s",
                    (session_id,)
                )
                await conn.commit()
                
                # 检查用户是否还有其他会话
                await cur.execute(
                    "SELECT COUNT(*) FROM robot_sessions WHERE user_id = %s",
                    (current_user['user_id'],)
                )
                session_count = (await cur.fetchone())[0]
                
                # 如果没有会话了，创建一个新会话
                if session_count == 0:
                    await cur.execute(
                        """
                        INSERT INTO robot_sessions (user_id, session_name)
                        VALUES (%s, %s)
                        """,
                        (current_user['user_id'], "新对话")
                    )
                    await conn.commit()
                    
                return {"success": True, "message": "会话已删除"}
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/clear/all")
async def clear_all_sessions(current_user: dict = Depends(get_current_user)):
    """清空用户的所有会话"""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 先删除所有聊天记录
                await cur.execute(
                    """
                    DELETE cr FROM chat_records cr
                    INNER JOIN robot_sessions rs ON cr.session_id = rs.session_id
                    WHERE rs.user_id = %s
                    """,
                    (current_user['user_id'],)
                )
                await conn.commit()
                
                # 删除所有会话
                await cur.execute(
                    "DELETE FROM robot_sessions WHERE user_id = %s",
                    (current_user['user_id'],)
                )
                await conn.commit()
                
                # 最后创建一个新的默认会话
                await cur.execute(
                    """
                    INSERT INTO robot_sessions (user_id, session_name)
                    VALUES (%s, %s)
                    """,
                    (current_user['user_id'], "新对话")
                )
                await conn.commit()
                
                return {"success": True, "message": "所有会话已清空"}
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/sessions/{session_id}/name")
async def update_session_name(
    session_id: int,
    name_update: SessionNameUpdate,
    current_user: dict = Depends(get_current_user)
):
    logger.info(f"收到更新会话名称请求: session_id={session_id}, new_name={name_update.new_name}")
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 验证会话所有权
                await cur.execute(
                    "SELECT 1 FROM robot_sessions WHERE session_id = %s AND user_id = %s",
                    (session_id, current_user['user_id'])
                )
                if not await cur.fetchone():
                    raise HTTPException(status_code=404, detail="会话不存在或无权访问")
                
                # 更新会话名称
                await cur.execute(
                    """
                    UPDATE robot_sessions 
                    SET session_name = %s 
                    WHERE session_id = %s AND user_id = %s
                    """,
                    (name_update.new_name, session_id, current_user['user_id'])
                )
                await conn.commit()
                
                logger.info(f"会话名称更新成功: session_id={session_id}, new_name={name_update.new_name}")
                return {"success": True, "message": "会话名称已更新"}
                
    except Exception as e:
        logger.error(f"更新会话名称失败: session_id={session_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/history/{session_id}")
async def get_chat_history(
    session_id: int,
    current_user: dict = Depends(get_current_user)
):
    """获取聊天历史"""
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # 验证会话所有权
            await cur.execute(
                """
                SELECT session_id FROM robot_sessions 
                WHERE session_id = %s AND user_id = %s
                """,
                (session_id, current_user['user_id'])
            )
            if not await cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="会话不存在"
                )
            
            # 获取聊天记录，包括图片信息
            await cur.execute(
                """
                SELECT cr.record_id, cr.user_message, cr.bot_response, cr.created_at,
                       cr.has_images,
                       CASE WHEN cr.has_images THEN
                           JSON_ARRAY(
                               CASE WHEN ci.image_1 IS NOT NULL THEN 1 ELSE NULL END,
                               CASE WHEN ci.image_2 IS NOT NULL THEN 2 ELSE NULL END,
                               CASE WHEN ci.image_3 IS NOT NULL THEN 3 ELSE NULL END,
                               CASE WHEN ci.image_4 IS NOT NULL THEN 4 ELSE NULL END,
                               CASE WHEN ci.image_5 IS NOT NULL THEN 5 ELSE NULL END
                           )
                       ELSE NULL END as image_indexes
                FROM chat_records cr
                LEFT JOIN chat_images ci ON cr.record_id = ci.record_id
                WHERE cr.session_id = %s 
                ORDER BY cr.created_at ASC
                """,
                (session_id,)
            )
            records = await cur.fetchall()
            
            # 格式化消息记录
            messages = []
            for record in records:
                if record['user_message']:
                    message = {
                        "role": "user",
                        "content": record['user_message'],
                        "timestamp": record['created_at']
                    }
                    # 如果消息包含图片，添加图片信息
                    if record['has_images'] and record['image_indexes']:
                        import json
                        # 解析JSON数组并过滤掉null值
                        try:
                            image_indexes = [i for i in json.loads(record['image_indexes']) if i is not None]
                            image_list = []
                            if image_indexes:
                                # 获取图片数据
                                image_columns = [f"image_{i}" for i in image_indexes]
                                await cur.execute(
                                    f"""
                                    SELECT {', '.join(image_columns)}
                                    FROM chat_images
                                    WHERE record_id = %s
                                    """,
                                    (record['record_id'],)
                                )
                                image_data = await cur.fetchone()
                                if image_data:
                                    for i, img in zip(image_indexes, image_data.values()):
                                        if img:
                                            image_list.append({
                                                "index": i,
                                                "data": base64.b64encode(img).decode('utf-8')
                                            })
                            message["images"] = image_list
                        except Exception as e:
                            print(f"处理图片数据时出错: {str(e)}")
                            message["images"] = []
                    messages.append(message)
                
                if record['bot_response']:
                    messages.append({
                        "role": "assistant",
                        "content": record['bot_response'],
                        "timestamp": record['created_at']
                    })
            
            return {
                "success": True,
                "data": {
                    "messages": messages
                }
            }

@app.post("/clear/{session_id}")
async def clear_history(
    session_id: int,
    current_user: dict = Depends(get_current_user)
):
    """清空会话历史"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # 验证会话所有权
            await cur.execute(
                """
                SELECT session_id FROM robot_sessions 
                WHERE session_id = %s AND user_id = %s
                """,
                (session_id, current_user['user_id'])
            )
            if not await cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="会话不存在"
                )
            
            # 清空聊天记录
            await cur.execute(
                "DELETE FROM chat_records WHERE session_id = %s",
                (session_id,)
            )
            await conn.commit()
            
            return {
                "success": True,
                "message": "历史记录已清空"
            }

@app.get("/sessions/{session_id}/latest-message")
async def get_latest_message(
    session_id: int,
    current_user: dict = Depends(get_current_user)
):
    """获取会话最新消息"""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 验证会话所有权
                await cur.execute(
                    "SELECT 1 FROM robot_sessions WHERE session_id = %s AND user_id = %s",
                    (session_id, current_user['user_id'])
                )
                if not await cur.fetchone():
                    raise HTTPException(status_code=404, detail="会话不存在或无权访问")
                
                # 获取最新的用户消息
                await cur.execute(
                    """
                    SELECT user_message
                    FROM chat_records
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (session_id,)
                )
                result = await cur.fetchone()
                
                if not result:
                    return {
                        "success": True,
                        "data": {
                            "message": None
                        }
                    }
                
                return {
                    "success": True,
                    "data": {
                        "message": result[0]
                    }
                }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/stats")
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """获取用户统计信息"""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 获取会话数
                await cur.execute(
                    "SELECT COUNT(*) FROM robot_sessions WHERE user_id = %s",
                    (current_user["user_id"],)
                )
                total_sessions = (await cur.fetchone())[0]

                # 获取消息数和token数
                await cur.execute(
                    """
                    SELECT COUNT(*) as total_conversations,
                           COALESCE(SUM(CHAR_LENGTH(user_message) + CHAR_LENGTH(COALESCE(bot_response, ''))), 0) as total_tokens
                    FROM chat_records cr
                    JOIN robot_sessions rs ON cr.session_id = rs.session_id
                    WHERE rs.user_id = %s
                    """,
                    (current_user["user_id"],)
                )
                result = await cur.fetchone()
                total_conversations = result[0]
                total_tokens = result[1]

                # 获取最后活跃时间
                await cur.execute(
                    """
                    SELECT MAX(cr.created_at) as last_active_at
                    FROM chat_records cr
                    JOIN robot_sessions rs ON cr.session_id = rs.session_id
                    WHERE rs.user_id = %s
                    """,
                    (current_user["user_id"],)
                )
                last_active_at = (await cur.fetchone())[0]

                return {
                    "success": True,
                    "data": {
                        "total_sessions": total_sessions,
                        "total_conversations": total_conversations,
                        "total_tokens": total_tokens,
                        "last_active_at": last_active_at
                    }
                }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取用户统计信息失败: {str(e)}"
        )

@app.get("/user/preferences")
async def get_user_preferences(current_user: dict = Depends(get_current_user)):
    """获取用户偏好设置"""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT theme, language, model, message_count, total_tokens, 
                           last_active_at, total_sessions, total_conversations,
                           ai_rules, is_rules_enabled
                    FROM user_preferences 
                    WHERE user_id = %s 
                    LIMIT 1
                    """,
                    (current_user["user_id"],)
                )
                result = await cur.fetchone()
                if not result:
                    # 如果没有记录，创建默认记录
                    default_preferences = {
                        "theme": "light",
                        "language": "zh",
                        "model": "glm-4-plus",
                        "message_count": 0,
                        "total_tokens": 0,
                        "last_active_at": None,
                        "total_sessions": 0,
                        "total_conversations": 0,
                        "ai_rules": "",
                        "is_rules_enabled": False
                    }
                    
                    await cur.execute(
                        """
                        INSERT INTO user_preferences 
                        (user_id, theme, language, model, message_count, total_tokens, 
                         last_active_at, total_sessions, total_conversations, 
                         ai_rules, is_rules_enabled)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            current_user["user_id"],
                            default_preferences["theme"],
                            default_preferences["language"],
                            default_preferences["model"],
                            default_preferences["message_count"],
                            default_preferences["total_tokens"],
                            default_preferences["last_active_at"],
                            default_preferences["total_sessions"],
                            default_preferences["total_conversations"],
                            default_preferences["ai_rules"],
                            default_preferences["is_rules_enabled"]
                        )
                    )
                    await conn.commit()
                    return {"success": True, "data": default_preferences}
                
                return {
                    "success": True,
                    "data": {
                        "theme": result[0],
                        "language": result[1],
                        "model": result[2],
                        "message_count": result[3],
                        "total_tokens": result[4],
                        "last_active_at": result[5],
                        "total_sessions": result[6],
                        "total_conversations": result[7],
                        "ai_rules": result[8] or "",
                        "is_rules_enabled": bool(result[9])
                    }
                }
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取用户偏好设置失败: {str(e)}"
        )

@app.put("/user/preferences")
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: dict = Depends(get_current_user)
):
    """更新用户偏好设置"""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 检查是否存在记录
                await cur.execute(
                    "SELECT 1 FROM user_preferences WHERE user_id = %s",
                    (current_user["user_id"],)
                )
                exists = await cur.fetchone()
                
                if exists:
                    # 更新现有记录
                    await cur.execute(
                        """
                        UPDATE user_preferences 
                        SET theme = %s,
                            language = %s,
                            model = %s,
                            ai_rules = %s,
                            is_rules_enabled = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                        """,
                        (
                            preferences.theme,
                            preferences.language,
                            preferences.model,
                            preferences.ai_rules,
                            preferences.is_rules_enabled,
                            current_user["user_id"]
                        )
                    )
                else:
                    # 插入新记录
                    await cur.execute(
                        """
                        INSERT INTO user_preferences 
                        (user_id, theme, language, model, ai_rules, is_rules_enabled, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        (
                            current_user["user_id"],
                            preferences.theme,
                            preferences.language,
                            preferences.model,
                            preferences.ai_rules,
                            preferences.is_rules_enabled
                        )
                    )
                
                await conn.commit()
                return {"success": True, "message": "偏好设置更新成功"}
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"更新用户偏好设置失败: {str(e)}"
        )

@app.put("/user/stats/update")
async def update_user_stats(current_user: dict = Depends(get_current_user)):
    """更新用户统计信息"""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 获取会话数
                await cur.execute(
                    "SELECT COUNT(*) FROM robot_sessions WHERE user_id = %s",
                    (current_user["user_id"],)
                )
                total_sessions = (await cur.fetchone())[0]
                
                # 获取消息数和Token数
                await cur.execute(
                    """
                    SELECT COUNT(*), COALESCE(SUM(LENGTH(user_message) + LENGTH(COALESCE(bot_response, ''))), 0)
                    FROM chat_records cr
                    JOIN robot_sessions rs ON cr.session_id = rs.session_id
                    WHERE rs.user_id = %s
                    """,
                    (current_user["user_id"],)
                )
                message_count, total_tokens = await cur.fetchone()
                
                # 更新用户统计信息
                await cur.execute(
                    """
                    UPDATE user_preferences
                    SET message_count = %s,
                        total_tokens = %s,
                        total_sessions = %s,
                        last_active_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                    """,
                    (message_count, total_tokens, total_sessions, current_user["user_id"])
                )
                await conn.commit()
                
                return {
                    "success": True,
                    "message": "统计信息已更新"
                }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 新增用户资料
@app.post("/api/user_profiles/")
async def create_user_profile(user_profile: UserProfile):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO user_profiles (user_id, age, gender, height, weight, health_conditions, allergies, diet_type, spicy_level, favorite_ingredients, disliked_ingredients, cooking_time_preference, calorie_target, protein_target, carb_target, fat_target, weight_goal)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (user_profile.user_id, user_profile.age, user_profile.gender, user_profile.height, user_profile.weight, json.dumps(user_profile.health_conditions), json.dumps(user_profile.allergies), user_profile.diet_type, user_profile.spicy_level, json.dumps(user_profile.favorite_ingredients), json.dumps(user_profile.disliked_ingredients), user_profile.cooking_time_preference, user_profile.calorie_target, user_profile.protein_target, user_profile.carb_target, user_profile.fat_target, user_profile.weight_goal)
            )
            await conn.commit()
            return {"success": True, "message": "用户资料已创建"}

# 获取用户资料
@app.get("/api/user_profiles/{user_id}")
async def get_user_profile(user_id: int):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT 
                    user_id, 
                    age, 
                    gender, 
                    height, 
                    weight, 
                    health_conditions,
                    allergies,
                    diet_type, 
                    spicy_level, 
                    favorite_ingredients,
                    disliked_ingredients,
                    cooking_time_preference, 
                    calorie_target, 
                    protein_target, 
                    carb_target, 
                    fat_target, 
                    weight_goal 
                FROM user_profiles 
                WHERE user_id = %s
                """,
                (user_id,)
            )
            user_profile = await cur.fetchone()
            if user_profile is None:
                raise HTTPException(status_code=404, detail="用户资料未找到")
            # 处理JSON字段
            if user_profile['allergies']:
                try:
                    user_profile['allergies'] = json.loads(user_profile['allergies'])
                except json.JSONDecodeError:
                    user_profile['allergies'] = []
            else:
                user_profile['allergies'] = []
            if user_profile['favorite_ingredients']:
                try:
                    user_profile['favorite_ingredients'] = json.loads(user_profile['favorite_ingredients'])
                except json.JSONDecodeError:
                    user_profile['favorite_ingredients'] = []
            else:
                user_profile['favorite_ingredients'] = []
            if user_profile['disliked_ingredients']:
                try:
                    user_profile['disliked_ingredients'] = json.loads(user_profile['disliked_ingredients'])
                except json.JSONDecodeError:
                    user_profile['disliked_ingredients'] = []
            else:
                user_profile['disliked_ingredients'] = []
            return {"success": True, "data": user_profile}

# 更新用户资料
@app.put("/api/user_profiles/{user_id}") 
async def update_user_profile(user_id: int, user_profile: UserProfile):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE user_profiles SET 
                    age = %s, 
                    gender = %s, 
                    height = %s, 
                    weight = %s, 
                    health_conditions = %s, 
                    allergies = %s, 
                    diet_type = %s, 
                    spicy_level = %s, 
                    favorite_ingredients = %s, 
                    disliked_ingredients = %s, 
                    cooking_time_preference = %s, 
                    calorie_target = %s, 
                    protein_target = %s, 
                    carb_target = %s, 
                    fat_target = %s, 
                    weight_goal = %s
                WHERE user_id = %s
                """,
                (
                    user_profile.age,
                    user_profile.gender,
                    user_profile.height,
                    user_profile.weight,
                    user_profile.health_conditions,  # 直接使用字符串
                    user_profile.allergies,         # 直接使用字符串
                    user_profile.diet_type,
                    user_profile.spicy_level,
                    user_profile.favorite_ingredients,  # 直接使用字符串
                    user_profile.disliked_ingredients,  # 直接使用字符串
                    user_profile.cooking_time_preference,
                    user_profile.calorie_target,
                    user_profile.protein_target,
                    user_profile.carb_target,
                    user_profile.fat_target,
                    user_profile.weight_goal,
                    user_id
                )
            )

             # 计算BMI
            if user_profile.height and user_profile.weight:
                # BMI = 体重(kg) / (身高(m))²
                height_in_meters = user_profile.height / 100  # 转换为米
                bmi_value = round(user_profile.weight / (height_in_meters * height_in_meters), 1)

                # 检查是否存在当天的记录
                await cur.execute(
                    """
                    SELECT id FROM bmi_records 
                    WHERE user_id = %s AND DATE(recorded_at) = CURDATE()
                    """,
                    (user_id,)
                )
                existing_record = await cur.fetchone()

                if existing_record:
                    # 更新当天的记录
                    await cur.execute(
                        """
                        UPDATE bmi_records 
                        SET bmi_value = %s 
                        WHERE id = %s
                        """,
                        (bmi_value, existing_record[0])
                    )
                else:
                    # 插入新记录
                    await cur.execute(
                        """
                        INSERT INTO bmi_records (user_id, bmi_value, recorded_at)
                        VALUES (%s, %s, NOW())
                        """,
                        (user_id, bmi_value)
                    )
            await conn.commit()
            return {"success": True, "message": "用户资料已更新"}

# 获取同步状态
@app.get("/api/sync/status")
async def get_sync_status(device_id: str, current_user: dict = Depends(get_current_user)):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # 检查设备是否存在
            await cur.execute(
                "SELECT * FROM user_devices WHERE device_id = %s AND user_id = %s",
                (device_id, current_user['user_id'])
            )
            device = await cur.fetchone()
            if not device:
                raise HTTPException(status_code=404, detail="设备未找到")
            
            # 获取最后同步时间
            await cur.execute(
                "SELECT last_sync_at FROM user_sync_status WHERE user_id = %s",
                (current_user['user_id'],)
            )
            sync_status = await cur.fetchone()
            last_sync_at = sync_status['last_sync_at'] if sync_status else None

            return {
                "success": True,
                "data": {
                    "lastSyncAt": last_sync_at
                }
            }

# 标记数据为已同步
@app.post("/api/sync/mark-synced")
async def mark_as_synced(device_id: str, current_user: dict = Depends(get_current_user)):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # 检查设备是否存在
            await cur.execute(
                "SELECT * FROM user_devices WHERE device_id = %s AND user_id = %s",
                (device_id, current_user['user_id'])
            )
            device = await cur.fetchone()
            if not device:
                raise HTTPException(status_code=404, detail="设备未找到")
            
            # 检查是否存在同步状态记录
            await cur.execute(
                "SELECT id FROM user_sync_status WHERE user_id = %s AND device_id = %s",
                (current_user['user_id'], device_id)
            )
            sync_status = await cur.fetchone()
            
            if sync_status:
                # 更新现有记录
                await cur.execute(
                    "UPDATE user_sync_status SET last_sync_at = NOW() WHERE user_id = %s AND device_id = %s",
                    (current_user['user_id'], device_id)
                )
            else:
                # 创建新记录
                await cur.execute(
                    "INSERT INTO user_sync_status (user_id, device_id, last_sync_at) VALUES (%s, %s, NOW())",
                    (current_user['user_id'], device_id)
                )
            
            await conn.commit()
            
            # 获取更新后的同步时间
            await cur.execute(
                "SELECT last_sync_at FROM user_sync_status WHERE user_id = %s AND device_id = %s",
                (current_user['user_id'], device_id)
            )
            updated_sync = await cur.fetchone()
            
            return {
                "success": True,
                "message": "同步状态已更新",
                "data": {
                    "lastSyncAt": updated_sync['last_sync_at'].strftime("%Y-%m-%d %H:%M:%S") if updated_sync else None
                }
            }

# 获取用户名
@app.get('/api/users/{user_id}')
async def get_username(user_id: int):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT username FROM users WHERE user_id = %s", (user_id,))
            user = await cur.fetchone()
            if user is None:
                raise HTTPException(status_code=404, detail="用户不存在")
            return {"success": True, "data": {"username": user[0]}}

# 健康建议相关路由
@app.get("/api/health-advice")
async def get_health_advice_list(
    page: int = 1,
    page_size: int = 10,
    keyword: str = "",
    sort: str = "date",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    favorites_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """获取健康建议列表"""
    logger.info(f"获取健康建议列表: user_id={current_user['user_id']}, page={page}, page_size={page_size}, keyword={keyword}, sort={sort}, favorites_only={favorites_only}")
    
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # 构建基础查询
                query = """
                    SELECT 
                        id, user_id, content, symptoms, recommended_foods,
                        created_at, updated_at, is_favorite, rating, feedback
                    FROM health_advice 
                    WHERE user_id = %s AND is_deleted = 0
                """
                params = [current_user['user_id']]

                # 如果是获取收藏列表，添加收藏条件
                if favorites_only:
                    query += " AND is_favorite = 1"

                # 添加关键词搜索
                if keyword:
                    query += " AND (content LIKE %s OR symptoms LIKE %s OR recommended_foods LIKE %s)"
                    keyword_param = f"%{keyword}%"
                    params.extend([keyword_param, keyword_param, keyword_param])

                # 添加日期范围
                if start_date:
                    query += " AND created_at >= %s"
                    params.append(start_date)
                if end_date:
                    query += " AND created_at <= %s"
                    params.append(end_date)

                # 添加排序
                if sort == "date":
                    query += " ORDER BY created_at DESC"
                elif sort == "rating":
                    query += " ORDER BY rating DESC"

                # 获取总记录数
                count_query = f"SELECT COUNT(*) as total FROM ({query}) as t"
                await cur.execute(count_query, params)
                total = (await cur.fetchone())['total']

                # 添加分页
                query += " LIMIT %s OFFSET %s"
                params.extend([page_size, (page - 1) * page_size])

                # 执行查询
                await cur.execute(query, params)
                results = await cur.fetchall()

                logger.info(f"获取到的建议数量: {len(results)}")

                return {
                    "success": True,
                    "data": {
                        "items": results,
                        "total": total,
                        "page": page,
                        "page_size": page_size
                    }
                }
    except Exception as e:
        logger.error(f"获取健康建议列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取健康建议列表失败"
        )

@app.put("/api/health-advice/{id}/favorite")
async def toggle_favorite(
    id: int,
    current_user: dict = Depends(get_current_user)
):
    """收藏/取消收藏健康建议"""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 验证建议所有权
                await cur.execute(
                    "SELECT is_favorite FROM health_advice WHERE id = %s AND user_id = %s",
                    (id, current_user['user_id'])
                )
                result = await cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="建议不存在")

                # 切换收藏状态
                new_status = 1 if not result[0] else 0
                await cur.execute(
                    "UPDATE health_advice SET is_favorite = %s WHERE id = %s",
                    (new_status, id)
                )
                await conn.commit()

                return {
                    "success": True,
                    "message": "收藏状态已更新",
                    "data": {
                        "is_favorite": bool(new_status)
                    }
                }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新收藏状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新收藏状态失败")

@app.get("/api/health-advice/{id}")
async def get_health_advice_detail(
    id: int,
    current_user: dict = Depends(get_current_user)
):
    """获取健康建议详情"""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT 
                        id, user_id, content, symptoms, recommended_foods,
                        created_at, updated_at, is_favorite, rating, feedback
                    FROM health_advice 
                    WHERE id = %s AND user_id = %s AND is_deleted = 0
                    """,
                    (id, current_user['user_id'])
                )
                result = await cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="建议不存在")

                return {
                    "success": True,
                    "data": result
                }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取健康建议详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取健康建议详情失败")

@app.delete("/api/health-advice/{id}")
async def delete_health_advice(
    id: int,
    current_user: dict = Depends(get_current_user)
):
    """删除健康建议（软删除）"""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 验证建议所有权
                await cur.execute(
                    "SELECT 1 FROM health_advice WHERE id = %s AND user_id = %s",
                    (id, current_user['user_id'])
                )
                if not await cur.fetchone():
                    raise HTTPException(status_code=404, detail="建议不存在")

                # 软删除
                await cur.execute(
                    "UPDATE health_advice SET is_deleted = 1 WHERE id = %s",
                    (id,)
                )
                await conn.commit()

                return {
                    "success": True,
                    "message": "建议已删除"
                }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除健康建议失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除健康建议失败")

class RatingUpdate(BaseModel):
    rating: float

class FeedbackUpdate(BaseModel):
    feedback: str

@app.put("/api/health-advice/{id}/rating")
async def update_advice_rating(
    id: int,
    rating_data: RatingUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新健康建议的评分"""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 验证建议所有权
                await cur.execute(
                    "SELECT 1 FROM health_advice WHERE id = %s AND user_id = %s",
                    (id, current_user['user_id'])
                )
                if not await cur.fetchone():
                    raise HTTPException(status_code=404, detail="建议不存在或无权访问")

                # 更新评分
                await cur.execute(
                    "UPDATE health_advice SET rating = %s WHERE id = %s",
                    (rating_data.rating, id)
                )
                await conn.commit()

                return {
                    "success": True,
                    "message": "评分已更新"
                }
    except Exception as e:
        logger.error(f"更新评分失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新评分失败")

@app.put("/api/health-advice/{id}/feedback")
async def update_advice_feedback(
    id: int,
    feedback_data: FeedbackUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新健康建议的反馈"""
    logger.info(f"接收到更新反馈请求: id={id}, feedback={feedback_data.feedback}, user_id={current_user['user_id']}")
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 验证建议所有权
                await cur.execute(
                    "SELECT 1 FROM health_advice WHERE id = %s AND user_id = %s",
                    (id, current_user['user_id'])
                )
                result = await cur.fetchone()
                logger.info(f"验证建议所有权结果: {result}")
                
                if not result:
                    logger.warning(f"建议不存在或无权访问: id={id}, user_id={current_user['user_id']}")
                    raise HTTPException(status_code=404, detail="建议不存在或无权访问")

                # 更新反馈
                update_sql = "UPDATE health_advice SET feedback = %s WHERE id = %s"
                logger.info(f"执行SQL: {update_sql} 参数: ({feedback_data.feedback}, {id})")
                await cur.execute(update_sql, (feedback_data.feedback, id))
                await conn.commit()
                logger.info("反馈更新成功")

                return {
                    "success": True,
                    "message": "反馈已更新"
                }
    except Exception as e:
        logger.error(f"更新反馈失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新反馈失败")

# 添加饮食记录
@app.post('/api/dietary-records')
async def create_dietary_record(record: DietaryRecord, current_user: dict = Depends(get_current_user)):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO dietary_records (user_id, meal_type, food_items, calories, protein, carbs, fat, satisfaction, notes, recorded_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (current_user['user_id'], record.meal_type, record.food_items, record.calories, record.protein, record.carbs, record.fat, record.satisfaction, record.notes, record.recorded_at)
            )
            await conn.commit()
            return {'success': True, 'message': '饮食记录已添加'}

# 获取饮食记录
@app.get('/api/dietary-records')
async def get_dietary_records(current_user: dict = Depends(get_current_user), date: str = None):
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            query = "SELECT * FROM dietary_records WHERE user_id = %s"
            params = [current_user['user_id']]
            if date:
                query += " AND DATE(recorded_at) = %s"
                params.append(date)
            await cur.execute(query, params)
            records = await cur.fetchall()
            return {'success': True, 'data': records}

# 更新饮食记录
@app.put('/api/dietary-records/{id}')
async def update_dietary_record(id: int, record: DietaryRecord, current_user: dict = Depends(get_current_user)):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE dietary_records SET meal_type = %s, food_items = %s, calories = %s, protein = %s, carbs = %s, fat = %s, satisfaction = %s, notes = %s, recorded_at = %s
                WHERE id = %s AND user_id = %s
                """,
                (record.meal_type, record.food_items, record.calories, record.protein, record.carbs, record.fat, record.satisfaction, record.notes, record.recorded_at, id, current_user['user_id'])
            )
            await conn.commit()
            return {'success': True, 'message': '饮食记录已更新'}

# 删除饮食记录
@app.delete('/api/dietary-records/{id}')
async def delete_dietary_record(id: int, current_user: dict = Depends(get_current_user)):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM dietary_records WHERE id = %s AND user_id = %s",
                (id, current_user['user_id'])
            )
            await conn.commit()
            return {'success': True, 'message': '饮食记录已删除'}

@app.get('/api/analysis/statistics')
async def get_analysis_statistics(current_user: dict = Depends(get_current_user)):
    """获取健康建议统计信息，包括总数和平均评分。"""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # 查询健康建议总数
                await cur.execute(
                    "SELECT COUNT(*) as total_advices, AVG(rating) as average_rating \
                    FROM health_advice \
                    WHERE user_id = %s AND is_deleted = 0",
                    (current_user['user_id'],)
                )
                result = await cur.fetchone()
                total_advices = result[0]
                average_rating = result[1] or 0.0  # 如果没有评分，默认为0

                return {
                    "success": True,
                    "data": {
                        "totalAdvices": total_advices,
                        "averageRating": average_rating
                    }
                }
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")

@app.get('/api/analysis/rating')
async def get_rating_analysis(current_user: dict = Depends(get_current_user)):
    """获取评分分布分析"""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # 查询 health_advice 表中的 rating 字段
                await cur.execute(
                    "SELECT rating FROM health_advice WHERE user_id = %s AND is_deleted = 0 AND rating IS NOT NULL",
                    (current_user['user_id'],)
                )
                results = await cur.fetchall()
                # 处理评分数据
                rating_distribution = [0] * 5  # 1-5分
                for row in results:
                    rating = int(row['rating'])
                    if rating is not None and 1 <= rating <= 5:
                        rating_distribution[rating - 1] += 1
                return {
                    "success": True,
                    "data": {
                        "ratingDistribution": rating_distribution
                    }
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'获取评分分析失败: {str(e)}')

@app.get('/api/analysis/feedback')
async def get_feedback_analysis(current_user: dict = Depends(get_current_user)):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT feedback FROM health_advice WHERE user_id = %s AND is_deleted = 0 AND feedback IS NOT NULL",
                    (current_user['user_id'],)
                )
                results = await cur.fetchall()
                feedback_list = []
                for row in results:
                    if row[0] is not None and row[0].strip():  # 使用索引访问元组的第一个元素，并确保它不是空字符串
                        feedback_list.append(row[0])
                processed_feedback = process_feedback(feedback_list)
                return {
                    'success': True,
                    'data': processed_feedback
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'获取反馈分析失败: {str(e)}')
    
@app.get('/api/analysis/bmi')
async def get_bmi_analysis(current_user: dict = Depends(get_current_user)):
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # 获取当前日期
                today = datetime.now()
                # 计算30天前的日期
                thirty_days_ago = today - timedelta(days=30)

                # 查询最近30天的BMI记录
                await cur.execute(
                    """
                    SELECT recorded_at, bmi_value 
                    FROM bmi_records 
                    WHERE user_id = %s AND recorded_at >= %s 
                    ORDER BY recorded_at ASC
                    """,
                    (current_user['user_id'], thirty_days_ago)
                )
                records = await cur.fetchall()

                # 创建一个字典来存储日期和对应的BMI值
                bmi_data = {record['recorded_at'].date(): record['bmi_value'] for record in records}

                # 生成最近30天的日期列表
                date_range = [thirty_days_ago + timedelta(days=i) for i in range(31)]
                result = []

                last_value = None  # 用于存储上一个有效的BMI值

                for date in date_range:
                    date_str = date.date()
                    if date_str in bmi_data:
                        # 如果有记录，更新last_value
                        last_value = bmi_data[date_str]
                        result.append({"date": date_str, "bmi_value": last_value})
                    else:
                        # 如果没有记录，使用上一个有效的值
                        if last_value is not None:
                            result.append({"date": date_str, "bmi_value": last_value})
                        else:
                            # 如果没有上一个有效值，尝试查找后一天的值
                            next_value = bmi_data.get((date + timedelta(days=1)).date())
                            if next_value is not None:
                                result.append({"date": date_str, "bmi_value": next_value})
                            else:
                                result.append({"date": date_str, "bmi_value": None})  # 如果前后都没有值，设置为 None

                return {
                    "success": True,
                    "data": result
                }
    except Exception as e:
        logger.error(f"获取BMI数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取BMI数据失败")

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)   
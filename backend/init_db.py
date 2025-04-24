import asyncio
import aiomysql
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

async def init_db():
    """初始化数据库"""
    # 创建数据库连接
    conn = await aiomysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root123"),
        db=os.getenv("DB_NAME", "robot")
    )
    
    async with conn.cursor() as cur:
        # 创建用户表
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID，主键',
                username VARCHAR(255) COMMENT '用户名',
                password_hash VARCHAR(255) COMMENT '密码哈希值',
                email VARCHAR(255) COMMENT '用户邮箱',
                created_at TIMESTAMP COMMENT '创建时间'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户基本信息表';
        """)
        
        # 创建机器人会话表
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS robot_sessions (
                session_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '会话ID，主键',
                user_id INT NOT NULL COMMENT '用户ID，关联users表',
                session_name VARCHAR(255) NOT NULL COMMENT '会话名称',
                created_at TIMESTAMP COMMENT '创建时间',
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='机器人会话表';
        """)
        
        # 创建聊天记录表
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_records (
                record_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID，主键',
                session_id INT NOT NULL COMMENT '会话ID，关联robot_sessions表',
                user_id INT NOT NULL COMMENT '用户ID，关联users表',
                user_message TEXT COMMENT '用户消息内容',
                bot_response TEXT COMMENT '机器人回复内容',
                response_at TIMESTAMP COMMENT '回复时间',
                created_at TIMESTAMP COMMENT '创建时间',
                has_images TINYINT(1) COMMENT '是否包含图片，1-是，0-否',
                device_id VARCHAR(64) COMMENT '设备ID',
                sync_status ENUM('pending', 'synced', 'conflict') COMMENT '同步状态：pending-待同步，synced-已同步，conflict-冲突',
                updated_at TIMESTAMP COMMENT '更新时间',
                FOREIGN KEY (session_id) REFERENCES robot_sessions(session_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                INDEX idx_sync_status (sync_status) COMMENT '同步状态索引',
                INDEX idx_device (device_id) COMMENT '设备ID索引'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天记录表';
        """)
        
        # 创建验证码表
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS verification_codes (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '验证码ID，主键',
                email VARCHAR(255) NOT NULL COMMENT '邮箱地址',
                code VARCHAR(6) NOT NULL COMMENT '验证码',
                created_at TIMESTAMP COMMENT '创建时间',
                expires_at TIMESTAMP COMMENT '过期时间',
                is_used TINYINT(1) COMMENT '是否已使用，1-是，0-否',
                INDEX idx_email (email) COMMENT '邮箱索引',
                INDEX idx_code (code) COMMENT '验证码索引'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='验证码表';
        """)
        
        # 创建用户偏好设置表
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '偏好设置ID，主键',
                user_id INT NOT NULL COMMENT '用户ID，关联users表',
                theme VARCHAR(20) COMMENT '主题设置',
                model VARCHAR(50) DEFAULT 'glm-4-plus' COMMENT '默认模型设置',
                language VARCHAR(20) COMMENT '语言设置',
                message_count INT COMMENT '消息数量',
                total_tokens INT COMMENT '总token数',
                last_active_at TIMESTAMP COMMENT '最后活跃时间',
                created_at TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP COMMENT '更新时间',
                total_sessions INT COMMENT '总会话数',
                total_conversations INT COMMENT '总对话数',
                ai_rules TEXT COMMENT 'AI个性化规则',
                is_rules_enabled TINYINT(1) DEFAULT 0 COMMENT 'AI规则是否启用，1-启用，0-禁用',
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户偏好设置表';
        """)

        # 创建聊天图片表
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_images (
                record_id INT PRIMARY KEY COMMENT '记录ID，关联chat_records表',
                image_1 LONGBLOB COMMENT '图片1内容',
                image_2 LONGBLOB COMMENT '图片2内容',
                image_3 LONGBLOB COMMENT '图片3内容',
                image_4 LONGBLOB COMMENT '图片4内容',
                image_5 LONGBLOB COMMENT '图片5内容',
                FOREIGN KEY (record_id) 
                    REFERENCES chat_records(record_id) 
                    ON DELETE CASCADE
                    ON UPDATE RESTRICT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天图片表';
        """)

        # 创建用户档案表
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '档案ID，主键',
                user_id INT NOT NULL UNIQUE COMMENT '用户ID，关联users表',
                height FLOAT COMMENT '身高(cm)',
                weight FLOAT COMMENT '体重(kg)',
                age INT COMMENT '年龄',
                gender ENUM('male', 'female', 'other') COMMENT '性别：male-男，female-女，other-其他',
                health_conditions JSON DEFAULT ('[]') COMMENT '健康状况，JSON数组',
                allergies JSON DEFAULT ('[]') COMMENT '过敏信息，JSON数组',
                diet_type ENUM('vegetarian', 'vegan', 'normal', 'low_carb', 'keto', 'paleo') DEFAULT 'normal' COMMENT '饮食类型',
                spicy_level ENUM('none', 'mild', 'medium', 'hot', 'extra_hot') DEFAULT 'medium' COMMENT '辣度偏好',
                favorite_ingredients JSON DEFAULT ('[]') COMMENT '喜爱的食材，JSON数组',
                disliked_ingredients JSON DEFAULT ('[]') COMMENT '不喜欢的食材，JSON数组',
                cooking_time_preference INT DEFAULT 30 COMMENT '烹饪时间偏好(分钟)',
                calorie_target INT COMMENT '卡路里目标(kcal)',
                protein_target INT COMMENT '蛋白质目标(g)',
                carb_target INT COMMENT '碳水化合物目标(g)',
                fat_target INT COMMENT '脂肪目标(g)',
                weight_goal FLOAT COMMENT '体重目标(kg)',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                INDEX idx_user_profile (user_id) COMMENT '用户档案索引',
                INDEX idx_diet_type (diet_type) COMMENT '饮食类型索引',
                INDEX idx_updated_at (updated_at) COMMENT '更新时间索引'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户档案表';
        """)

        # 创建饮食记录表
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS dietary_records (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID，主键',
                user_id INT NOT NULL COMMENT '用户ID，关联users表',
                meal_type VARCHAR(20) NOT NULL COMMENT '餐食类型',
                food_items JSON NOT NULL COMMENT '食物项目，JSON数组',
                calories FLOAT COMMENT '卡路里(kcal)',
                protein FLOAT COMMENT '蛋白质(g)',
                carbs FLOAT COMMENT '碳水化合物(g)',
                fat FLOAT COMMENT '脂肪(g)',
                satisfaction INT COMMENT '满意度评分',
                notes TEXT COMMENT '备注',
                recorded_at TIMESTAMP NOT NULL COMMENT '记录时间',
                sync_status ENUM('pending', 'synced', 'conflict') COMMENT '同步状态',
                updated_at TIMESTAMP COMMENT '更新时间',
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                INDEX idx_user_recorded (user_id, recorded_at) COMMENT '用户记录时间索引',
                INDEX idx_meal_type (meal_type) COMMENT '餐食类型索引',
                INDEX idx_satisfaction (satisfaction) COMMENT '满意度索引',
                INDEX idx_recorded_at (recorded_at) COMMENT '记录时间索引',
                INDEX idx_sync_status (sync_status) COMMENT '同步状态索引'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='饮食记录表';
        """)

        # 创建健康建议表
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS health_advice (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '建议ID，主键',
                user_id INT NOT NULL COMMENT '用户ID，关联users表',
                content TEXT NOT NULL COMMENT '建议内容',
                symptoms TEXT COMMENT '症状描述',
                recommended_foods TEXT COMMENT '推荐食物',
                created_at TIMESTAMP NOT NULL COMMENT '创建时间',
                updated_at TIMESTAMP NOT NULL COMMENT '更新时间',
                is_favorite TINYINT(1) COMMENT '是否收藏，1-是，0-否',
                is_deleted TINYINT(1) COMMENT '是否删除，1-是，0-否',
                rating FLOAT COMMENT '评分',
                feedback TEXT COMMENT '反馈内容',
                device_id VARCHAR(64) COMMENT '设备ID',
                sync_status ENUM('pending', 'synced', 'conflict') COMMENT '同步状态',
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                INDEX idx_user_created (user_id, created_at) COMMENT '用户创建时间索引',
                INDEX idx_user_favorite (user_id, is_favorite) COMMENT '用户收藏索引',
                INDEX idx_user_rating (user_id, rating) COMMENT '用户评分索引',
                INDEX idx_created_at (created_at) COMMENT '创建时间索引',
                INDEX idx_updated_at (updated_at) COMMENT '更新时间索引',
                INDEX idx_sync_status (sync_status) COMMENT '同步状态索引',
                INDEX idx_device (device_id) COMMENT '设备索引'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健康建议表';
        """)

        # 创建用户同步状态表
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS user_sync_status (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '同步状态ID，主键',
                user_id INT NOT NULL COMMENT '用户ID，关联users表',
                device_id VARCHAR(64) NOT NULL COMMENT '设备ID',
                last_sync_at TIMESTAMP COMMENT '最后同步时间',
                sync_status ENUM('never_synced', 'completed', 'failed', 'in_progress') DEFAULT 'never_synced' COMMENT '同步状态',
                created_at TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY unique_user_device (user_id, device_id) COMMENT '用户设备唯一索引',
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                INDEX idx_user_last_sync (user_id, last_sync_at) COMMENT '用户最后同步时间索引'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户同步状态表';
        """)

        # 创建设备信息表
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS user_devices (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '设备ID，主键',
                user_id INT NOT NULL COMMENT '用户ID，关联users表',
                device_id VARCHAR(64) NOT NULL COMMENT '设备唯一标识',
                device_name VARCHAR(255) COMMENT '设备名称',
                device_type VARCHAR(50) COMMENT '设备类型',
                last_active_at TIMESTAMP COMMENT '最后活跃时间',
                created_at TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY unique_user_device (user_id, device_id) COMMENT '用户设备唯一索引',
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                INDEX idx_user_last_active (user_id, last_active_at) COMMENT '用户最后活跃时间索引'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备信息表';
        """)

        # 创建用户BMI记录表
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS bmi_records (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID，主键',
                user_id INT NOT NULL COMMENT '用户ID，关联users表',
                bmi_value FLOAT NOT NULL COMMENT 'BMI值',
                recorded_at TIMESTAMP NOT NULL COMMENT '记录时间',
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                INDEX idx_user_recorded (user_id, recorded_at) COMMENT '用户记录时间索引'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户BMI记录表';
        """)

        # 创建食材基础信息表
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS food_base (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '食材ID',
                name VARCHAR(100) NOT NULL COMMENT '食材名称',
                category VARCHAR(50) COMMENT '食材类别',
                properties JSON COMMENT '性质（寒热温凉）',
                season JSON COMMENT '适用季节',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY uk_name (name) COMMENT '食材名称唯一索引'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='食材基础信息表';
        """)

        # 创建食材营养成分表
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS food_nutrients (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '营养成分ID',
                food_id INT NOT NULL COMMENT '食材ID',
                nutrient_name VARCHAR(50) NOT NULL COMMENT '营养素名称',
                amount DECIMAL(10,2) COMMENT '含量',
                unit VARCHAR(20) COMMENT '单位',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                FOREIGN KEY (food_id) REFERENCES food_base(id) ON DELETE CASCADE,
                INDEX idx_food (food_id) COMMENT '食材索引'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='食材营养成分表';
        """)

        # 创建食材关系表
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS food_relations (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '关系ID',
                source_id INT NOT NULL COMMENT '源食材ID',
                target_id INT NOT NULL COMMENT '目标食材ID',
                relation_type ENUM('相生', '相克', '营养互补') NOT NULL COMMENT '关系类型',
                weight DECIMAL(3,2) COMMENT '关系强度',
                evidence TEXT COMMENT '依据',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                FOREIGN KEY (source_id) REFERENCES food_base(id) ON DELETE CASCADE,
                FOREIGN KEY (target_id) REFERENCES food_base(id) ON DELETE CASCADE,
                UNIQUE KEY uk_relation (source_id, target_id, relation_type) COMMENT '关系唯一索引'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='食材关系表';
        """)

        # 创建功效信息表
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS effects (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '功效ID',
                name VARCHAR(100) NOT NULL COMMENT '功效名称',
                description TEXT COMMENT '功效描述',
                related_symptoms JSON COMMENT '相关症状',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY uk_name (name) COMMENT '功效名称唯一索引'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='功效信息表';
        """)

        # 创建食材功效关联表
        await cur.execute("""
            CREATE TABLE IF NOT EXISTS food_effects (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '关联ID',
                food_id INT NOT NULL COMMENT '食材ID',
                effect_id INT NOT NULL COMMENT '功效ID',
                confidence DECIMAL(3,2) DEFAULT 0.8 COMMENT '置信度',
                reference_info TEXT COMMENT '参考依据',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                FOREIGN KEY (food_id) REFERENCES food_base(id) ON DELETE CASCADE,
                FOREIGN KEY (effect_id) REFERENCES effects(id) ON DELETE CASCADE,
                UNIQUE KEY uk_food_effect (food_id, effect_id) COMMENT '食材功效唯一索引'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='食材功效关联表';
        """)
    
        await conn.commit()
    
    await conn.close()
    print("数据库初始化完成")

if __name__ == "__main__":
    asyncio.run(init_db()) 
# 智能健康饮食助手系统

## 项目介绍

本项目是一个基于人工智能的健康饮食助手系统，旨在帮助用户管理饮食记录、提供个性化健康建议，并通过知识图谱和大语言模型实现智能交互。系统具备食物识别、营养分析、健康建议等功能，为用户提供全方位的健康饮食管理服务。

## 系统架构

系统由三大部分组成：

1. **前端** - 基于Vue.js构建的用户界面
2. **后端** - 使用FastAPI开发的REST API服务
3. **AI机器人** - 基于LangChain框架构建的智能对话系统

## 技术栈

### 前端
- Vue.js 3
- Vite
- Vue Router
- 响应式设计

### 后端
- Python 3.12
- FastAPI
- SQLAlchemy
- MySQL数据库
- JWT认证

### AI机器人
- LangChain框架
- 知浦AI大语言模型
- Neo4j知识图谱
- 文本向量嵌入 (text2vec-base-chinese)
- 食物图像识别模型

## 功能特点

- **智能聊天** - 与AI助手进行健康饮食相关对话
- **食物识别** - 上传食物图片进行自动识别和营养分析
- **饮食记录** - 记录和管理日常饮食摄入
- **健康建议** - 获取个性化的健康饮食建议
- **数据分析** - 分析用户饮食模式和营养摄入情况
- **知识图谱** - 利用食物和营养知识图谱提供专业建议
- **多语言支持** - 支持中文和英文界面

## 安装说明

### 环境要求
- Python 3.12
- Node.js 16+
- MySQL 8.0+
- Neo4j 5.0+
- Conda

### 后端安装

1. 创建并激活Conda环境：
```bash
conda create -n robotS python=3.12
conda activate robotS
```

2. 安装后端依赖：
```bash
cd backend
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
# 复制环境变量模板并根据需要修改
cp .env.example .env
```

4. 初始化数据库：
```bash
python init_db.py
```

### 前端安装

1. 安装依赖：
```bash
cd frontend/vue-project
npm install
```

2. 构建前端：
```bash
npm run build
```

### AI机器人部分安装

1. 确保在robotS环境中：
```bash
conda activate robotS
```

2. 安装相关依赖：
```bash
pip install langchain langchain-community langchain-core langgraph
```

3. 配置知识图谱：
```bash
cd robot/knowledge_graph/neo4j
python init_graph.py
```

## 运行项目

启动完整项目：

```bash
python run.py
```

这会同时启动后端API服务器和AI机器人服务器。

## 访问界面

- 前端界面：http://localhost:5173 (开发模式) 或 http://localhost:8000 (生产环境)
- 后端API：http://localhost:8000/docs
- 机器人API：http://localhost:8001/docs

## 使用说明

1. 注册/登录系统
2. 在聊天界面与AI助手交流
3. 上传食物图片进行识别
4. 记录每日饮食
5. 查看个性化健康建议
6. 分析您的饮食数据

## 贡献者

- 开发者: [您的姓名]

## 许可证

本项目为毕业设计作品，版权所有。 
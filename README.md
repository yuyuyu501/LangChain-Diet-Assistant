# Intelligent Healthy Eating Assistant System

## Project Introduction

This project is an AI-based healthy eating assistant system designed to help users manage their dietary records, provide personalized health advice, and enable intelligent interaction through knowledge graphs and large language models. The system features food recognition, nutritional analysis, health recommendations, and more, offering users comprehensive healthy eating management services.

## System Architecture

The system consists of three main parts:

1.  **Frontend** - User interface built with Vue.js
2.  **Backend** - REST API service developed using FastAPI
3.  **AI Robot** - Intelligent conversational system built on the LangChain framework

## Technology Stack

### Frontend
- Vue.js 3
- Vite
- Vue Router
- Responsive Design

### Backend
- Python 3.12
- FastAPI
- SQLAlchemy
- MySQL Database
- JWT Authentication

### AI Robot
- LangChain Framework
- Neo4j Knowledge Graph
- Text Vector Embedding (text2vec-base-chinese)

## Features

- **Intelligent Chat** - Engage in conversations about healthy eating with the AI assistant
- **Food Recognition** - Upload food images for automatic identification and nutritional analysis
- **Dietary Logging** - Record and manage daily food intake
- **Health Recommendations** - Receive personalized healthy eating advice
- **Data Analysis** - Analyze user eating patterns and nutrient intake
- **Knowledge Graph** - Leverage food and nutrition knowledge graphs for professional advice
- **Multilingual Support** - Supports both Chinese and English interfaces

## Installation Instructions

### Environment Requirements
- Python 3.12
- Node.js 16+
- MySQL 8.0+
- Neo4j 5.0+
- Conda

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Initialize Database
```bash
python init_db.py
```

### Initialize Knowledge Graph
```bash
cd robot/knowledge_graph/neo4j
python init_graph.py
```

### Frontend Setup
```bash
cd frontend/vue-project
npm install
```

### Environment Configuration
Fill in the necessary keys in the `.env` file.

### Running the Project

Use the `run.py` script to start both the backend and frontend with one command:

```bash
python run.py
```

This will simultaneously start the backend API server and the AI robot server.

## Accessing the Interface

- Frontend Interface: http://localhost:5173
- Backend API Docs: http://localhost:8000/docs
- Robot API Docs: http://localhost:8001/docs

## Usage Instructions

1. Register/Login to the system
2. Interact with the AI assistant in the chat interface
3. Upload food images for recognition
4. Log your daily meals
5. View personalized health recommendations
6. Analyze your dietary data

## Contributors

- Developer: [yuyuyu_501]

## License

This project is a graduation design work. All rights reserved. 
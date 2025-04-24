import os
import sys
from pathlib import Path
import uvicorn
from dotenv import load_dotenv
import asyncio
import threading
import multiprocessing
import platform

# 获取项目根目录
project_root = Path(__file__).resolve().parent

# 添加项目根目录到Python路径
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# 加载环境变量
load_dotenv(os.path.join(project_root, '.env'))

def run_backend_server():
    """运行backend服务"""
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8000))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    
    # 启动服务器
    uvicorn.run(
        "backend.server:app",
        host=host,
        port=port,
        reload=debug,
        reload_dirs=[str(project_root), str(project_root / "backend")]
    )

def run_robot_server():
    """运行robot服务"""
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("ROBOT_PORT", 8001))  # 使用不同的端口
    debug = os.getenv("DEBUG", "true").lower() == "true"

    # 启动服务器
    uvicorn.run(
        "robot.chat_routes:app",
        host=host,
        port=port,
        reload=debug,
        reload_dirs=[str(project_root), str(project_root / "robot")]
    )

def start_servers():
    """启动所有服务"""
    if platform.system() == 'Windows':
        # Windows下使用spawn方式
        multiprocessing.set_start_method('spawn', force=True)
    
    # 创建两个进程分别运行两个服务
    backend_process = multiprocessing.Process(target=run_backend_server)
    robot_process = multiprocessing.Process(target=run_robot_server)
    
    processes = [backend_process, robot_process]
    
    try:
        print("正在启动服务...")
        # 启动进程
        for process in processes:
            process.start()
        
        # 等待进程结束
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        print("\n正在关闭服务...")
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)  # 等待最多5秒
        sys.exit(0)
    except Exception as e:
        print(f"启动服务时出错: {str(e)}")
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
        sys.exit(1)

if __name__ == "__main__":
    # Windows下需要这个
    if platform.system() == 'Windows':
        multiprocessing.freeze_support()
    start_servers()

"""PlotPilot API 启动入口"""
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 切换到项目目录
os.chdir(project_root)

# 设置环境变量
os.environ['PYTHONPATH'] = project_root

# 启动服务
if __name__ == '__main__':
    import uvicorn
    from interfaces.main import app
    uvicorn.run(app, host='0.0.0.0', port=8005)

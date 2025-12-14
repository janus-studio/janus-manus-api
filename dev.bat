@echo off
REM Windows 开发环境启动脚本
REM 使用 python -m uvicorn 避免 Windows 上的路径规范化问题

python -m uvicorn app.main:app --reload --lifespan on --host 127.0.0.1 --port 8000

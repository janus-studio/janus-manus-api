#!/bin/bash
# 开发环境启动脚本

exec python -m uvicorn app.main:app --reload --lifespan on --host 127.0.0.1 --port 8000

#!/bin/bash
# 生产环境启动脚本
# 使用 python -m uvicorn 避免脚本入口点的路径问题

exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --timeout-graceful-shutdown 0

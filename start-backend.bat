@echo off
chcp 65001 >nul
title 企业知识库 AI Agent 平台 - 后端服务
REM %~dp0 = 本脚本所在目录（项目根），克隆到任何机器都能用
cd /d "%~dp0backend"

REM 离线模式：向量模型直接用本地缓存，避免联网校验卡住
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1

echo [1/2] 检查虚拟环境 ...
call .venv\Scripts\activate.bat

echo [2/2] 启动后端服务 ...
uvicorn app.main:app --host 127.0.0.1 --port 8000

pause

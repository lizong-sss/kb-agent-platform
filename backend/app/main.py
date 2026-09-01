import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api import auth, chat, documents
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时后台线程预热向量模型：第一次上传就不用现场加载（省 3-60 秒）。"""

    def warmup():
        try:
            from app.services.document.embedder import get_model
            get_model()
            print("[预热] 向量模型已加载完成")
        except Exception as e:
            print(f"[预热] 模型加载失败（不影响服务，首次上传会重试）: {e}")

    threading.Thread(target=warmup, daemon=True).start()
    yield


app = FastAPI(
    title="企业知识库 AI Agent 平台",
    description="基于 RAG 与 Function Calling 的企业知识库智能问答系统",
    version="0.2.0",
    lifespan=lifespan,
)

# 跨域：前端页面与后端可能不同端口/协议，放开以便本地演示
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)

_INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "index.html")


@app.get("/", include_in_schema=False)
def index():
    """托管前端单页应用：浏览器访问根路径即进入产品界面。"""
    return FileResponse(os.path.abspath(_INDEX_PATH))


@app.get("/health", tags=["system"])
def health_check():
    """健康检查：部署后用于探活"""
    return {"status": "ok", "app": settings.APP_NAME, "version": app.version}

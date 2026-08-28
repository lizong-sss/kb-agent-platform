from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title="企业知识库 AI Agent 平台",
    description="基于 RAG 与 Function Calling 的企业知识库智能问答系统",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
def health_check():
    """健康检查：部署后用于探活"""
    return {"status": "ok", "app": settings.APP_NAME, "version": app.version}

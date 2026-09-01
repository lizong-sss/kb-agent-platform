"""问答接口：Agent + SSE 流式 + 多轮对话 + 高频缓存。

链路：收问题 → (Redis 缓存命中则直返) → 取会话历史 → Agent(Function Calling 自动选工具)
      → 工具结果回填 → 生成回答 → 存会话 → 返回。

对应简历：对话管理、多轮对话、SSE 流式响应、Redis 缓存高频查询。
"""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.mysql import get_db
from app.models.user import User
from app.services.agent.agent import run_agent, run_agent_stream
from app.services.cache.redis_client import get_cached_answer, set_cached_answer
from app.services.conversation import service as conv_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    conversation_id: int | None = None   # 不传则新建会话


class AskResponse(BaseModel):
    answer: str
    conversation_id: int
    cached: bool = False
    steps: list[dict] = []               # Agent 工具调用过程


@router.post("/ask", response_model=AskResponse)
def ask(
    req: AskRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """非流式问答：走 Agent，返回完整答案 + 工具调用过程。"""
    # 1. Redis 高频缓存：完全一样的问题直接返回，不调大模型
    cached = get_cached_answer(req.question)
    if cached:
        return AskResponse(answer=cached, conversation_id=req.conversation_id or 0, cached=True)

    # 2. 会话：存在则校验归属，不存在则新建
    if req.conversation_id:
        conv = conv_service.get_conversation(db, req.conversation_id, user.id)
        if conv is None:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        conv = conv_service.create_conversation(db, user.id)

    # 3. 拼历史 + 当前问题 → Agent（历史窗口 4 条 = 近 2 轮：
    #    历史越长，模型越倾向模仿历史"直接回答"而跳过工具调用）
    history = conv_service.get_history(db, conv.id, limit=4)
    messages = history + [{"role": "user", "content": req.question}]
    answer, steps = run_agent(messages)

    # 4. 落库（用户消息 + 助手消息）和缓存
    conv_service.add_message(db, conv.id, "user", req.question)
    conv_service.add_message(db, conv.id, "assistant", answer)
    set_cached_answer(req.question, answer)

    return AskResponse(
        answer=answer,
        conversation_id=conv.id,
        steps=[{"name": s.name, "args": s.args, "result": s.result} for s in steps],
    )


@router.post("/ask/stream")
def ask_stream(
    req: AskRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """SSE 流式问答：工具调用过程 + 答案逐字输出。"""
    # 会话处理（同步完成，流式只负责输出）
    if req.conversation_id:
        conv = conv_service.get_conversation(db, req.conversation_id, user.id)
        if conv is None:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        conv = conv_service.create_conversation(db, user.id)

    history = conv_service.get_history(db, conv.id, limit=4)
    messages = history + [{"role": "user", "content": req.question}]
    conv_id = conv.id

    # Redis 高频缓存：命中则直接流式回放缓存答案（毫秒级，不调大模型）
    cached = get_cached_answer(req.question)
    if cached:
        def cached_stream():
            yield "data: " + json.dumps({"type": "start", "conversation_id": conv_id}, ensure_ascii=False) + "\n\n"
            for i in range(0, len(cached), 8):   # 分片回放，保持前端打字机效果
                yield "data: " + json.dumps({"type": "token", "content": cached[i:i + 8]}, ensure_ascii=False) + "\n\n"
            yield "data: " + json.dumps({"type": "done", "conversation_id": conv_id, "sources": [], "cached": True}, ensure_ascii=False) + "\n\n"
        return StreamingResponse(cached_stream(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache"})

    async def event_generator():
        answer_parts: list[str] = []
        yield "data: " + json.dumps({"type": "start", "conversation_id": conv_id}, ensure_ascii=False) + "\n\n"
        for event in run_agent_stream(messages):
            if event["type"] == "tool":
                # Agent 产出的事件字段叫 name，前端约定是 tool_name，这里做适配
                event = {**event, "tool_name": event.get("name", "")}
                yield "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"
            elif event["type"] == "token":
                answer_parts.append(event["content"])
                yield "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"
            elif event["type"] == "done":
                # 从 rag_search 的工具结果里提取来源文件名（格式："来源:文件名 第N块"）
                import re
                sources: set[str] = set()
                for step in event.get("steps", []):
                    if step.get("name") == "rag_search":
                        sources.update(re.findall(r"来源[:：]\s*(\S+?)(?:\s|第|$)", step.get("result", "")))
                # 落库并结束
                full_answer = "".join(answer_parts)
                conv_service.add_message(db, conv_id, "user", req.question)
                conv_service.add_message(db, conv_id, "assistant", full_answer)
                set_cached_answer(req.question, full_answer)
                yield "data: " + json.dumps(
                    {"type": "done", "conversation_id": conv_id, "sources": sorted(sources)},
                    ensure_ascii=False,
                ) + "\n\n"
                return

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ===================== 会话管理 =====================

class ConversationCreate(BaseModel):
    title: str = "新对话"


@router.post("/conversations")
def create_conversation(
    req: ConversationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv = conv_service.create_conversation(db, user.id, req.title)
    return {"id": conv.id, "title": conv.title}


@router.get("/conversations")
def list_conversations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return conv_service.list_conversations(db, user.id)


@router.get("/conversations/{conversation_id}/messages")
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv = conv_service.get_conversation(db, conversation_id, user.id)
    if conv is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    rows = conv_service.get_history(db, conversation_id, limit=100)
    return {"conversation_id": conversation_id, "messages": rows}

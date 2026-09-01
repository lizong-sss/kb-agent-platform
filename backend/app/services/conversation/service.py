"""会话管理服务：多轮对话的持久化读写。

一句话：每次对话都存进 MySQL（conversations 表 + messages 表），
下次提问时把历史消息取出来拼进 Prompt，让 Agent"记得前面说过什么"。
对应简历"对话管理、多轮对话与上下文理解"。
"""
import logging

from sqlalchemy.orm import Session

from app.models.conversation import Conversation, Message

logger = logging.getLogger(__name__)


def create_conversation(db: Session, user_id: int, title: str = "新对话") -> Conversation:
    conv = Conversation(user_id=user_id, title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def add_message(db: Session, conversation_id: int, role: str, content: str) -> None:
    db.add(Message(conversation_id=conversation_id, role=role, content=content))
    db.commit()


def get_history(db: Session, conversation_id: int, limit: int = 10) -> list[dict]:
    """取最近 N 条历史消息（升序），转成 OpenAI 兼容的 messages 格式。"""
    rows = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(limit)
        .all()
    )
    rows.reverse()  # 回到时间正序
    return [{"role": r.role, "content": r.content} for r in rows if r.role in ("user", "assistant")]


def list_conversations(db: Session, user_id: int) -> list[dict]:
    rows = db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.id.desc()).all()
    return [{"id": c.id, "title": c.title, "created_at": c.created_at.strftime("%Y-%m-%d %H:%M")} for c in rows]


def get_conversation(db: Session, conversation_id: int, user_id: int) -> Conversation | None:
    """校验会话归属：只能访问自己的会话。"""
    return (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )

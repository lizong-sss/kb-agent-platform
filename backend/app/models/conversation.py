"""会话模型：多轮对话的持久化存储。

一张会话对应一段连续对话，消息按顺序追加。这样"多轮对话"有了真正的数据来源：
再次提问时可以取回历史消息拼进 Prompt。
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.mysql import Base


class Conversation(Base):
    """一次多轮对话会话。"""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(128), default="新对话")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Message(Base):
    """会话里的一条消息：谁说的、说了什么、什么时候。"""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))          # user / assistant / tool
    content: Mapped[str] = mapped_column(Text)             # 消息正文
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

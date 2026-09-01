"""MySQL 数据库访问层。

职责：创建 SQLAlchemy 引擎、会话工厂，供全项目获取数据库会话。
一句话：这里是"业务数据库的门口"，所有读写 MySQL 的地方都从这里拿会话。
"""
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# 连接串：mysql+pymysql://用户:密码@主机:端口/库名?charset=utf8mb4
DATABASE_URL = (
    f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}?charset=utf8mb4"
)

# pool_pre_ping=True：每次取连接前先探活，避免 MySQL 空闲回收导致连接失效
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类：模型只需继承它，建表时统一收集。"""
    pass


def get_db():
    """FastAPI 依赖：请求进来时开一个会话，请求结束自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

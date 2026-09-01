"""业务数据模型：给 Agent 工具提供真实可查的数据源。

- Employee（员工表）：给 sql_query / hr_lookup 工具用，演示"查张三的部门"。
- Policy（政策表）：给 policy_lookup 工具用，演示"查政策编号 XX 是什么"。
"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.mysql import Base


class Employee(Base):
    """员工信息：姓名、部门、职位、邮箱、入职日期。"""

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    department: Mapped[str] = mapped_column(String(64), nullable=False)
    position: Mapped[str] = mapped_column(String(64), default="")
    email: Mapped[str] = mapped_column(String(128), default="")
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)


class Policy(Base):
    """政策条目：政策编号、标题、所属部门、生效日期。"""

    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    department: Mapped[str] = mapped_column(String(64), default="")
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

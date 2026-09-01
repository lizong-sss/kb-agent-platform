"""数据库初始化脚本：建表 + 灌入演示业务数据 + 创建默认账号。

用法（在 backend 目录下）：
    .venv\\Scripts\\python.exe scripts/init_db.py

干了三件事：
1. 按 models/ 里的定义创建全部数据表（users/conversations/messages/employees/policies）
2. 插入员工表、政策表演示数据（供 Agent 的 sql_query/hr_lookup/policy_lookup 工具查询）
3. 创建默认账号 demo / demo123（供登录演示）
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date

from app.core.security import hash_password
from app.db.mysql import Base, SessionLocal, engine
from app.models import business, conversation, user  # noqa: F401  确保模型被注册
from app.models.business import Employee, Policy
from app.models.user import User

# 演示员工数据（给"查张三的部门"用）
EMPLOYEES = [
    ("张三", "技术部", "后端工程师", "zhangsan@example.com", date(2021, 3, 15)),
    ("李四", "人事部", "HR 专员", "lisi@example.com", date(2020, 7, 1)),
    ("王五", "财务部", "会计", "wangwu@example.com", date(2022, 1, 10)),
    ("赵六", "市场部", "市场专员", "zhaoliu@example.com", date(2021, 11, 22)),
    ("陈七", "行政部", "行政专员", "chenqi@example.com", date(2023, 5, 8)),
]

# 演示政策数据（给"查政策编号"用）
POLICIES = [
    ("POL-2024-001", "差旅报销管理办法", "财务部", date(2024, 1, 1)),
    ("POL-2024-002", "员工考勤管理制度", "人事部", date(2024, 2, 1)),
    ("POL-2025-001", "信息安全管理办法", "技术部", date(2025, 1, 1)),
]


def main():
    print("1/3 创建数据表 ...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("2/3 插入业务数据 ...")
        if db.query(Employee).count() == 0:
            for row in EMPLOYEES:
                db.add(Employee(name=row[0], department=row[1], position=row[2], email=row[3], hire_date=row[4]))
        if db.query(Policy).count() == 0:
            for row in POLICIES:
                db.add(Policy(code=row[0], title=row[1], department=row[2], effective_date=row[3]))

        print("3/3 创建默认账号 demo/demo123 ...")
        if db.query(User).filter(User.username == "demo").count() == 0:
            salt, digest = hash_password("demo123")
            db.add(User(username="demo", salt=salt, password_hash=digest, email="demo@example.com"))

        db.commit()
        print("✅ 初始化完成")
        print("   员工", db.query(Employee).count(), "条，政策", db.query(Policy).count(), "条，账号 demo 已创建")
    finally:
        db.close()


if __name__ == "__main__":
    main()

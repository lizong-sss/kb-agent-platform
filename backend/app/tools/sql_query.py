"""工具：业务数据库 SQL 查询。

对接 MySQL，只允许查询白名单表（employees/policies）和白名单字段，
后端用 ORM 参数化查询执行，避免让大模型直接拼 SQL 带来的注入风险。
简历上"SQL 查询工具、对接业务数据库"指的就是它。
"""
from app.db.mysql import SessionLocal
from app.models.business import Employee, Policy
from app.tools.base import BaseTool

# 每张表允许查询的字段（白名单，防注入）
_ALLOWED = {
    "employees": {"name", "department", "position", "email"},
    "policies": {"code", "title", "department"},
}

# 表 → ORM 模型映射
_MODELS = {"employees": Employee, "policies": Policy}


class SqlQueryTool(BaseTool):
    name = "sql_query"
    description = "查询业务数据库（employees 员工表 / policies 政策表）。按指定字段模糊查询，适合查人员部门、政策条目等结构化数据。"
    args_schema = {
        "type": "object",
        "properties": {
            "table": {"type": "string", "enum": ["employees", "policies"], "description": "要查询的表"},
            "field": {"type": "string", "description": "查询字段，如 name/department/code/title"},
            "value": {"type": "string", "description": "要匹配的值"},
            "limit": {"type": "integer", "description": "最多返回几条，默认5", "default": 5},
        },
        "required": ["table", "field", "value"],
    }

    def run(self, table: str, field: str, value: str, limit: int = 5) -> str:
        if table not in _MODELS:
            return f"不支持的数据库表: {table}（仅支持 employees/policies）"
        if field not in _ALLOWED[table]:
            return f"表 {table} 不支持字段 {field}（允许: {sorted(_ALLOWED[table])}）"

        db = SessionLocal()
        try:
            model = _MODELS[table]
            # like 的参数是绑定参数，value 不会被拼进 SQL，天然防注入
            rows = db.query(model).filter(getattr(model, field).like(f"%{value}%")).limit(limit).all()
            if not rows:
                return f"表 {table} 中没有匹配 {field}={value} 的记录。"
            if table == "employees":
                return "\n".join(
                    f"姓名:{r.name} | 部门:{r.department} | 职位:{r.position} | 邮箱:{r.email} | 入职:{r.hire_date}"
                    for r in rows
                )
            return "\n".join(
                f"编号:{r.code} | 标题:{r.title} | 部门:{r.department} | 生效:{r.effective_date}"
                for r in rows
            )
        finally:
            db.close()

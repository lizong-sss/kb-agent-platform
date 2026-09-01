"""工具：人员信息查询（语义化封装）。

专门查员工表，按姓名查部门/职位/联系方式。演示口径是"人员信息 2 类业务工具"之一。
"""
from app.db.mysql import SessionLocal
from app.models.business import Employee
from app.tools.base import BaseTool


class HrLookupTool(BaseTool):
    name = "hr_lookup"
    description = "查询员工信息，按姓名查询该员工的部门、职位、邮箱等。"
    args_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "员工姓名，如 张三"},
        },
        "required": ["name"],
    }

    def run(self, name: str) -> str:
        db = SessionLocal()
        try:
            rows = db.query(Employee).filter(Employee.name.like(f"%{name}%")).limit(5).all()
            if not rows:
                return f"未找到员工「{name}」。"
            return "\n".join(
                f"姓名:{r.name} | 部门:{r.department} | 职位:{r.position} | 邮箱:{r.email}"
                for r in rows
            )
        finally:
            db.close()

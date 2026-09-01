"""工具：政策查询（语义化封装）。

专门查政策表，按政策编号或标题关键词查询。演示口径是"政策编号 2 类业务工具"之一。
"""
from app.db.mysql import SessionLocal
from app.models.business import Policy
from app.tools.base import BaseTool


class PolicyLookupTool(BaseTool):
    name = "policy_lookup"
    description = "查询企业政策信息，可按政策编号（如 POL-2024-001）或政策标题关键词查询。"
    args_schema = {
        "type": "object",
        "properties": {
            "keyword": {"type": "string", "description": "政策编号或标题关键词，如 POL-2024-001 或 报销"},
        },
        "required": ["keyword"],
    }

    def run(self, keyword: str) -> str:
        db = SessionLocal()
        try:
            rows = (
                db.query(Policy)
                .filter((Policy.code.like(f"%{keyword}%")) | (Policy.title.like(f"%{keyword}%")))
                .limit(5)
                .all()
            )
            if not rows:
                return f"未找到与「{keyword}」相关的政策。"
            return "\n".join(
                f"编号:{r.code} | 标题:{r.title} | 负责部门:{r.department} | 生效日期:{r.effective_date}"
                for r in rows
            )
        finally:
            db.close()

"""工具注册表：把所有工具收集到一起，统一暴露给 Agent。

新增一个工具的步骤只有两步：
1. 在 tools/ 下新建一个继承 BaseTool 的文件；
2. 在下面 ALL_TOOLS 列表里加一行。
这就是简历里写的"方便新增工具快速接入与管理"。
"""
from app.tools.base import BaseTool
from app.tools.get_time import GetTimeTool
from app.tools.hr_lookup import HrLookupTool
from app.tools.policy_lookup import PolicyLookupTool
from app.tools.rag_search import RagSearchTool
from app.tools.send_email import SendEmailTool
from app.tools.sql_query import SqlQueryTool

# 全部工具实例（顺序即暴露给大模型的顺序）
ALL_TOOLS: list[BaseTool] = [
    RagSearchTool(),
    SqlQueryTool(),
    PolicyLookupTool(),
    HrLookupTool(),
    SendEmailTool(),
    GetTimeTool(),
]

# 名字 → 实例 的映射，方便按名执行
TOOL_MAP: dict[str, BaseTool] = {t.name: t for t in ALL_TOOLS}


def get_tools_schemas() -> list[dict]:
    """返回全部工具的 OpenAI Function Calling 描述（给大模型看说明书）。"""
    return [t.to_openai_schema() for t in ALL_TOOLS]


def execute_tool(name: str, args: dict) -> str:
    """按名字执行工具，返回文本结果。找不到工具或执行出错都返回友好信息。"""
    tool = TOOL_MAP.get(name)
    if tool is None:
        return f"未知工具: {name}"
    try:
        return tool.run(**args)
    except Exception as e:  # 工具内部出错不能中断整个对话
        return f"工具 {name} 执行失败: {e}"

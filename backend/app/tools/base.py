"""工具基类：所有 Agent 工具的统一"模板"。

一个工具 = 一份给 LLM 看的说明书（name/description/args_schema）+ 一段真实执行的代码（run）。
Agent 通过 Function Calling 看到说明书后点名调用，代码在这里真正跑起来。
"""
from typing import Any


class BaseTool:
    """所有工具都要继承它并实现 name/description/args_schema/run。"""

    name: str = ""
    description: str = ""
    args_schema: dict = {}

    def run(self, **kwargs: Any) -> str:
        """真正执行工具逻辑，返回一段文本结果（会被回填给大模型）。"""
        raise NotImplementedError

    def to_openai_schema(self) -> dict:
        """转成 OpenAI Function Calling 认识的 JSON Schema 格式。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.args_schema,
            },
        }

"""工具：获取当前时间。

最简单的工具，但很有用——大模型不知道"现在是几点"，需要查工具才知道。
用它演示"Agent 遇到能力边界时主动求助工具"。
"""
from datetime import datetime

from app.tools.base import BaseTool


class GetTimeTool(BaseTool):
    name = "get_time"
    description = "获取当前日期和时间（北京时间）。当用户问'今天几号/几点/周几'时必须调用本工具。"
    args_schema = {"type": "object", "properties": {}}

    def run(self, **kwargs) -> str:
        now = datetime.now()
        return now.strftime("当前时间：%Y-%m-%d %H:%M:%S（%A）")

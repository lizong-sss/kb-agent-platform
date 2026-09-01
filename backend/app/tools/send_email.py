"""工具：发送邮件（演示模式）。

真实发送需要配置 SMTP 服务；这里用"模拟发送"——打印日志并返回成功，
足以演示"Agent 能调用外部动作类工具"的能力。面试时可说明：接入真实 SMTP 只需换掉 run() 里的实现。
"""
import logging

from app.tools.base import BaseTool

logger = logging.getLogger(__name__)


class SendEmailTool(BaseTool):
    name = "send_email"
    description = "发送邮件给指定收件人（演示模式：模拟发送，不真实投递）。适合演示'邮件通知、审批提醒'类场景。"
    args_schema = {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "收件人邮箱"},
            "subject": {"type": "string", "description": "邮件主题"},
            "body": {"type": "string", "description": "邮件正文"},
        },
        "required": ["to", "subject", "body"],
    }

    def run(self, to: str, subject: str, body: str) -> str:
        # 演示模式：真实发送可在此替换为 smtplib 调用
        logger.info("[演示] 发送邮件 -> %s | 主题: %s | 正文: %s", to, subject, body)
        return f"邮件已发送至 {to}（主题：{subject}）。[演示模式，未真实投递]"

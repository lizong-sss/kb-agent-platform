"""Agent 编排核心（LangChain 版）：Function Calling 循环。

这是整个项目最核心的逻辑，对应简历"基于 LangChain 构建 Agent、
通过 Function Calling 实现工具自动选择与执行"。

基于 LangChain 的模型封装：
- ChatOpenAI：LangChain 对 OpenAI 兼容接口的封装（改 base_url 即接 DeepSeek）；
- bind_tools()：把工具说明书绑定给模型，模型按需返回 tool_calls；
- ToolMessage：工具结果的标准化消息类型，回填给模型继续推理。

工作方式（一个循环）：
1. 把"历史消息 + 用户新问题 + 工具说明书"发给大模型；
2. 大模型判断：不需要工具 → 直接输出最终回答，循环结束；
   需要工具 → 返回 tool_calls（工具名 + 参数），后端执行；
3. 执行结果以 ToolMessage 回填，进入下一轮，直到模型给出最终回答。

所有工具调用过程都会记录/流式产出，用于前端展示"Agent 正在做什么"。
"""
import json
import logging

from langchain_core.messages import AIMessage, ToolMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.tools.registry import execute_tool, get_tools_schemas

logger = logging.getLogger(__name__)

# 给 Agent 的系统提示词：说明身份 + 什么时候该用工具
AGENT_SYSTEM_PROMPT = """你是企业知识库 AI 助手，可以调用工具来完成用户请求。

使用工具的规则：
1. 只要用户的问题涉及公司制度、员工手册、政策文件等文档内容（考勤、请假、薪酬、报销、班车、采购等），每一轮都必须重新调用 rag_search 检索知识库——即使对话历史中出现过类似问题的答案，也禁止直接用历史信息回答；
2. 用户查人员、部门、政策编号等结构化数据时，调用 sql_query / policy_lookup / hr_lookup 查询数据库；
3. 用户问时间、日期时，调用 get_time；
4. 用户要求发送邮件通知时，调用 send_email；
5. 工具返回的结果就是真实依据，请基于工具结果回答，不要编造工具没返回的信息。
6. 只要工具返回的资料中已经包含问题答案，就直接完整回答，不要反问用户、不要要求用户补充信息。
7. 如果使用了 rag_search，回答末尾另起一行注明"来源：<资料中的来源文件名>"。

当工具足够回答问题时，直接用中文给出简洁、准确的最终回答。"""

MAX_ITERATIONS = 5  # 最多循环 5 轮工具调用，防止死循环

_llm_with_tools: ChatOpenAI | None = None


def get_llm() -> ChatOpenAI:
    """懒加载单例：绑定工具的 LangChain 聊天模型，进程内只创建一次。"""
    global _llm_with_tools
    if _llm_with_tools is None:
        _llm_with_tools = ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            temperature=0.1,
        ).bind_tools(get_tools_schemas())
    return _llm_with_tools


class AgentStep:
    """记录 Agent 循环里的一次工具调用，用于前端展示和日志。"""

    def __init__(self, name: str, args: dict, result: str):
        self.name = name
        self.args = args
        self.result = result


def _build_messages(messages: list[dict]) -> list:
    """系统提示词 + 对话历史（dict 与 LangChain 消息对象可混用）。"""
    return [{"role": "system", "content": AGENT_SYSTEM_PROMPT}] + messages


def run_agent(messages: list[dict]) -> tuple[str, list[AgentStep]]:
    """非流式 Agent 循环。

    Returns:
        (最终回答文本, AgentStep 列表)
    """
    llm = get_llm()
    steps: list[AgentStep] = []
    full_messages = _build_messages(messages)
    response: AIMessage | None = None

    for _ in range(MAX_ITERATIONS):
        response: AIMessage = llm.invoke(full_messages)
        full_messages.append(response)

        # 模型没要求调工具 → 这就是最终回答
        if not response.tool_calls:
            return (response.content or ""), steps

        # 模型点名工具 → 执行，结果以 ToolMessage 回填
        for call in response.tool_calls:
            fn_name = call["name"]
            fn_args = call["args"]   # LangChain 已解析成 dict
            logger.info("[Agent] 调用工具 %s 参数=%s", fn_name, fn_args)
            result = execute_tool(fn_name, fn_args)
            steps.append(AgentStep(fn_name, fn_args, result))
            full_messages.append(ToolMessage(content=result, tool_call_id=call["id"]))

    return (response.content or "已达到最大工具调用次数，请换个问法。"), steps


def run_agent_stream(messages: list[dict]):
    """SSE 流式版 Agent（流式优先）。

    每一轮直接用 stream() 发起请求（工具已绑定），从同一个流里同时读出：
    - 答案文本片段（chunk.content）→ 逐字产出 token 事件；
    - 工具调用意图（chunk 累积后自动拼装出 tool_calls）→ 执行后产出 tool 事件。
    没有工具调用的那一轮，答案就是最终回答。

    注意：不能先非流式拿到完整答案再发起第二次请求"续写"——
    模型看到自己已经回答过，只会输出"请问还有其他问题"之类的结束语。
    """
    llm = get_llm()
    full_messages = _build_messages(messages)
    steps: list[dict] = []
    response: AIMessage | None = None

    for _ in range(MAX_ITERATIONS):
        content_parts: list[str] = []
        aggregated: AIMessage | None = None

        for chunk in llm.stream(full_messages):
            if chunk.content:
                content_parts.append(chunk.content)
                yield {"type": "token", "content": chunk.content}
            # AIMessageChunk 支持 + 合并：tool_call_chunks 自动拼装成完整 tool_calls
            aggregated = chunk if aggregated is None else aggregated + chunk

        response = aggregated
        content = "".join(content_parts)

        if not aggregated or not aggregated.tool_calls:
            # 没有工具调用：content 即最终答案（已逐字产出）
            yield {"type": "done", "answer": content, "steps": steps}
            return

        # 有工具调用：回填本轮 assistant 消息（含 tool_calls），逐个执行
        full_messages.append(aggregated)
        for call in aggregated.tool_calls:
            fn_name = call["name"]
            fn_args = call["args"] if isinstance(call["args"], dict) else json.loads(call["args"] or "{}")
            logger.info("[Agent] 调用工具 %s 参数=%s", fn_name, fn_args)
            result = execute_tool(fn_name, fn_args)
            step = {"name": fn_name, "args": fn_args, "result": result}
            steps.append(step)
            yield {"type": "tool", **step}
            full_messages.append(ToolMessage(content=result, tool_call_id=call["id"]))

    yield {"type": "done", "answer": "已达到最大工具调用次数，请换个问法。", "steps": steps}

"""生成器：RAG 的"答"半边——把检索到的资料交给 DeepSeek 组织成回答。

调用方式：DeepSeek 提供 OpenAI 兼容接口，用 openai SDK 指定 base_url 即可。
"""
import logging

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是企业知识库助手。请严格遵守以下规则：
1. 只依据【参考资料】回答问题，不要使用资料之外的知识。
2. 如果资料中没有答案，直接回答"知识库中没有找到相关内容"，不要编造。
3. 回答末尾注明引用的资料来源文件名。
4. 用简洁的中文回答。"""

_client: OpenAI | None = None


def get_client() -> OpenAI:
    """懒加载单例：整个进程共用一个 API 客户端。"""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
    return _client


def build_prompt(question: str, chunks: list[dict]) -> str:
    """把召回的文本块拼装成参考资料上下文。"""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[资料{i}] 来源: {chunk['source']}\n{chunk['text']}")
    context = "\n\n".join(parts)
    return f"【参考资料】\n{context}\n\n【问题】{question}"


def generate_answer(question: str, chunks: list[dict]) -> dict:
    """RAG 生成：检索块 + 问题 → 大模型回答。

    Returns:
        {"answer": 回答文本, "sources": 引用的来源列表}
    """
    client = get_client()
    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(question, chunks)},
        ],
        temperature=0.1,   # 事实型问答用低温度：减少发挥，保证忠实资料
    )
    answer = response.choices[0].message.content
    sources = sorted({c["source"] for c in chunks})
    logger.info("生成回答: 问题=%s, 引用%s个来源, 回答长度=%s", question, len(sources), len(answer))
    return {"answer": answer, "sources": sources}

"""文本分块器：把长文本切成适合检索的语义段落。

策略：递归字符分块（langchain-text-splitters）。
chunk_size=500 / overlap=50：中文场景下效果与成本的平衡点。
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", "。", "，", " ", ""],
    length_function=len,
)


def split_text(text: str) -> list[str]:
    """把长文本切成文本块列表。

    Returns:
        块列表，每块长度 <= chunk_size，相邻块重叠 overlap 个字符。
    """
    chunks = _splitter.split_text(text)
    return [c.strip() for c in chunks
            if len(c.strip()) >= 20]

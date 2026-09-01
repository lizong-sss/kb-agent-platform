"""重排序器：在向量召回的基础上做二次精排。

思路：向量检索能召回"语义相近"的块，但偶尔会把真正精确答案排在后面。
这里引入"词面重合度"作为补充信号：问题里的关键片段在文本里出现得越多，越可能是精确答案。
最终分数 = 0.7×向量相似度 + 0.3×词面重合度，再取 TopK。

生产环境可用 bge-reranker 交叉编码器替换这里的轻量实现，效果更强。
对应简历"结合检索结果重排序提升答案相关性"。
"""
from app.services.rag.retriever import search

# 向量分与词面重合分的权重
VECTOR_WEIGHT = 0.7
OVERLAP_WEIGHT = 0.3


def _overlap_score(query: str, text: str) -> float:
    """词面重合度：把问题切成 2-gram 字符片段，统计出现在文本中的比例。"""
    q = query.strip()
    if len(q) < 2:
        return 0.0
    grams = {q[i : i + 2] for i in range(len(q) - 1)}
    if not grams:
        return 0.0
    hit = sum(1 for g in grams if g in text)
    return hit / len(grams)


def search_with_rerank(query: str, recall_top_k: int = 8, final_top_k: int = 3) -> list[dict]:
    """检索 + 重排：先向量召回 recall_top_k 条，重排后取 final_top_k 条。"""
    hits = search(query, top_k=recall_top_k)
    for h in hits:
        overlap = _overlap_score(query, h["text"])
        h["rerank_score"] = round(VECTOR_WEIGHT * h["score"] + OVERLAP_WEIGHT * overlap, 4)
    hits.sort(key=lambda h: h["rerank_score"], reverse=True)
    return hits[:final_top_k]

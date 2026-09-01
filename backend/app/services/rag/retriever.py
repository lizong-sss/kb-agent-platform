"""检索器：RAG 的"查"半边——把用户问题变成最相关的文本块。"""
import logging

from pymilvus import Collection

from app.core.config import settings
from app.db.milvus import COLLECTION_NAME, connect, ensure_collection
from app.services.document.embedder import embed_texts

logger = logging.getLogger(__name__)

TOP_K = 3


def search(query: str, top_k: int = TOP_K) -> list[dict]:
    """语义检索：返回与问题最相关的 top_k 个文本块。

    Returns:
        [{"text": 原文, "source": 文件名, "chunk_index": 序号, "score": 相似度}, ...]
    """
    connect(settings.MILVUS_HOST, settings.MILVUS_PORT)
    collection: Collection = ensure_collection()
    collection.load()

    query_vector = embed_texts([query])[0]
    results = collection.search(
        data=[query_vector],
        anns_field="vector",
        param={"metric_type": "IP", "params": {"nprobe": 16}},
        limit=top_k,
        output_fields=["text", "source", "chunk_index"],
    )

    hits = []
    for hit in results[0]:
        hits.append(
            {
                "text": hit.entity.get("text"),
                "source": hit.entity.get("source"),
                "chunk_index": hit.entity.get("chunk_index"),
                "score": float(hit.score),
            }
        )
    logger.info("检索 '%s' 召回 %s 块, 最高分 %.4f", query, len(hits), hits[0]["score"] if hits else 0)
    return hits

"""入库验证脚本：连接 Milvus，用一句查询验证向量检索链路是否跑通。

用法：
    .venv/Scripts/python.exe scripts/verify_ingestion.py "报销标准是多少"
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pymilvus import Collection

from app.core.config import settings
from app.db.milvus import COLLECTION_NAME, connect, ensure_collection
from app.services.document.embedder import embed_texts


def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "报销标准是多少"
    top_k = 3

    connect(settings.MILVUS_HOST, settings.MILVUS_PORT)
    collection = ensure_collection()
    collection.load()

    query_vector = embed_texts([query])[0]
    results = collection.search(
        data=[query_vector],
        anns_field="vector",
        param={"metric_type": "IP", "params": {"nprobe": 16}},
        limit=top_k,
        output_fields=["text", "source", "chunk_index"],
    )

    print(f"\n查询: {query}")
    print(f"召回 Top{top_k}:")
    for rank, hit in enumerate(results[0], 1):
        entity = hit.entity
        print(f"\n--- 第{rank}名 (相似度 {hit.score:.4f}) ---")
        print(f"来源: {entity.get('source')} 第{entity.get('chunk_index')}块")
        print(f"内容: {entity.get('text')[:120]}...")


if __name__ == "__main__":
    main()

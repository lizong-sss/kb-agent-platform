"""Milvus 连接与 Collection（向量集合）管理。

一个 Collection 类比 MySQL 的一张表：
- id/source/chunk_index 是标量字段（元数据，可过滤）
- vector 是向量字段（512 维，建了 IVF 索引用于相似度检索）
"""
import logging

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from app.services.document.embedder import EMBEDDING_DIM

logger = logging.getLogger(__name__)

COLLECTION_NAME = "kb_chunks"


def connect(host: str, port: int) -> None:
    """建立与 Milvus 服务器的连接（幂等，可重复调用）。"""
    connections.connect(alias="default", host=host, port=str(port))


def ensure_collection() -> Collection:
    """获取 Collection，不存在则按 schema 创建。"""
    if utility.has_collection(COLLECTION_NAME):
        return Collection(COLLECTION_NAME)

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=2048),
        FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="chunk_index", dtype=DataType.INT64),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM),
    ]
    schema = CollectionSchema(fields, description="企业知识库文本块")
    collection = Collection(name=COLLECTION_NAME, schema=schema)

    # 向量检索索引：IVF_FLAT = 先聚类分桶再桶内精确比较，速度/精度均衡
    collection.create_index(
        field_name="vector",
        index_params={
            "index_type": "IVF_FLAT",
            "metric_type": "IP",           # 内积（向量已归一化，等价余弦相似度）
            "params": {"nlist": 128},
        },
    )
    logger.info("Milvus collection 已创建: %s", COLLECTION_NAME)
    return collection


def insert_chunks(chunks: list[str], source: str) -> int:
    """把一批文本块连同向量写入 Milvus，返回写入条数。"""
    from app.services.document.embedder import embed_texts

    if not chunks:
        return 0
    collection = ensure_collection()
    vectors = embed_texts(chunks)
    collection.insert(
        [
            chunks,                    # text
            [source] * len(chunks),    # source：每块都标来源文件
            list(range(len(chunks))),  # chunk_index：块序号
            vectors,                   # vector
        ]
    )
    collection.flush()                 # 立即落盘可检索（生产环境可省，靠自动刷新）
    logger.info("入库 %s 块，来源: %s", len(chunks), source)
    return len(chunks)

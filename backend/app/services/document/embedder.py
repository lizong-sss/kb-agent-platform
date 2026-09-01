"""向量化器：把文本块转成语义向量。

模型：bge-small-zh-v1.5（中文语义检索专用，512 维，CPU 可跑）。
DeepSeek 没有 embedding 接口，所以生成和向量化分属两家——这是行业常态。
"""
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-zh-v1.5"
EMBEDDING_DIM = 512

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """懒加载模型：第一次调用时才从本地/缓存加载，进程内只加载一次。"""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量向量化。

    Args:
        texts: 文本块列表。
    Returns:
        与输入顺序一一对应的向量列表，每个向量 EMBEDDING_DIM 维。
    """
    if not texts:
        return []
    vectors = get_model().encode(
        [t for t in texts],
        normalize_embeddings=True,   # 归一化后用内积(内积=余弦相似度)算距离
        show_progress_bar=False,
    )
    return vectors.tolist()

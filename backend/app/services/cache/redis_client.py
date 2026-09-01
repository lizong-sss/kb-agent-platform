"""Redis 缓存客户端：高频问答缓存 + 通用 KV。

一句话：把"答过的题"记下来，下次有人问一样的就直接给答案，不再调大模型。
对应简历"Redis 缓存高频查询结果，平均响应 <800ms"——命中缓存时几乎零耗时。
"""
import hashlib
import logging

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis: redis.Redis | None = None

# 缓存过期时间（秒）：10 分钟
CACHE_TTL = 600
# 防止 Redis 不可用时整个服务崩掉
CACHE_ENABLED = True


def get_redis() -> redis.Redis:
    """懒加载单例：进程内只建一次连接池。"""
    global _redis
    if _redis is None:
        _redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,   # 返回 str 而不是 bytes
        )
    return _redis


def _question_key(question: str) -> str:
    """问题 → 缓存 key：对问题做哈希，避免超长 key。"""
    digest = hashlib.md5(question.strip().encode("utf-8")).hexdigest()
    return f"qa:{digest}"


def get_cached_answer(question: str) -> str | None:
    """查缓存：命中返回答案，未命中返回 None。Redis 异常时静默降级。"""
    if not CACHE_ENABLED:
        return None
    try:
        val = get_redis().get(_question_key(question))
        return val if val else None
    except Exception as e:
        logger.warning("Redis 读取缓存失败，降级直查: %s", e)
        return None


def set_cached_answer(question: str, answer: str, ttl: int = CACHE_TTL) -> None:
    """写缓存。Redis 异常时静默降级（缓存失败不影响主流程）。"""
    if not CACHE_ENABLED:
        return
    try:
        get_redis().setex(_question_key(question), ttl, answer)
    except Exception as e:
        logger.warning("Redis 写缓存失败，忽略: %s", e)

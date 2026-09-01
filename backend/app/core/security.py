"""安全工具：密码哈希 + JWT 令牌签发/校验。
- 密码不是明文存库，而是"加盐再哈希"（sha256 + 随机盐），数据库被拖也不怕。
- JWT 是一张"带签名的通行证"：登录成功后签发，之后每次请求带着它，后端验签即认身份。
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings


def hash_password(password: str) -> tuple[str, str]:
    """生成 (盐, 哈希值)。每次生成随机盐，同一密码两次哈希结果不同。"""
    salt = secrets.token_hex(8)
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return salt, digest


def verify_password(password: str, salt: str, digest: str) -> bool:
    """校验密码：用存的盐重新算一遍，比对是否一致。"""
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest() == digest


def create_access_token(user_id: int) -> str:
    """签发 JWT：把用户 id 包进 token，附带过期时间。"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> int | None:
    """校验 JWT：验签 + 查过期。合法则返回 user_id，否则返回 None。"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return int(payload["sub"])
    except jwt.PyJWTError:
        return None

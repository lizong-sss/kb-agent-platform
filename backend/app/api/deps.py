"""认证依赖：从请求里解析 token 并确认当前登录用户。

一句话：任何接口只要加一个 current_user: User = Depends(get_current_user)，
就自动要求"必须带有效登录凭证"，否则返回 401。
对应简历"实现用户登录验证"。
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.mysql import get_db
from app.models.user import User

# 告诉 FastAPI：登录接口在 /auth/login，token 通过 Authorization: Bearer <token> 携带
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """解析 token → 找到用户 → 返回。任何一步失败都返回 401。"""
    user_id = decode_token(token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录凭证无效或已过期")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user

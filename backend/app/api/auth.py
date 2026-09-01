"""认证接口：注册、登录、当前用户信息。

- /auth/register  注册新账号
- /auth/login     登录（表单格式），返回 JWT access_token
- /auth/me        查询当前登录用户信息（需要带 token）
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.mysql import get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=6, max_length=64)
    email: str = ""


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """注册：用户名唯一，密码加盐哈希后入库。"""
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="用户名已被占用")
    salt, digest = hash_password(req.password)
    user = User(username=req.username, salt=salt, password_hash=digest, email=req.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    return {"id": user.id, "username": user.username, "access_token": token, "token_type": "bearer"}


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """登录：校验用户名密码，成功返回 JWT。"""
    user = db.query(User).filter(User.username == form.username).first()
    if user is None or not verify_password(form.password, user.salt, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(user.id)
    return {"id": user.id, "username": user.username, "access_token": token, "token_type": "bearer"}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    """查询当前用户（测试 token 是否有效用）。"""
    return {"id": current_user.id, "username": current_user.username, "email": current_user.email}

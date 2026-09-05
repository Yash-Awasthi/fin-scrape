"""
认证路由 - 登录/注册/令牌刷新/用户管理
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.db.database import get_db
from backend.models.user import User
from backend.core.auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    require_auth, require_admin, Role,
)
from backend.core.rate_limiter import limiter

logger = logging.getLogger("auth")
router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=6, max_length=128)
    email: Optional[str] = None
    role: str = Field(default=Role.VIEWER, pattern=r"^(viewer|analyst|admin)$")


class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class PasswordChangeRequest(BaseModel):
    old_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=6, max_length=128)


class RoleUpdateRequest(BaseModel):
    role: str = Field(..., pattern=r"^(viewer|analyst|admin)$")


def _user_to_dict(user: User) -> dict:
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    """用户登录，返回 access_token 和 refresh_token"""
    user = db.query(User).filter_by(username=body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已禁用",
        )

    access_token = create_access_token(data={"sub": user.user_id, "role": user.role})
    refresh_token = create_refresh_token(data={"sub": user.user_id})

    user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": _user_to_dict(user),
    }


@router.post("/register")
@limiter.limit("3/minute")
async def register(request: Request, body: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册（首次注册用户自动成为 admin，后续注册默认 viewer）"""
    existing = db.query(User).filter_by(username=body.username).first()
    if existing:
        raise HTTPException(400, "用户名已存在")

    if body.email:
        existing_email = db.query(User).filter_by(email=body.email).first()
        if existing_email:
            raise HTTPException(400, "邮箱已被注册")

    user_count = db.query(User).count()
    assigned_role = Role.ADMIN if user_count == 0 else body.role

    user = User(
        user_id=str(uuid.uuid4()),
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=assigned_role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": user.user_id, "role": user.role})
    refresh_token = create_refresh_token(data={"sub": user.user_id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": _user_to_dict(user),
    }


@router.post("/refresh")
async def refresh_token(body: TokenRefreshRequest, db: Session = Depends(get_db)):
    """刷新访问令牌"""
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(401, "无效的刷新令牌")

    user_id = payload.get("sub")
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or not user.is_active:
        raise HTTPException(401, "用户不存在或已禁用")

    access_token = create_access_token(data={"sub": user.user_id, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
async def get_me(user: dict = Depends(require_auth)):
    """获取当前用户信息"""
    return user


@router.post("/change-password")
async def change_password(
    body: PasswordChangeRequest,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """修改密码"""
    user = db.query(User).filter_by(user_id=current_user["user_id"]).first()
    if not user:
        raise HTTPException(404, "用户不存在")

    if not verify_password(body.old_password, user.hashed_password):
        raise HTTPException(400, "旧密码错误")

    user.hashed_password = hash_password(body.new_password)
    user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return {"status": "ok", "message": "密码已更新"}


@router.get("/users")
async def list_users(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """列出所有用户（仅管理员）"""
    users = db.query(User).all()
    return {"total": len(users), "items": [_user_to_dict(u) for u in users]}


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    body: RoleUpdateRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """修改用户角色（仅管理员）"""
    target = db.query(User).filter_by(user_id=user_id).first()
    if not target:
        raise HTTPException(404, "用户不存在")

    if target.user_id == current_user["user_id"]:
        raise HTTPException(400, "不能修改自己的角色")

    target.role = body.role
    target.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return {"status": "ok", "user": _user_to_dict(target)}


@router.patch("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: str,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """启用/禁用用户（仅管理员）"""
    target = db.query(User).filter_by(user_id=user_id).first()
    if not target:
        raise HTTPException(404, "用户不存在")

    if target.user_id == current_user["user_id"]:
        raise HTTPException(400, "不能禁用自己")

    target.is_active = not target.is_active
    target.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return {"status": "ok", "is_active": target.is_active, "user": _user_to_dict(target)}

"""
用户模型 - 支持认证与角色权限
"""
from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime, timezone
from backend.db.database import Base


def _utc_now_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="viewer")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utc_now_naive)
    updated_at = Column(DateTime, default=_utc_now_naive, onupdate=_utc_now_naive)

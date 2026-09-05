"""
全局速率限制器实例，避免循环导入
"""
import os
from slowapi import Limiter
from slowapi.util import get_remote_address

_limiter_instance = None


def get_limiter() -> Limiter:
    global _limiter_instance
    if _limiter_instance is None:
        _limiter_instance = Limiter(
            key_func=get_remote_address,
            default_limits=["120/minute"],
            enabled=True,
            storage_uri="memory://",
            config_filename=os.devnull,
        )
    return _limiter_instance


limiter = get_limiter()

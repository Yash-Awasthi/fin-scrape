"""
统一日志配置，main.py顶部调一次setup_logging()就行
DEBUG=True详细格式带文件名行号，False简洁格式，敏感信息自动脱敏
"""
import logging
import logging.config
import re
from typing import Optional


# 常见API Key模式
_SENSITIVE_PATTERNS = [
    re.compile(r"(sk-[A-Za-z0-9\-]{10,})", re.I),
    re.compile(r"(Bearer\s+[A-Za-z0-9\-._~+/]+=*)", re.I),
    re.compile(r"(api[_-]?key[\"'\s:=]+)[^\s\"',]{8,}", re.I),
]


class SensitiveFilter(logging.Filter):
    """过滤日志里的敏感信息"""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        msg = record.getMessage()
        for pattern in _SENSITIVE_PATTERNS:
            if pattern.search(msg):
                # 脱敏但保留日志条目
                record.msg = pattern.sub(r"[REDACTED]", str(record.msg))
                record.args = ()
        return True


def setup_logging(debug: Optional[bool] = None) -> None:
    """初始化日志配置，debug=None时从settings读"""
    if debug is None:
        try:
            from backend.core.config import settings
            debug = settings.DEBUG
        except Exception:
            debug = False

    level = "DEBUG" if debug else "INFO"

    fmt_detail = "%(asctime)s [%(levelname)-8s] %(name)-30s %(message)s  (%(filename)s:%(lineno)d)"
    fmt_simple = "%(asctime)s [%(levelname)-8s] %(name)s - %(message)s"
    fmt = fmt_detail if debug else fmt_simple

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "sensitive": {
                "()": SensitiveFilter,
            }
        },
        "formatters": {
            "main": {
                "format": fmt,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "main",
                "filters": ["sensitive"],
                "stream": "ext://sys.stderr",
            }
        },
        "loggers": {
            # 应用
            "": {"handlers": ["console"], "level": level, "propagate": False},
            # uvicorn
            "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "DEBUG" if debug else "WARNING",  # 生产不刷access log
                "propagate": False,
            },
            # SQL不刷屏
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": "DEBUG" if debug else "WARNING",
                "propagate": False,
            },
            # httpx减噪
            "httpx": {"handlers": ["console"], "level": "WARNING", "propagate": False},
            "httpcore": {"handlers": ["console"], "level": "WARNING", "propagate": False},
            # 子模块
            "llm_router":     {"handlers": ["console"], "level": level, "propagate": False},
            "task_manager":   {"handlers": ["console"], "level": level, "propagate": False},
            "pipeline":       {"handlers": ["console"], "level": level, "propagate": False},
            "clustering":     {"handlers": ["console"], "level": level, "propagate": False},
            "abstraction":    {"handlers": ["console"], "level": level, "propagate": False},
            "theory":         {"handlers": ["console"], "level": level, "propagate": False},
            "scenario":       {"handlers": ["console"], "level": level, "propagate": False},
            "anti_template":  {"handlers": ["console"], "level": level, "propagate": False},
            "analogy":        {"handlers": ["console"], "level": level, "propagate": False},
            "inference_layer":{"handlers": ["console"], "level": level, "propagate": False},
        },
    }

    logging.config.dictConfig(config)
    logging.getLogger("logging_config").info(
        "日志系统初始化完成 (level=%s, debug=%s)", level, debug
    )

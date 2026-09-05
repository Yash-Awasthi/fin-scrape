"""
配置管理，pydantic_settings 自动读 .env，默认值写字段定义里
启动时会检查密钥缺失、占位符、生产环境安全项
"""
import logging
from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from typing import Any, List

logger = logging.getLogger("config")


class Settings(BaseSettings):
    # API 配置
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com"
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # 数据库
    DATABASE_URL: str = "sqlite:///./geopolitical_intel.db"

    # 新闻采集
    NEWS_FETCH_INTERVAL_MINUTES: int = 30
    MAX_NEWS_PER_FETCH: int = 100

    # 推演参数
    MIN_NEWS_FOR_CLUSTER: int = 3
    MAX_SCENARIOS_PER_DIRECTION: int = 3
    MIN_STEPS_PER_SCENARIO: int = 5

    # 应用
    APP_NAME: str = "国关推演平台"
    APP_VERSION: str = "1.0.1"  # 安全加固版本
    DEBUG: bool = False
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # SSL验证
    SSL_VERIFY: bool = True  # 默认开SSL验证

    # JWT认证
    JWT_SECRET_KEY: str = "ir-platform-dev-secret-change-in-production"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    @field_validator("DEBUG", mode="before")
    @classmethod
    def _parse_debug(cls, value: Any) -> bool:
        """兼容各种DEBUG值，别因为奇怪的值启动不了"""
        if isinstance(value, bool):
            return value
        if value is None:
            return False

        text = str(value).strip().lower()
        if text == "":
            return False

        truthy = {"1", "true", "yes", "y", "on", "debug", "dev", "development"}
        falsy = {"0", "false", "no", "n", "off", "prod", "production", "release"}
        if text in truthy:
            return True
        if text in falsy:
            return False

        # 不认识的值（比如 "uvicorn:*"）当 False，保证能启动
        return False

    @model_validator(mode="after")
    def _validate_security_settings(self) -> "Settings":
        """启动时安全检查"""
        # API密钥检查
        if not self.ANTHROPIC_API_KEY or self.ANTHROPIC_API_KEY in [
            "",
            "your_anthropic_api_key_here",
            "your-api-key-here",
            "sk-xxx",
        ]:
            logger.warning(
                "⚠️  [安全] ANTHROPIC_API_KEY 未设置或使用占位符值。"
                "LLM 相关功能（推演/分析）将不可用。"
                "请在 .env 文件中配置有效的 API 密钥。"
            )
        else:
            masked_key = self._mask_api_key(self.ANTHROPIC_API_KEY)
            logger.info(f"✓ [安全] API 密钥已配置: {masked_key}")

        # 生产环境安全警告
        if not self.DEBUG:
            if self.SSL_VERIFY is False:
                logger.error(
                    "🔴 [安全] 生产环境(DEBUG=false)禁用了 SSL 验证(SSL_VERIFY=false)，"
                    "存在中间人攻击(MITM)风险！建议立即启用 SSL_VERIFY=true"
                )
            if "*" in self.CORS_ORIGINS:
                logger.warning(
                    "⚠️  [安全] 生产环境 CORS 配置包含通配符(*)，"
                    "允许任意来源访问API，存在安全风险！"
                )

        return self

    @staticmethod
    def _mask_api_key(key: str, visible_chars: int = 8) -> str:
        """脱敏显示，前8后4"""
        if len(key) <= 12:
            return "***"
        return f"{key[:visible_chars]}...{key[-4:]}"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()

# 启动时打一下状态
logger.info(f"[启动] {settings.APP_NAME} v{settings.APP_VERSION}")
logger.info(f"[启动] DEBUG={settings.DEBUG} | SSL_VERIFY={settings.SSL_VERIFY}")

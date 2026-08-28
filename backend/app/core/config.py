from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """全局配置：从 backend/.env 读取，密钥等敏感信息不写死在代码里"""

    # 应用
    APP_NAME: str = "kb-agent-platform"
    DEBUG: bool = True

    # DeepSeek LLM
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    LLM_MODEL: str = "deepseek-chat"

    # MySQL
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "root123"
    MYSQL_DB: str = "kb_agent"

    # Redis
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Milvus
    MILVUS_HOST: str = "127.0.0.1"
    MILVUS_PORT: int = 19530

    # JWT
    JWT_SECRET_KEY: str = "dev-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

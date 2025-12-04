from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DEVELOP: bool = True
    TITLE: str = 'API'
    VERSION: str = 'v1.0'
    DOC_URL: str = '/docs'
    OPENAPI_URL: str = '/openapi.json'
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000
    WORKERS: int = 1
    LOG_LEVEL: str = 'debug'
    LOG_FORMAT: str = (
        '{"time": "%(asctime)s", "level": "%(levelname)s", "file": "%(name)s", "line": "%(lineno)s", "msg": "%(msg)s"}'
    )

    POSTGRES_USER: str = "postgres_user"
    POSTGRES_PASSWORD: str = "postgres_password"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres_db"
    POSTGRES_POOL_SIZE: int = 20
    POSTGRES_MAX_OVERFLOW: int = 5

    RABBITMQ_DEFAULT_USER: str = "admin"
    RABBITMQ_DEFAULT_PASS: str = "admin"
    RABBITMQ_DEFAULT_VHOST: str = "/"


settings = Settings(
    _env_file="../.env",
    _env_file_encoding="utf-8",
)

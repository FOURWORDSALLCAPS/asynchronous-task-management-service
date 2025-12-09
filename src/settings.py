from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DEVELOP: bool = True
    TITLE: str = "API"
    VERSION: str = "v1.0"
    DOC_URL: str = "/docs"
    OPENAPI_URL: str = "/openapi.json"
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000
    PAGINATION_PAGE: int = 1
    PAGINATION_PAGE_SIZE: int = 25
    WORKERS: int = 1
    LOG_LEVEL: str = "debug"
    LOG_FORMAT: str = '{"time": "%(asctime)s", "level": "%(levelname)s", "file": "%(name)s", "line": "%(lineno)s", "msg": "%(msg)s"}'

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
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: str = "5672"

    @property
    def get_postgres_uri_asyncpg(self):
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def get_test_postgres_uri_asyncpg(self):
        return "postgresql+asyncpg://test_user:test_password@localhost:5446/test_db"

    @property
    def get_postgres_alembic_uri_asyncpg(self):
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@localhost:5445/{self.POSTGRES_DB}"

    @property
    def get_rabbitmq_uri(self):
        return f"amqp://{self.RABBITMQ_DEFAULT_USER}:{self.RABBITMQ_DEFAULT_PASS}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"


settings = Settings(
    _env_file="../.env",
    _env_file_encoding="utf-8",
)

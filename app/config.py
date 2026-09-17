from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket: str = "documents"
    minio_secure: bool = False

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0

    # ONLYOFFICE
    onlyoffice_url: str = "http://onlyoffice"

    # API URLs
    # Browser-facing URL
    public_api_url: str = "http://localhost:8000"

    # Docker internal URL
    # Used by ONLYOFFICE -> FastAPI communication
    internal_api_url: str = "http://api:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
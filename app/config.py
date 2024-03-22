from pathlib import Path

from pydantic import MySQLDsn, PostgresDsn, DirectoryPath, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    server_port: int = 8013
    project_dir: DirectoryPath = Path(__file__).parent.parent
    api_prefix: str = '/api'
    user_token: str
    bot_token: str
    guild_id: str
    channel_id: str
    application_id: str
    bot_application_id: str
    user_id: str
    session_id: str
    interaction_url: str = 'https://discord.com/api/v9/interactions'
    redis_host: str
    redis_port: int
    redis_db: int
    proxy_url: str
    httpx_timeout: int = 60 * 5
    log_level: str = 'DEBUG'
    azure_api_url: str
    azure_api_key: str
    default_instructions: str
    kimi_api_url: str
    kimi_api_key: str
    concurrency_limit: int = 3
    prefetch_count: int = 1
    midjourney_rate_limit: int | float = 1 / 4
    redis_texture_generation_result: str = 'molook:texture'
    redis_expire_time: int = 60 * 60 * 24 * 15  # 15天
    redis_dsn: RedisDsn = 'redis://@localhost:6379/0'

    mysql_dsn: str | MySQLDsn = 'mysql+mysqlconnector://<user>:<password>@<host>[:<port>]/<dbname>'
    pg_dsn: str | PostgresDsn = 'postgresql+psycopg://user:pass@host:5432/db'

    # RABBITMQ
    rabbitmq_url: str
    texture_generation_queue: str  # 纹理生成队列
    texture_generation_result_queue: str  # 纹理生成结果队列
    rabbitmq_exchange: str

    # Aliyun OSS
    oss_access_key_id: str
    oss_access_key_secret: str
    oss_bucket_name: str
    oss_endpoint: str
    oss_storage_path: str
    oss_domain: str | None = None

    # 用于测试, 避免多次调用midjourney api
    test: bool = False

    model_config = SettingsConfigDict(
        env_file=('.env', '.env.local', '.env.staging', '.env.prod', '.env.prod.local')
    )


settings = Settings()

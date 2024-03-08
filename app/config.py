from pathlib import Path

from pydantic import MySQLDsn, PostgresDsn, DirectoryPath
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    server_port: int = 8013
    project_dir: DirectoryPath = Path(__file__).parent.parent
    api_prefix: str = '/api'
    user_token: str
    bot_token: str
    guild_id: str
    channel_id: str
    interaction_url: str = 'https://discord.com/api/v9/interactions'
    redis_host: str
    redis_port: int
    redis_db: int
    proxy_url: str
    httpx_timeout: int = 60 * 5
    log_level: str = 'DEBUG'

    mysql_dsn: str | MySQLDsn = 'mysql+mysqlconnector://<user>:<password>@<host>[:<port>]/<dbname>'
    pg_dsn: str | PostgresDsn = 'postgresql+psycopg://user:pass@host:5432/db'

    model_config = SettingsConfigDict(
        env_file=('.env', '.env.local', '.env.prod', '.env.prod.local')
    )


settings = Settings()

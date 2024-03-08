import redis.asyncio as redis

from app.config import settings
from app.db import SessionLocal


async def get_redis_connection():
    r = await redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        encoding='utf-8'
    )
    return r


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

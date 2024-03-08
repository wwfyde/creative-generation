from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app import settings

engine = create_engine(
    settings.mysql_dsn,
    pool_pre_ping=True,
    connect_args={},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    ...

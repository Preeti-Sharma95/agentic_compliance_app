from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from src.core.config import get_settings

s = get_settings()

connect_args = {"check_same_thread" : False} if S.is_sqlite else {}

engine = create_engine(
    S.db_url,
    connect_args=connect_args,
    futire=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=Flase,
    furure=True,
)

class Base(DeclarativeBase):
    pass
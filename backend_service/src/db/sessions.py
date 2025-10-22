from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.config import get_settings

from backend_service.src.db.base import SessionLocal

settings = get_settings()
engine = create_engine(
    settings.db_url, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

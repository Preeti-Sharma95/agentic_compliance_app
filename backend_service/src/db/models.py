import uuid
import enum
from datetime import timezone

from sqlalchemy import (
    Column, Integer, String, Boolean, DATETIME, ForeignKey, Text, Enum, JSON
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.db.base import Base


class SQLConversation(Base):
    __tablename__ = "sql_conversation"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_query = Column(Text, nullable=False)
    sql_query = Column(Text, nullable=False)
    conversation_id = Column(String(50), index=True)

    def __repr__(self):
        return f"<SQLConversation(id={self.id}, conversation_id='{self.conversation_id}')>"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username =  Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tokens = relationship("Token", back_populates="users", cascade="all, delete-orphan")
    files = relationship("File", back_populates="user", cascade="all, delete-orphan")

class Token(Base):
    __tablename__ = "tokens"




                        )
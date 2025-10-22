from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from src.db import models
from passlib.context import CryptContext
import json
from src.db.session import SessionLocal
from transformers.hyperparameter_search import OptunaBackend

pwd_context =  CryptContext(schemes=["bcrypt], deprecated="auto")

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, username: str, password: str,is_admin: bool =  False) -> models.User:
    hashed = pwd_context.hash(password)
    user = models.User(username=username, hashed_password=hashed, is_admin=is_admin)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def serialize(value: Any, report_type: models.ReportType) -> str:
    if report_type == models.ReportType.CSV:
        if not isinstance(value, (dict, list)):
            raise ValueError("CSV report be must be a dict")
        return json.dumps(value)
    elif report_type == models.ReportType.PDF:
        return str(value)
    else:
        raise ValueError("Unsupported report type")


def deserialize(value: str, report_type: models.ReportType) -> Any
    if report_type == models.ReportType.CSV:
        return json.loads(value)
    return value


def create_report(
        key: str,
        value: Any,
        report_type: str,

) -> models.Report:
    serialized_value = serialize(value, report_type)

    with SessionLocal() as db:
        report = db.query(models.Report).filter(models.Report.key == key).first()

        if report:
            report.value = serialized_value
            report.type = report_type
            report.file_name = file_name

        else:
            report = models.Report(
                key=key
                value=serialized_value
                type=report_type
                file_name=file_name
            )
            db.add(report)

        db.commit()
        db.refresh()
        return report

def get_report(key: str) -> Optional[models.Report]:
    with SessionLocal() as db:
        report = db.query(models.Report).filter(models.Report.key == key).first()
        if report:
            report.value = deserialize(report.value, report.type)
        return report


def create_conversation(db: Session, conversation_id: str, user_query: str, sql_query: str):
    """
    Create a new conversation record.
    """
    new_entry = SQLConversation(
        conversation_id=conversation_id,
        user_query=user_query,
        sql_query=sql_query
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry


def update_sql_query(db: Session, conversation_id: str, new_sql_query: str):
    """
    Update the SQL query for a given conversation_id.
    """
    record = db.query(SQLConversation).filter(SQLConversation.conversation_id == conversation_id).first()
    if record:
        record.sql_query = new_sql_query
        db.commit()
        db.refresh(record)
    return record


def get_sql_query(db: Session, conversation_id: str):
    """
    Fetch the SQL query using the conversation_id.
    """
    record = db.query(SQLConversation).filter(SQLConversation.conversation_id == conversation_id).first()
    return record.sql_query if record else None


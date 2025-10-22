"""
Manages the storage and registration of uploaded datasets.
"""
from pathlib import Path
import uuid
import pandas as pd
import logging
from app.core.config import settings
logger = logging.getLogger(__name__)
UPLOAD_DIR= settings.UPLOAD_DIR
def register_dataframe(df: pd.DataFrame) -> str:
    """Saves a pandas DataFrame to a new CSV file and returns its unique ID."""
    file_id = uuid.uuid4().hex
    output_path = UPLOAD_DIR / f"{file_id}.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"DataFrame saved to '{output_path}' with file_id '{file_id}'")
    return file_id

def register_csv_from_disk(csv_path: Path) -> str:
    """Moves a CSV from a temp path to a new permanent file and returns its ID."""
    file_id = uuid.uuid4().hex
    output_path = UPLOAD_DIR / f"{file_id}.csv"
    csv_path.rename(output_path)
    logger.info(f"CSV moved to '{output_path}' with file_id '{file_id}'")
    return file_id


"""
Centralized FastAPI dependencies for the application.
"""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.auth.azure_ad import validate_token, security
from app.db import crud, session as db_session
from app.api.schemas import UserOut


async def get_current_user(
        credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
        db: Session = Depends(db_session.get_db)
) -> UserOut:
    """
    FastAPI dependency that validates the Azure AD token from the Authorization header
    and returns the corresponding user from our local database.

    It also performs Just-In-Time (JIT) provisioning by creating a new user record
    if the authenticated user does not already exist in the local database.
    """
    token = credentials.credentials
    claims = validate_token(token)

    username = claims.get("upn") or claims.get("preferred_username")
    if not username:
        raise HTTPException(status_code=401, detail="Token does not contain a valid username claim.")

    user = crud.get_user_by_username(db, username=username)
    if user is None:
        # JIT Provisioning: Create a user on their first login
        user_data = {
            "username": username,
            "email": claims.get("email", username),
            "is_admin": False  # New users are not admins by default
        }
        user = crud.create_user(db, user_data=user_data)

    return user
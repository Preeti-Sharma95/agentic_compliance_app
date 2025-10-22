"""API router for handling CSV and Excel file uploads."""

import uuid
import shutil
from pathlib import Path
from typing import Dict, Any
import logging

import pandas as pd
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError # NEW: Import for specific DB exceptions

from app.api.dependencies import get_current_user, register_dataframe, register_csv_from_disk
from app.db.session import get_db
from app.api.schemas import UserOut
from app.db.models import File as UploadedDBFile
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Upload a CSV/Excel file")
async def upload_file(
        file: UploadFile = File(...),
        current_user: UserOut = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Accepts .csv, .xls, or .xlsx files, normalizes them to CSV format,
    stores metadata in the database, and returns a unique file_id.

    This endpoint reads the file into memory, converts it if necessary, saves
    it to a persistent storage location, and records its metadata in the
    database. The returned file_id can be used in other endpoints to
    reference this file.

    Args:
        file (UploadFile): The CSV or Excel file being uploaded by the user.
        current_user (UserOut): The authenticated user, injected by dependency.
        db (Session): The database session, injected by dependency.

    Raises:
        HTTPException(400): If the uploaded file is not a .csv, .xls, or .xlsx file.
        HTTPException(422): If the file is malformed and cannot be parsed by pandas.
        HTTPException(500): For any unexpected server-side errors, such as database
                           connection issues or file system errors.

    Returns:
        Dict[str, Any]: A dictionary containing the generated 'file_id' and the
                        original 'filename' of the uploaded file.
    """
    filename = file.filename or ""
    filename_lower = filename.lower()

    # --- 1. Validate file extension ---
    if not any(filename_lower.endswith(ext) for ext in [".csv", ".xls", ".xlsx"]):
        # UPDATED: Structured logging
        logger.warning(
            "User attempted to upload an unsupported file type",
            extra={"user": current_user.username, "filename": filename}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV and Excel (.xls, .xlsx) files are supported."
        )

    ext = Path(filename_lower).suffix
    tmp_path = (settings.UPLOAD_DIR / f"tmp_{uuid.uuid4().hex}{ext}").resolve()

    try:
        # --- 2. Save the uploaded file temporarily ---
        # UPDATED: Structured logging
        logger.info(
            "Receiving and saving temporary file",
            extra={"user": current_user.username, "original_filename": filename, "temp_path": str(tmp_path)}
        )
        with tmp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # --- 3. Parse the file and register it ---
        # NEW: Added specific error handling for parsing/processing
        try:
            if ext == ".csv":
                file_id = register_csv_from_disk(tmp_path)
            else: # .xls or .xlsx
                df = pd.read_excel(tmp_path)
                file_id = register_dataframe(df)
        except (pd.errors.ParserError, ValueError) as e:
            # This is a client error: the file is malformed.
            logger.error(
                "Failed to parse the uploaded file",
                extra={"user": current_user.username, "filename": filename, "error_details": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not parse the file. Please ensure it is a valid {ext} file."
            )

        # --- 4. Persist metadata to the database ---
        persisted_csv_path = (settings.UPLOAD_DIR / f"{file_id}.csv").resolve()

        # NEW: Added specific error handling for database operations
        try:
            db_file = UploadedDBFile(
                id=file_id,
                filename=filename,
                content_type="text/csv",
                path=str(persisted_csv_path),
                uploaded_by=current_user.id,
            )
            db.add(db_file)
            db.commit()
            db.refresh(db_file)
        except SQLAlchemyError as e:
            logger.error(
                "Database error while saving file metadata",
                extra={"user": current_user.username, "file_id": file_id, "error_details": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A database error occurred while saving file information."
            )

        # --- 5. Success ---
        # UPDATED: Structured logging
        logger.info(
            "File processed and metadata stored successfully",
            extra={"user": current_user.username, "file_id": file_id, "original_filename": filename}
        )
        return {"file_id": file_id, "filename": filename}

    except Exception as e:
        # This is the final catch-all for truly unexpected errors (e.g., disk full, permissions error)
        # UPDATED: Using logger.critical with exc_info for structured tracebacks
        logger.critical(
            "An unexpected error occurred during the file upload process",
            exc_info=True, # This adds the full stack trace to the structured log
            extra={"user": current_user.username, "filename": filename}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected server error occurred during file upload."
        )
    finally:
        # This cleanup is important and correctly placed.
        tmp_path.unlink(missing_ok=True)
        await file.close()
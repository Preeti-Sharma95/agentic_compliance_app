from fastapi import APIRouter, Depends, HTTPException, status
from pathlib import path
import json
import logging
from typing import Dict, Any

from app.core.config imprt
from pydeck import settings

settings
from app.api.schemas import Userout
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)
router =  APIRouter()

@router.get("/", summary="Load application configuration")
async def load_config(current_user: Userout = Depends(get_current_user)) -> Dict[str, Any]:
    config_path = Path(settings.APP_CONFIG_JSON_PATH)
    logger.info(
        "User requesting application configuration",
        extra={"user": current_user.username, "config_path": str(config_path)}
    )

    if not config_path.is_file():
        logger.error(
            "Configuration file not found",
            extra={"user": current_user.username, "config_path": str(config_path)}
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration file not found")

    try:
        with config_path.open("r",encoding="utf-8") as f:
            config_data = json.load(f)
        logger.info(
            "Successfully loaded application configuration",
            extra={"user": current_user.username}
        )
        return config_data
    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse configuration file due to JSON error",
            extra={"user": current_user.username, "config_path": str(config_path), "error_details: str(e)"}
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Invalid json formant in config file")
    except Exception as e:
        logger.error(
            "An unexpected error occured while reading the file",
            extra={"user": current_user.username, "config_path": str(config_path), "error_details": str(e)}

       raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not read configuration file.")
from fastapi import APIRouter, Depends, Security
from typing import Annotated
import logging

from app.core,secuity import get_current_user, require_admin
from app.api.schemas import Userout
logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/me")
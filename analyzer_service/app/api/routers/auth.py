"""
API router for authenticated user endpoints.

This module provides endpoints that can only be accessed by users who have been
successfully authenticated via Azure AD. The authentication itself is handled
by the get_current_user dependency, which validates the Azure AD token.
"""
from fastapi import APIRouter, Depends, Security
from typing import Annotated
import logging

from app.core.security import get_current_user, require_admin
from app.api.schemas import UserOut

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/me", response_model=UserOut, summary="Get current user profile")
async def read_current_user(
    current_user: Annotated[UserOut, Depends(get_current_user)]
):
    """
    Fetch the profile of the currently authenticated user from our local database.

    This endpoint is protected by Azure AD authentication. It serves as a way for
    the client to verify the user's identity and retrieve their application-specific
    details (like their internal user ID and admin status).
    """
    logger.info(f"Fetching profile for authenticated user: '{current_user.username}'")
    return current_user


@router.get("/admin-only", response_model=dict, summary="Admin-only test endpoint")
async def admin_only_route(
    admin_user: Annotated[UserOut, Security(require_admin)]
):
    """
    An example of an admin-protected route.

    This endpoint can only be accessed by users who have a valid Azure AD token AND
    whose corresponding user entry in our local database has is_admin=True.
    """
    logger.info(f"Admin-only route accessed by user: '{admin_user.username}'")
    return {"message": f"Welcome, admin {admin_user.username}!"}
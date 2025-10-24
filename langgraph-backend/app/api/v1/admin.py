from typing import Any, Dict, Annotated
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_admin
from app.services.cache_services import redis

router = APIRouter()

@router.get(
    "/active_conversations",
    response_model=Dict[str, Any],
    summary="Lisr all active conversation",
    description=(
        "Retrieve all currently active conversations stored in Redis."
    )
)

async def active_conversation(admin: Annotated = Depends(get_current_admin)):
    if not redis:
        return {"active_conversations":{}}

    try:
        active = await redis.hgetall("active_chats")
    except Exception as e:
        return {"active_conversations": {}, "error": str(e)}

    return {"active_conversations": active}


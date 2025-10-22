"""
API router for the secure gateway functionality.

This gateway authenticates users and securely proxies requests to downstream
AI agent services, handling both standard JSON and streaming responses.
"""
import httpx
import logging
import json
from typing import Any, Dict, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Body, status, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user
from app.api.schemas import UserOut
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_AGENTS = {"dormant", "compliance", "ia-chat", "sql-bot"}


class AgentProxyRequest(BaseModel):
    """Defines the expected JSON body for a proxy request."""
    agent: str = Field(..., description="The name of the agent endpoint to call (e.g., 'dormant', 'compliance', 'ia-chat', 'sql-bot').")
    params: Dict[str, Any] = Field(default_factory=dict, description="A dictionary of query parameters to forward.")


async def _stream_downstream_response(url: str, params: dict, headers: dict) -> AsyncGenerator[bytes, None]:
    """
    An async generator that streams the response from a downstream service.

    It handles connection errors and HTTP status errors by yielding a
    structured error message within the event stream instead of raising
    an exception, which would terminate the client's connection abruptly.
    """
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", url, params=params, headers=headers, timeout=120.0) as response:


                # 1. Manually check for an error status code
                if response.status_code >= 400:
                    # 2. Read the error response body ONCE, while the stream is still open
                    error_text = await response.atext()

                    logger.error(
                        "Downstream service returned a streaming error",
                        extra={"target_url": str(response.request.url), "downstream_status": response.status_code,
                               "downstream_response": error_text}
                    )
                    error_payload = json.dumps({"type": "error", "message": f"Downstream error: {error_text}"})
                    yield f"data: {error_payload}\n\n".encode()

                    # 3. Stop the generator since we're done.
                    return

                # If the status is successful, stream the response as before
                async for chunk in response.aiter_bytes():
                    yield chunk



    except httpx.RequestError as exc:
        # This part for connection errors is correct and can remain as is.
        logger.error(
            "Streaming request to downstream service failed",
            extra={"target_url": str(exc.request.url), "error_details": str(exc)}
        )
        error_payload = json.dumps({"type": "error", "message": "Downstream service is unavailable."})
        yield f"data: {error_payload}\n\n".encode()
    # We no longer need the HTTPStatusError handler here, as it's handled inside the 'with' block.


# --- THIS IS THE LINE THAT WAS FIXED ---
@router.post("/", summary="Securely proxy a request to a downstream AI agent", response_model=None)
async def agent(
        request: Request,
        current_user: UserOut = Depends(get_current_user),
        payload: AgentProxyRequest = Body(...)
) -> StreamingResponse | JSONResponse:
    """
    Proxies a request to a specified downstream AI agent service.

    This endpoint validates the requested agent against an allowed list, then
    forwards the request. It supports both standard JSON responses and
    server-sent event (SSE) streams for real-time updates.

    Args:
        request (Request): The incoming request object from FastAPI.
        current_user (UserOut): The authenticated user, injected by dependency.
        payload (AgentProxyRequest): The JSON body containing the target agent and its parameters.

    Raises:
        HTTPException(400): If the specified 'agent' is not in the allowed list.
        HTTPException(503): If the downstream service is unavailable for a non-streaming request.
        HTTPException(>=400): If the downstream service returns an error for a non-streaming request.

    Returns:
        StreamingResponse: For streaming requests, provides a 'text/event-stream'.
        JSONResponse: For non-streaming requests, returns the JSON response from the agent.
    """
    if payload.agent not in ALLOWED_AGENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid agent specified. Allowed agents are: {', '.join(ALLOWED_AGENTS)}"
        )

    logger.info("User initiated proxy request", extra={"user": current_user.username, "agent": payload.agent})
    internal_headers = {"x-api-key": settings.INTERNAL_API_KEY, "x-internal-caller": "1"}
    target_url = f"{settings.AGENT_AI_SERVICE_URL}/{payload.agent}"
    is_streaming = payload.params.get("streaming", False)

    if is_streaming:
        logger.info("Initiating streaming request", extra={"user": current_user.username, "target_url": target_url})
        return StreamingResponse(
            _stream_downstream_response(target_url, payload.params, internal_headers),
            media_type="text/event-stream"
        )

    try:
        async with httpx.AsyncClient() as client:
            logger.info("Forwarding non-streaming request",
                        extra={"user": current_user.username, "target_url": target_url})
            response = await client.get(url=target_url, params=payload.params, headers=internal_headers, timeout=60.0)
            response.raise_for_status()
            logger.info("Successfully received non-streaming response from downstream",
                        extra={"user": current_user.username})
            return response.json()
    except httpx.RequestError as exc:
        logger.error("Request to downstream service failed",
                     extra={"user": current_user.username, "target_url": str(exc.request.url),
                            "error_details": str(exc)})
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="The downstream AI agent service is currently unavailable.")
    except httpx.HTTPStatusError as exc:
        logger.error("Downstream service returned a non-streaming error",
                     extra={"user": current_user.username, "target_url": str(exc.request.url),
                            "downstream_status": exc.response.status_code, "downstream_response": exc.response.text})
        raise HTTPException(status_code=exc.response.status_code,
                            detail=f"Downstream service error: {exc.response.text}")
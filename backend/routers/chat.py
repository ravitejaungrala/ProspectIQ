import logging
from fastapi import APIRouter

from schemas import ChatRequest, ChatResponse
from services.chat_agent import run_chat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Conversational prospecting assistant endpoint."""
    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    try:
        result = await run_chat(messages, req.context or {})
    except Exception as exc:
        logger.exception("chat agent crashed")
        return ChatResponse(
            reply="Sorry - something went wrong on my end. Please try again.",
            context=req.context or {},
            data={},
        )
    return ChatResponse(
        reply=result.get("reply", ""),
        context=result.get("context", {}) or {},
        data=result.get("data", {}) or {},
    )

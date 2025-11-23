from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    history: List[Dict[str, str]] = []


class ChatResponse(BaseModel):
    sql: str
    data: Any
    visualization: str  # 'bar', 'line', 'table'


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # Placeholder - se implementará en Fase 2
    return ChatResponse(sql="SELECT 1", data=[], visualization="table")



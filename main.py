from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from agent import SESSIONS, agent

app = FastAPI(title="Smart Banking Support Agent", version="1.0.0")
WEB_PAGE = Path(__file__).parent / "static" / "index.html"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: str | None = None


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(WEB_PAGE)


@app.post("/chat", tags=["Agent"])
def chat(request: ChatRequest):
    return agent.respond(request.message, request.conversation_id or str(uuid4()))


@app.delete("/conversation/{conversation_id}", tags=["Agent"])
def clear_conversation(conversation_id: str):
    SESSIONS.pop(conversation_id, None)
    return {"message": "Conversation cleared."}

"""可选 HTTP 入口。同步路由由 FastAPI 在线程池中执行阻塞的模型请求。"""

from typing import Literal

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .agent import run_agent
from .chat import build_messages
from .client import OllamaClient, OllamaError
from .config import Settings
from .rag import VectorIndex, answer_question


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=20000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=20000)
    history: list[Message] = Field(default_factory=list, max_length=40)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=20000)


class RagRequest(QuestionRequest):
    k: int = Field(default=3, ge=1, le=20)
    min_score: float = Field(default=-1, ge=-1, le=1)


def create_app(settings: Settings | None = None, client=None) -> FastAPI:
    settings = settings or Settings.from_env()
    client = client or OllamaClient(settings)
    app = FastAPI(title="LLM 学习实验室", version="0.2.0")

    @app.exception_handler(OllamaError)
    async def upstream_error(request: Request, exc: OllamaError):
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def input_error(request: Request, exc: ValueError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.get("/health")
    def health():
        # 存活检查不触发推理。实际连接验证使用 llm-lab doctor。
        return {"status": "ok", "model": settings.model}

    @app.post("/chat")
    def chat(body: ChatRequest):
        history = [message.model_dump() for message in body.history]
        messages = build_messages(body.question, history, history_turns=settings.history_turns)
        return {"answer": client.chat(messages).get("content", "")}

    @app.post("/rag")
    def rag(body: RagRequest):
        return answer_question(
            client, VectorIndex.load(settings.index_path), body.question, body.k, body.min_score
        )

    @app.post("/agent")
    def agent(body: QuestionRequest):
        return run_agent(client, body.question, max_tool_calls=settings.max_tool_calls)

    return app

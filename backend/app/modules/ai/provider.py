from typing import Protocol

from pydantic import BaseModel


class AIRequest(BaseModel):
    action_type: str
    input_text: str
    context_text: str = ""
    project_name: str | None = None
    task_title: str | None = None


class AIResponse(BaseModel):
    content: str
    summary: str


class AIProvider(Protocol):
    name: str

    async def analyze(self, request: AIRequest) -> AIResponse: ...

    async def plan(self, request: AIRequest) -> AIResponse: ...

    async def execute(self, request: AIRequest) -> AIResponse: ...

    async def summarize(self, request: AIRequest) -> AIResponse: ...

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: str
    content: str


class ChatMessageRequest(BaseModel):
    message: str
    page: str = "heatmap"
    history: list[ChatTurn] = Field(default_factory=list)


class ChatToolSnapshot(BaseModel):
    tool_name: str
    summary: str


class ChatMessageResponse(BaseModel):
    answer: str
    answer_ar: str | None = None
    voice_text_ar: str | None = None
    tools_used: list[ChatToolSnapshot] = Field(default_factory=list)
    suggested_prompts: list[str] = Field(default_factory=list)
    used_llm: bool = False
    page: str

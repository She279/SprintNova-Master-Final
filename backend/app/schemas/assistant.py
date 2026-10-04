from pydantic import BaseModel


class AssistantQueryRequest(BaseModel):
    question: str


class RetrievedSource(BaseModel):
    id: int
    title: str
    doc_type: str
    snippet: str


class AssistantQueryResponse(BaseModel):
    answer: str
    ai_generated: bool
    retrieval_method: str  # "vector" | "keyword" | "none" (no documents indexed)
    sources: list[RetrievedSource]

"""Pydantic schemas for daily work update analysis."""
from datetime import datetime
from pydantic import BaseModel, Field


class DailyWorkUpdateAnalysisBase(BaseModel):
    """Base schema for analysis data."""
    summary: str | None = None
    completed_items: str | None = None
    pending_items: str | None = None
    detected_blockers: str | None = None
    risk_level: str = Field(default="low")
    risk_reason: str | None = None
    suggested_progress: int | None = Field(None, ge=0, le=100)
    suggested_actions: str | None = None
    task_suggestions: str | None = None
    ai_provider: str = Field(default="rule_based")
    model_version: str | None = None


class DailyWorkUpdateAnalysisCreate(DailyWorkUpdateAnalysisBase):
    """Schema for creating an analysis (internally used)."""
    daily_update_id: int


class DailyWorkUpdateAnalysisResponse(DailyWorkUpdateAnalysisBase):
    """Schema for returning analysis data."""
    id: int
    daily_update_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TaskSuggestion(BaseModel):
    """A single task status suggestion from AI analysis."""
    task_id: int
    task_key: str
    current_status: str
    suggested_status: str
    reason: str


class AnalysisWithSuggestions(DailyWorkUpdateAnalysisResponse):
    """Analysis response with parsed task suggestions."""
    task_suggestions_parsed: list[TaskSuggestion] | None = None

    class Config:
        from_attributes = True

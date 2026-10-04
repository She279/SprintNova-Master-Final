"""Pydantic schemas for daily work updates."""
from datetime import datetime, date as Date
from pydantic import BaseModel, Field


class DailyWorkUpdateBase(BaseModel):
    """Base schema for daily work update data."""
    project_id: int | None = None
    work_done: str | None = None
    completed_work: str | None = None
    pending_work: str | None = None
    blockers: str | None = None
    additional_notes: str | None = None
    progress_percentage: int | None = Field(None, ge=0, le=100)


class DailyWorkUpdateCreate(DailyWorkUpdateBase):
    """Schema for creating a daily work update."""
    date: Date | None = None  # If None, defaults to today


class DailyWorkUpdateUpdate(BaseModel):
    """Schema for updating an existing daily work update."""
    work_done: str | None = None
    completed_work: str | None = None
    pending_work: str | None = None
    blockers: str | None = None
    additional_notes: str | None = None
    progress_percentage: int | None = Field(None, ge=0, le=100)


class DailyWorkUpdateResponse(DailyWorkUpdateBase):
    """Schema for returning daily work update data."""
    id: int
    user_id: int
    date: Date
    submitted_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DailyWorkUpdateDetailResponse(DailyWorkUpdateResponse):
    """Detailed daily work update response with analysis."""
    analysis: dict | None = None  # Will be populated by API if analysis exists

    class Config:
        from_attributes = True

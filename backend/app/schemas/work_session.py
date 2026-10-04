"""Pydantic schemas for work session management."""
from datetime import datetime
from pydantic import BaseModel, Field


class WorkSessionBase(BaseModel):
    """Base schema for work session data."""
    status: str = Field(default="active")


class WorkSessionCreate(WorkSessionBase):
    """Schema for creating a new work session."""
    pass


class WorkSessionUpdate(BaseModel):
    """Schema for updating a work session (mainly for stopping it)."""
    ended_at: datetime | None = None
    total_work_minutes: int | None = None
    status: str | None = None


class WorkSessionResponse(WorkSessionBase):
    """Schema for returning work session data."""
    id: int
    user_id: int
    started_at: datetime
    ended_at: datetime | None = None
    total_work_minutes: int | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkSessionDetailResponse(WorkSessionResponse):
    """Detailed work session response with computed fields."""
    elapsed_minutes: int | None = None  # Computed field for active sessions

    class Config:
        from_attributes = True

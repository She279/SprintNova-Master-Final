"""Pydantic schemas for weekly availability management."""
from datetime import datetime, time
from pydantic import BaseModel, Field


class WeeklyAvailabilityBase(BaseModel):
    """Base schema for weekly availability data."""
    day_of_week: str = Field(...)
    start_time: time | None = None
    end_time: time | None = None
    timezone: str | None = Field(default="UTC")


class WeeklyAvailabilityCreate(WeeklyAvailabilityBase):
    """Schema for creating weekly availability entries."""
    pass


class WeeklyAvailabilityUpdate(BaseModel):
    """Schema for updating weekly availability."""
    start_time: time | None = None
    end_time: time | None = None
    timezone: str | None = None


class WeeklyAvailabilityResponse(WeeklyAvailabilityBase):
    """Schema for returning weekly availability data."""
    id: int
    user_id: int
    effective_from: datetime
    effective_to: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WeeklyScheduleSetup(BaseModel):
    """Schema for setting up an entire weekly schedule."""
    timezone: str = Field(default="UTC")
    schedule: dict[str, dict[str, str | None]] = Field(
        ...,
        example={
            "monday": {"start_time": "09:00", "end_time": "17:30"},
            "tuesday": {"start_time": "09:00", "end_time": "17:30"},
            "wednesday": {"start_time": "09:00", "end_time": "17:30"},
            "thursday": {"start_time": "09:00", "end_time": "17:30"},
            "friday": {"start_time": "09:00", "end_time": "17:30"},
            "saturday": {"start_time": None, "end_time": None},
            "sunday": {"start_time": None, "end_time": None},
        }
    )


class FullWeeklyScheduleResponse(BaseModel):
    """Schema for returning complete weekly schedule for a user."""
    user_id: int
    timezone: str
    schedule: list[WeeklyAvailabilityResponse]
    is_configured: bool

    class Config:
        from_attributes = True

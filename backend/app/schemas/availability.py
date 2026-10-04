from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.availability import AvailabilityStatus


class AvailabilitySetRequest(BaseModel):
    date: date
    status: AvailabilityStatus
    hours_available: float | None = None
    note: str | None = None


class AvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    date: date
    status: AvailabilityStatus
    hours_available: float | None
    note: str | None
    created_at: datetime


class TeamAvailabilityDay(BaseModel):
    date: date
    user_id: int
    full_name: str
    status: AvailabilityStatus
    hours_available: float | None
class WeeklyDaySchedule(BaseModel):
    start_time: str | None = None
    end_time: str | None = None


class WeeklyAvailabilitySetupRequest(BaseModel):
    timezone: str = "UTC"
    schedule: dict[str, WeeklyDaySchedule]
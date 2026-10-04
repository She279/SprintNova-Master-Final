from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.leave import LeaveType, LeaveStatus


class LeaveRequestCreateRequest(BaseModel):
    type: LeaveType
    start_date: date
    end_date: date
    start_time: str | None = None  # "HH:MM", required for PERMISSION
    end_time: str | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def validate_permission_times(self):
        if self.type == LeaveType.PERMISSION:
            if self.start_date != self.end_date:
                raise ValueError("A permission request must be within a single day")
            if not self.start_time or not self.end_time:
                raise ValueError("start_time and end_time are required for a permission request")
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self


class LeaveDecisionRequest(BaseModel):
    approve: bool
    review_note: str | None = None


class LeaveRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    type: LeaveType
    start_date: date
    end_date: date
    start_time: str | None
    end_time: str | None
    reason: str | None
    status: LeaveStatus
    reviewed_by_id: int | None
    reviewed_at: datetime | None
    review_note: str | None
    created_at: datetime


class LeaveRequestWithEmployee(LeaveRequestResponse):
    full_name: str
    company_email: str

from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ProjectAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    uploaded_by_id: int
    original_name: str
    content_type: str | None
    size_bytes: int
    created_at: datetime

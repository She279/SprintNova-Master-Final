from datetime import datetime
from pydantic import BaseModel

class HealthRisk(BaseModel):
    severity: str
    type: str
    title: str
    detail: str

class ProjectHealthResponse(BaseModel):
    project_id: int
    project_code: str
    project_name: str
    overall_health: int
    health_label: str
    components: dict[str, int]
    signals: dict
    risks: list[HealthRisk]
    recommendations: list[str]
    generated_at: datetime

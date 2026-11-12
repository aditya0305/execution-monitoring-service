
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class ExecutionCreate(BaseModel):
    pipeline_id: int = Field(gt=0)
    simulate_failure: bool = False
    fail_attempts: int = Field(default=0, ge=0, le=20)

class ExecutionResponse(BaseModel):
    id: int
    pipeline_id: int
    pipeline_name: str
    status: str
    retry_count: int
    simulate_failure: bool
    start_time: datetime
    end_time: datetime | None
    error_message: str | None

    model_config = ConfigDict(from_attributes=True)

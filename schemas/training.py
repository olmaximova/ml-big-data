from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TrainingStartRequest(BaseModel):
    target_column: str

class TrainingResponse(BaseModel):
    job_id: str
    upload_id: str
    status: str

class TrainingStatusResponse(BaseModel):
    job_id: str
    status: str
    accuracy: Optional[float] = None
    features_used: Optional[int] = None
    mse: Optional[float] = None
    completed_at: Optional[datetime] = None
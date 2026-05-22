from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Dict, Any, Optional

class UploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    upload_id: str
    filename: str
    status: str = "success"  
    rows_count: int
    columns: List[str]
    statistics: Optional[Dict[str, Dict[str, Any]]] = None
    preview: Optional[List[List[Any]]] = None  
    created_at: Optional[datetime] = None     
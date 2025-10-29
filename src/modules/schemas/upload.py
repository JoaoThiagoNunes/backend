from pydantic import BaseModel
from typing import List, Optional, Any

class UploadCreate(BaseModel):
    filename: str
    total_escolas: int

class UploadInfo(BaseModel):
    upload_id: int
    filename: str
    rows: int
    columns: int
    column_names: List[str]
    data: Optional[List[dict]] = None

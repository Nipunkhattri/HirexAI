from pydantic import BaseModel, Field
from typing import List, Optional

class interview_data(BaseModel):
    domain: str = Field(..., example="Software Development")
    interview_date: str = Field(..., example="2023-10-01")
    interview_time: str = Field(..., example="10:00 AM")
    list_of_candidates: List[dict] = Field(..., example=[{"name": "John Doe", "email": "john@example.com"}])
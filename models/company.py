from pydantic import BaseModel, Field
from typing import List, Optional

class interview_data(BaseModel):
    domain: str = Field(..., example="Software Development")
    interview_date: str = Field(..., example="2023-10-01")
    interview_time: str = Field(..., example="10:00 AM")
    list_of_candidates: List[dict] = Field(..., example=[{"name": "John Doe", "email": "john@example.com"}])


class SubmitTestAnswer(BaseModel):
    interview_id: str = Field(..., example="interview_12345")
    question: str = Field(..., example="What is your name?")
    answer_text: str = Field(..., example="John Doe")
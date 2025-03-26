from pydantic import BaseModel
from typing import List, Dict

class DomainInfo(BaseModel):
    skills: List[str]

class DomainsResponse(BaseModel):
    status: str
    message: str
    resume_id: str
    domains: Dict[str, DomainInfo]

class SkillsRequest(BaseModel):
    skills: List[str]
    resume_id: str
    DomainName: str

class QuestionsResponse(BaseModel):
    questions: List[str]
    
class SubmitAnswer(BaseModel):
    question:str
    answer_text:str
    DomainName: str
    resume_id: str
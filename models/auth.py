from pydantic import BaseModel, EmailStr
from typing import List, Optional

class RegisterSchema(BaseModel):
    name: str
    email: EmailStr
    password: str
    
class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class CompanyLoginSchema(BaseModel):
    email: EmailStr
    password: str
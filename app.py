from typing import Union,List
from fastapi import FastAPI , status
from fastapi.middleware.cors import CORSMiddleware
from views.resume import resume_router
from views.auth import auth_router
from contextlib import asynccontextmanager
from database.mongodb import db

app = FastAPI()

origins: List = ['http://localhost:3000']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume_router)
app.include_router(auth_router)

@app.get("/", status_code=status.HTTP_200_OK)
def root() -> dict:
    return {"message": "Welcome to FastAPI SAAS Template", "docs": "/docs"}
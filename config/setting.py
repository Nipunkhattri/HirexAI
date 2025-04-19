from pydantic_settings import BaseSettings
from fastapi_mail import ConnectionConfig

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    DEEPGRAM_API_KEY: str
    MONGODB_URI:str
    port:8000
    ACCESS_TOKEN_EXPIRE_MINUTES:int
    SECRET_KEY:str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "HirexAI"
    
    class Config:
        env_file = ".env"

settings = Settings()

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)
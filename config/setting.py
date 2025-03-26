from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    DEEPGRAM_API_KEY: str
    MONGODB_URI:str
    port:8000
    ACCESS_TOKEN_EXPIRE_MINUTES:int
    SECRET_KEY:str
    
    class Config:
        env_file = ".env"

settings = Settings()
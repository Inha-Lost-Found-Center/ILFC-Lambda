from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # .env 파일에서 읽어올 변수들
    DATABASE_URL: str
    SECRET_KEY: str

    # JWT 관련 설정
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

settings = Settings()

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # .env 파일에서 읽어올 변수들
    DATABASE_URL: str
    SECRET_KEY: str

    AWS_REGION: str = "us-west-2"
    DYNAMODB_TABLE_VERIFICATION: str = "inha-capstone-14-VerificationCodes"

    GMAIL_USER: str
    GMAIL_PASSWORD: str

    # JWT 관련 설정
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

settings = Settings()

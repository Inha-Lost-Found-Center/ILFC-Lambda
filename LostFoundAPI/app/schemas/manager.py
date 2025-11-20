from pydantic import BaseModel, EmailStr
from app.models.manager import ManagerRole

# 로그인 요청 (Request)
class ManagerLogin(BaseModel):
    email: EmailStr
    password: str

# 관리자 정보 응답 (Response)
class ManagerResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: ManagerRole
    is_active: bool

    class Config:
        from_attributes = True

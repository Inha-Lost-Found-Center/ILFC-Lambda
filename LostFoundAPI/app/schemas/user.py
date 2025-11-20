from pydantic import BaseModel, EmailStr

# 1.7 회원가입 (Request)
# API가 '받을' 데이터. 이메일과 비밀번호가 필요.
class UserCreate(BaseModel):
    email: EmailStr  # Pydantic이 자동으로 유효한 이메일 형식인지 검사
    password: str
    name: str
    contact_info: str | None = None  # 선택적 정보 ( | None = None )

# UserCreate를 상속받으므로 위 4개 필드는 자동으로 포함되고, 토큰만 추가됨
class UserCreateVerified(UserCreate):
    verification_token: str

# 1.7 회원가입 (Response)
# API가 '반환할' 데이터. 비밀번호는 절대 반환하면 안 됨.
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str

    class Config:
        from_attributes = True

# 1.8 로그인 (Response - Token)
# 로그인이 성공하면 이 형식으로 Access Token을 반환.
class Token(BaseModel):
    access_token: str
    token_type: str

# 1.8 로그인 (Request)
# (이전에 정의했던 스키마. JSON으로 로그인을 받는 경우)
class UserLogin(BaseModel):
    email: EmailStr
    password: str

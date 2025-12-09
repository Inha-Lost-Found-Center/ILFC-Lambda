from pydantic import BaseModel

# 태그 API의 응답(Response)에 사용될 스키마
class TagResponse(BaseModel):
    id: int
    name: str
    locker_number: int | None = None

    class Config:
        from_attributes = True

# 관리자용 태그 생성/수정 스키마
class TagCreate(BaseModel):
    name: str

class TagUpdate(BaseModel):
    name: str

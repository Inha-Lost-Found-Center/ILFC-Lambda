from pydantic import BaseModel

# 태그 API의 응답(Response)에 사용될 스키마
class TagResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

from pydantic import BaseModel
import datetime
from typing import List
from .tag import TagResponse

# Item 응답 스키마
class ItemResponse(BaseModel):
    id: int
    photo_url: str
    location: str | None = None
    status: str
    registered_at: datetime.datetime

    tags: List[TagResponse] = []

    class Config:
        from_attributes = True

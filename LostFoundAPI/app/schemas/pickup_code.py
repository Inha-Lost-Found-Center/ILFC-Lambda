from pydantic import BaseModel
import datetime

class PickupCodeResponse(BaseModel):
    code: str
    expires_at: datetime.datetime

    class Config:
        from_attributes = True

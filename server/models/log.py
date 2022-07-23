import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Log(BaseModel):
    text: str = Field(..., description="The log text")
    source: str = Field(..., description="The log source")
    createdAt: Optional[str] = Field(default=str(datetime.datetime.utcnow()), description="The time of story creation")

    class Config:
        schema_extra = {
            "example": {
                "text": "ERROR",
                "nameAr": "shorts",
            }
        }

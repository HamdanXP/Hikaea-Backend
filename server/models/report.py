import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Comment(BaseModel):
    content: str = Field(..., description="The report's content")
    type: str = Field(..., description="The report's type")
    reportedId: str = Field(..., description="The reported user id")
    reporterId: str = Field(..., description="The reporter user id")
    status: Optional[str] = Field(default="pending", description="The comment's status")

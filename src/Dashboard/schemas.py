from typing import Optional

from pydantic import BaseModel, Field


class AdminUpdateStory(BaseModel):
    storyId: str = Field(..., description="The story's ID")
    adminMessage: Optional[str] = Field(default=None, description="The admin massage")
    notify: Optional[bool] = Field(default=False, description="Notify the users about the story or not?")
    status: str = Field(..., description="The story's status ('published', 'pending', 'draft', 'rejected', 'deleted')")

    class Config:
        schema_extra = {
            "example": {
                "storyId": "1111",
                "adminMessage": "تم قبول قصتك!",
                "notify": True,
                "status": "published"
            }
        }

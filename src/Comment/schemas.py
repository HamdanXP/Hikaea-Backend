from typing import Optional

from pydantic import BaseModel, Field


class Comment(BaseModel):
    commenterId: str = Field(..., description="The commenter uid")
    storyId: str = Field(..., description="The story's id")
    comment: str = Field(..., description="The comment")
    replyToId: Optional[str] = Field(default=None, description="If the comment is reply, put the id of the user")

    class Config:
        schema_extra = {
            "example": {
                "commenterId": "1234",
                "storyId": "1234",
                "comment": "Great story",
            }
        }


class UpdateComment(BaseModel):
    commentId: str = Field(..., description="The comment's ID")
    commenterId: str = Field(..., description="The commenter uid")
    storyId: str = Field(..., description="The story's id")
    comment: str = Field(..., description="The comment")
    status: Optional[str] = Field(default="published", description="The comment's status")

    class Config:
        schema_extra = {
            "example": {
                "commentId": "11111",
                "commenterId": "1234",
                "storyId": "1234",
                "comment": "Great story",
                "status": "deleted"
            }
        }

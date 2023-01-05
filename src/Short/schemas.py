from typing import Optional

from pydantic import BaseModel, Field


class Short(BaseModel):
    text: str = Field(..., description="The short's text")
    type: str = Field(..., description="The short's type (short, anecdote, confession, quote)")
    isAnon: Optional[bool] = Field(default=True, description="is this the writer's anonymous?")
    writerId: Optional[str] = Field(default=None, description="The writer's id (If not anonymous)")
    tiktokId: Optional[str] = Field(default="", description="The writer's tiktok id")
    FCM: Optional[str] = Field(default=None, description="The writer's notification's ID")

    class Config:
        schema_extra = {
            "example": {
                "text": "My short",
                "type": "confession",
                "isAnon": True,
                "tiktokId": "@SSWWW",
            }
        }


class ShortComment(BaseModel):
    shortId: str = Field(..., description="The short's ID")
    comment: str = Field(..., description="The short's comment")

    class Config:
        schema_extra = {
            "example": {
                "shortId": "1121",
                "comment": "Great short",
            }
        }


class ShortCommentVote(BaseModel):
    shortId: str = Field(..., description="The short's ID")
    commentId: str = Field(..., description="The short's comment's ID")

    class Config:
        schema_extra = {
            "example": {
                "shortId": "1121",
                "commentId": "11221",
            }
        }


class ShortVote(BaseModel):
    shortId: str = Field(..., description="The short's ID")

    class Config:
        schema_extra = {
            "example": {
                "shortId": "1121",
            }
        }

from pydantic import BaseModel, Field


class Follow(BaseModel):
    initiatorId: str = Field(..., description="The user who initiated the action")
    toBeFollowedId: str = Field(..., description="The user to be followed")


class Block(BaseModel):
    initiatorId: str = Field(..., description="The user who initiated the action")
    toBeBlockedId: str = Field(..., description="The user to be blocked")
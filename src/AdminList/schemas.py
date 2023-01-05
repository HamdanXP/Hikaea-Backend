from pydantic import BaseModel, Field


class AdminList(BaseModel):
    title: str = Field(..., description="The title of the admin list")
    status: str = Field(..., description="The status of the list whether it's private or public")

    class Config:
        schema_extra = {
            "example": {
                "title": "القصص المميزة",
                "status": "public",
            }
        }


class UpdateAdminList(BaseModel):
    listId: str = Field(..., description="The id of the list you want to update")
    operation: str = Field(..., description="Either 'add' or 'remove'")
    storyId: str = Field(..., description="The id of the story you want to add or remove")

    class Config:
        schema_extra = {
            "example": {
                "listId": "62e7ff15760308e51ca6d853",
                "operation": "add",
                "storyId": "62486102b6cd2173886cb3df",
            }
        }

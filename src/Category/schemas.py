from pydantic import BaseModel, Field


class Category(BaseModel):
    name: str = Field(..., description="The category name in English")
    nameAr: str = Field(..., description="The category name in Arabic")

    class Config:
        schema_extra = {
            "example": {
                "name": "Comedy",
                "nameAr": "كوميديا",
            }
        }
from pydantic import BaseModel, Field, EmailStr


class UniqueInfo(BaseModel):
    username: str = Field(..., description="The username")
    email: EmailStr = Field(..., description="The email")

    class Config:
        schema_extra = {
            "example": {
                "username": "user",
                "email": "email@emai.com",
            }
        }

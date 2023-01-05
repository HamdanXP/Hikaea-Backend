from pydantic import BaseModel, Field


class Report(BaseModel):
    content: str = Field(..., description="The report content (What is being reported)")
    type: str = Field(..., description="The type of the reported (Story, Profile, ...)")
    reportedId: str = Field(..., description="The ID of the reported entity")
    reporterId: str = Field(..., description="The ID of the report's issuer")

    class Config:
        schema_extra = {
            "example": {
                "content": "Hateful or abusive content",
                "type": "reportStory",
                "reportedId": "1111",
                "reporterId": "1234",
            }
        }


class UpdateReport(BaseModel):
    reportID: str = Field(..., description="The report's ID")
    status: str = Field(..., description="The report's status")

    class Config:
        schema_extra = {
            "example": {
                "reportID": "11111",
                "status": "approved"
            }
        }

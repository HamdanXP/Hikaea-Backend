from typing import Optional

from pydantic import BaseModel, Field


class Blog(BaseModel):
    title: str = Field(..., description="The blog's title")
    content: str = Field(..., description="The blog's content")
    writerName: str = Field(..., description="The writer's name")
    categories: Optional[list] = Field(default=[], description="The blog's categories IDs")
    blogCover: str = Field(..., description="The blog's cover")

    class Config:
        schema_extra = {
            "example": {
                "title": "قصة خليفة شيرلوك هولمز – لا تطيع فضولك",
                "content": "",
                "writerName": "عبدالرحمن القصاص",
                "blogCover": "https://nationaltoday.com/wp-content/uploads/2022/06/5-Sherlock.jpg"
            }
        }

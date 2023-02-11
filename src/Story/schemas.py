from typing import Optional, List

from pydantic import BaseModel, Field


class Story(BaseModel):
    type: str = Field(..., description="The story's type 'normal' or 'chat'")
    writerId: str = Field(..., description="The writer uid")
    content: List[object] = Field(..., description="The story's content")
    characters: Optional[List[str]] = Field(default=None, description="The story's characters (for 'chat' stories)")
    title: str = Field(..., description="The story's title")
    description: str = Field(..., description="The story's description")
    categories: list = Field(..., description="The story's categories IDs")
    storyCover: str = Field(..., description="The story's cover")
    status: str = Field(..., description="The story's status ('published', 'pending', 'draft', 'rejected', 'deleted')")

    class Config:
        schema_extra = {
            "example": {
                "type": "normal",
                "writerId": "1234",
                "content": [{"text": "This is the first page"}, {"text": "this is the second page"}],
                "title": "My story",
                "description": "This is a great story",
                "categories": ["123asas45", "1234sas5"],
                "storyCover": "http://image",
                "status": "pending"
            }
        }


class UpdateStory(BaseModel):
    storyId: str = Field(..., description="The story's ID")
    type: Optional[str] = Field(default=None, description="The story's type 'normal' or 'chat'")
    content: List[object] = Field(..., description="The story's content")
    characters: Optional[List[str]] = Field(default=None, description="The story's characters (for 'chat' stories)")
    title: str = Field(..., description="The story's title")
    description: str = Field(..., description="The story's description")
    categories: list = Field(..., description="The story's categories IDs")
    storyCover: str = Field(..., description="The story's cover")
    status: str = Field(..., description="The story's status ('published', 'pending', 'draft', 'rejected', 'deleted')")

    class Config:
        schema_extra = {
            "example": {
                "storyId": "1111",
                "type": "normal",
                "content": [{"text": "This is the first page"}, {"text": "this is the second page"}],
                "title": "My story",
                "description": "This is a great story",
                "categories": ["123asas45", "1234sas5"],
                "storyCover": "http://image",
                "status": "pending"
            }
        }


class StoryID(BaseModel):
    storyId: str = Field(..., description="The story's ID (will be generated by the database)")


class StoryReader(BaseModel):
    readerId: str = Field(..., description="The reader's ID")
    storyId: str = Field(..., description="The story's ID (will be generated by the database)")


class StoryLiker(BaseModel):
    likerId: str = Field(..., description="The liker's ID")
    storyId: str = Field(..., description="The story's ID (will be generated by the database)")


class StoriesQuery(BaseModel):
    nextPage: Optional[str] = Field(default=None,
                                    description="The next page index (The id of the last story in the previous page)")
    categories: Optional[List[str]] = Field(default=[], description="The categories you want")
    sortWay: Optional[str] = Field(default="new",
                                   description="The way you want to sort the stories (new, top, trending)")


class BuyChapter(BaseModel):
    uid: str = Field(..., description="The user's uid")
    storyId: str = Field(..., description="The story's ID")
    chapterNumber: int = Field(..., description="The chapter number")

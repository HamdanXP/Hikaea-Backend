import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    uid: str = Field(..., description="The user id (from firebase)")
    username: str = Field(..., description="The username entered by the user")
    name: str = Field(..., description="The display name")
    email: Optional[EmailStr] = Field(default=None, description="The email (could be null if the user used twitter for authentication)")
    birthDate: Optional[str] = Field(default=None, description="The user birth date")
    profileImage: Optional[str] = Field(default=None, description="The user profile image")
    bio: Optional[str] = Field(default="", description="The user's bio")
    sex: Optional[str] = Field(default="undetermined", description="The user's sex")
    personalLink: Optional[str] = Field(default="", description="The user's personal link")
    followersList: Optional[list] = Field(default=[])
    followingList: Optional[list] = Field(default=[])
    blockedUserList: Optional[list] = Field(default=[])
    createdAt: Optional[str] = Field(default=str(datetime.datetime.utcnow()), description="The time of user creation")
    status: Optional[str] = Field(default="active", description="The user's status")
    readStories: Optional[list] = Field(default=[])
    likedStories: Optional[list] = Field(default=[])
    userStories: Optional[list] = Field(default=[])
    storyLists: Optional[object] = Field(default={
        str(ObjectId()):
            {
                "title": 'readLater',
                "listStoryIds": [],
                "status": "private",
            }
    })

    class Config:
        schema_extra = {
            "example": {
                "uid": "1234",
                "username": "user1234",
                "name": "user1234",
                "email": "jdoe@x.edu.ng",
                "birthDate": "01/01/1990",
                "profileImage": None,
            }
        }


class UpdateUserModel(BaseModel):
    name: str = Field(..., description="The display name")
    email: EmailStr = Field(..., description="The user's email")
    birthDate: Optional[str] = Field(default=None, description="The user birth date")
    profileImage: Optional[str] = Field(default=None, description="The user profile image")
    bio: Optional[str] = Field(default="", description="The user's bio")
    sex: Optional[str] = Field(default="undetermined", description="The user's sex")
    personalLink: Optional[str] = Field(default="", description="The user's personal link")

    class Config:
        schema_extra = {
            "example": {
                "name": "user1234",
                "email": "jdoe@x.edu.ng",
                "birthDate": "01/01/1990",
                "profileImage": None,
                "bio": "Hello",
                "sex": "male",
                "personalLink": "www.google.com"
            }
        }
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    uid: str = Field(..., description="The user id (from firebase)")
    username: str = Field(..., description="The username entered by the user")
    name: str = Field(..., description="The display name")
    email: Optional[EmailStr] = Field(default=None, description="The user's email")
    birthDate: Optional[str] = Field(default=None, description="The user birth date")
    profileImage: Optional[str] = Field(default=None, description="The user profile image")

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


class UpdateUser(BaseModel):
    uid: str = Field(..., description="The user id (from firebase)")
    name: Optional[str] = Field(default=None, description="The display name")
    username: Optional[str] = Field(default=None, description="The user's username")
    email: Optional[EmailStr] = Field(default=None, description="The user's email")
    birthDate: Optional[str] = Field(default=None, description="The user birth date")
    profileImage: Optional[str] = Field(default=None, description="The user profile image")
    bio: Optional[str] = Field(default=None, description="The user's bio")
    sex: Optional[str] = Field(default=None, description="The user's sex")
    FMC: Optional[str] = Field(default=None, description="The user's notification's id")
    subscriptionTier: Optional[str] = Field(default=None, description="The user's subscription tier")
    subscriptionExpiry: Optional[str] = Field(default=None, description="The user's subscription expiry date")
    personalLink: Optional[str] = Field(default=None, description="The user's personal link")

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


class EmailAndUsername(BaseModel):
    username: Optional[str] = Field(default=None, description="The username entered by the user")
    email: Optional[EmailStr] = Field(default=None, description="The user's email")


class Follow(BaseModel):
    initiatorId: str = Field(..., description="The user who initiated the action")
    toBeFollowedId: str = Field(..., description="The user to be followed")


class Block(BaseModel):
    initiatorId: str = Field(..., description="The user who initiated the action")
    toBeBlockedId: str = Field(..., description="The user to be blocked")


class SubscriptionInfo(BaseModel):
    uid: str = Field(..., description="The user's uid")
    subscriptionTier: str = Field(..., description="The user's subscription tier")
    subscriptionExpiry: str = Field(..., description="The user's subscription expiry")


class UserStoriesList(BaseModel):
    initiatorId: str = Field(..., description="The list's creator id")
    title: str = Field(..., description="The list's tile")
    status: str = Field(..., description="The list's status")
    listId: Optional[str] = Field(default=None, description="The list's id")


class UserStoriesListItem(BaseModel):
    initiatorId: str = Field(..., description="The list's creator id")
    listId: str = Field(..., description="The list's id")
    storyId: str = Field(..., description="The new story's id")

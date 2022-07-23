from fastapi import APIRouter

from server.models.uniqueInfo import UniqueInfo
from server.models.user import User, UpdateUserModel
from server.models.userToUserActions import Follow, Block

router = APIRouter(tags=['Users'])


@router.put("/sign_up", description="Use to create a new user", status_code=201)
def create_user(user: User):
    return {"uid": user.uid}


@router.post("/check_unique_info", description="Use before registering the user to avoid duplicated", status_code=201)
def check_unique_info(unique_info: UniqueInfo):
    return {"message": "User information is valid and unique"}


@router.get("/get_user_profile/{identifier}", description="Use to get the user profile", response_model=User)
def get_user_profile():
    return User()


@router.put("/update_user_profile", description="Use to update the user profile", status_code=200)
def update_user_profile(update_user_model: UpdateUserModel):
    return None


@router.put("/follow", description="Use to follow a user", status_code=201)
def follow_user(follow_obj: Follow):
    return None


@router.delete("/unfollow/{initiator_id}/{to_be_unfollowed_id}", description="Use to unfollow a user", status_code=200)
def unfollow_user(initiator_id: str, to_be_unfollowed_id: str):
    return None


@router.put("/block", description="Use to block a user", status_code=201)
def block_user(block_obj: Block):
    return None


@router.delete("/unblock/{initiator_id}/{to_be_unfollowed_id}", description="Use to unblock a user", status_code=200)
def unblock_user(initiator_id: str, to_be_unblocked_id: str):
    return None

import datetime
import uuid

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Response, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi_redis_cache import cache_one_minute

from db import db
from src.User.schemas import User, UpdateUser, EmailAndUsername, Follow, Block, SubscriptionInfo, UserStoriesList, \
    UserStoriesListItem, UpdateCoins, Referral
from src.utils import send_notification, notify_admin

router = APIRouter(tags=['User'])


@router.put("/sign_up", description="Use to create a new user", status_code=201)
async def sign_up(user: User, background_tasks: BackgroundTasks):
    background_tasks.add_task(create_user, user)
    return {"message": "The user has been created successfully"}


@router.post("/check_unique_info", description="Use before registering the user to avoid duplicated", status_code=200)
async def check_unique_info(email_and_username: EmailAndUsername, res: Response):
    not_unique_user = None
    not_unique_email = None
    if email_and_username.username is not None:
        not_unique_user = len(list(db.users.find({'username': email_and_username.username}).collation(
            {'locale': 'en', 'strength': 2}))) > 0
    if email_and_username.email is not None:
        not_unique_email = len(list(db.users.find({'email': email_and_username.email}).collation(
            {'locale': 'en', 'strength': 2}))) > 0

    if not_unique_user or (not_unique_email and email_and_username.email is not None):
        if not_unique_user:
            response = {
                "message": 'The username is not unique, please choose another username',
                "messageAr": "اسم المستخدم موجود من قبل، رجاء حاول استخدام اسم اخر"
            }
        else:
            response = {
                "message": 'The email is not unique,please choose another email',
                "messageAr": "البريد الالكتروني موجود من قبل، رجاء حاول استخدام بريد الكتروني اخر"
            }
        res.status_code = status.HTTP_400_BAD_REQUEST
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json; charset=UTF-8'
        }
        return JSONResponse(content=response, headers=headers)
    else:
        response = {
            "message": "User information is valid and unique"
        }
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json; charset=UTF-8'
        }
        return JSONResponse(content=response, headers=headers)


@router.get("/get_user_profile/{identifier}", description="Use to get the user profile")
@cache_one_minute()
async def get_user_profile(identifier: str, searchBy: str = 'uid'):
    user = list(db.users.aggregate([
        {"$match": {searchBy: identifier}},
        {
            "$lookup": {
                "from": "Story",
                "let": {"writerId": "$uid", 'writerName': '$name'},
                "pipeline": [
                    {"$match": {"$and": [{"$expr": {"$eq": ["$writerId", "$$writerId"]}}, {'status': 'published'}]}},
                    {
                        "$project": {
                            "_id": 0,
                            "storyId": {"$toString": "$_id"},
                            "writerName": "$$writerName",
                            "title": 1,
                            "slug": 1,
                            "storyCover": 1,
                            "categories": 1,
                            "description": 1,
                        }
                    }
                ],
                "as": "userStories"
            }
        },
        {
            "$lookup": {
                "from": "Story",
                "let": {"likedStories": "$likedStories", 'writerName': '$name'},
                "pipeline": [
                    {"$match": {"$expr": {"$in": [{"$toString": "$_id"}, "$$likedStories"]}}},
                    {
                        "$project": {
                            "_id": 0,
                            "storyId": {"$toString": "$_id"},
                            "writerName": "$$writerName",
                            "title": 1,
                            "slug": 1,
                            "storyCover": 1,
                            "categories": 1,
                            "description": 1,
                        }
                    }
                ],
                "as": "likedStoriesList"
            }
        },
        {
            "$project": {
                "_id": 0,
            }
        }
    ], collation={'locale': 'en', 'strength': 2}))
    if len(user) == 0:
        raise HTTPException(status_code=400, detail="The user does not exist")

    profile = user[0]
    profile['createdAt'] = str(profile['createdAt'])
    profile['followingCount'] = len(profile['followingList'])
    profile['followersCount'] = len(profile['followersList'])

    for story_list in profile['storyLists']:
        if len(story_list['listStoryIds']) > 0:
            list_stories = list(db.stories.aggregate([
                {"$match": {"$expr": {"$in": [{"$toString": "$_id"}, story_list['listStoryIds']]}}},
                {
                    "$project": {
                        "_id": 0,
                        "storyId": {"$toString": "$_id"},
                        "numPages": {"$size": "$content"},
                        "title": 1,
                        "slug": 1,
                        "storyCover": 1,
                        "categories": 1,
                        "description": 1,
                    }
                }
            ]))
            story_list['listStories'] = list_stories
        else:
            story_list['listStories'] = []

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    return JSONResponse(content=profile, headers=headers)


@router.put("/update_user_profile", description="Use to update the user profile", status_code=200)
async def update_user_profile(update_user_model: UpdateUser, background_tasks: BackgroundTasks):
    background_tasks.add_task(update_user, update_user_model)
    return {"message": "The user has been updated successfully"}


@router.put("/update_user_coins", description="Use to update the user coins", status_code=200)
async def user_coins(update_coins: UpdateCoins, background_tasks: BackgroundTasks):
    background_tasks.add_task(update_user_coins, update_coins)
    return {"message": "The user's coins has been updated successfully"}


@router.put("/redeem_referral_code", description="Use to redeem code the referral code", status_code=200)
async def redeem_referral_code(referral: Referral):
    referral_code_owner = db.users.find_one({'referralCode': referral.referralCode, 'uid': {'$ne': referral.uid}})
    if referral_code_owner is None:
        raise HTTPException(status_code=400, detail="Incorrect referral code")

    user = db.users.find_one({"uid": referral.uid}, {"referredBy": 1})
    if user['referredBy'] is None:
        db.users.update_one({"uid": referral.uid},
                            {"$inc": {"coins": 20}, "$set": {"referredBy": referral.referralCode}})
        db.users.update_one({"referralCode": referral.referralCode}, {"$inc": {"coins": 20}})

        send_notification(title="لقد ربحت 20 عملة", text="لقد ربحت 20 عملة من خلال رمز الدعوة الخاص بك",
                          target_fcm=referral_code_owner['FCM'], image='https://a.top4top.io/p_22286og1w1.jpeg',
                          link=None, target_uid=referral_code_owner['uid'], notif_type="Coins", sender_uid=None)
    else:
        raise HTTPException(status_code=400, detail="The user has already redeemed a referral code")


@router.get("/get_follow_list/{username}", description="Use to get the user follow list", status_code=200)
@cache_one_minute()
async def get_follow_list(username: str, type: str = "followersList"):
    user = list(db.users.aggregate([
        {"$match": {'username': username}},
        {
            "$lookup": {
                "from": "User",
                "let": {"list": f"${type}"},
                "pipeline": [
                    {"$match": {"$expr": {"$in": ["$uid", "$$list"]}}},
                    {
                        "$project": {
                            "_id": 0,
                            "uid": 1,
                            "name": 1,
                            "username": 1,
                            "bio": 1,
                            "profileImage": 1,
                            "followersList": 1,
                        }
                    }
                ],
                "as": "followInfo"
            }
        },
    ], collation={'locale': 'en', 'strength': 2}))
    if len(user) == 0:
        raise HTTPException(status_code=400, detail="The user does not exist")

    user_obj = user[0]
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    return JSONResponse(content=user_obj['followInfo'], headers=headers)


@router.put("/follow", description="Use to follow a user", status_code=201)
def follow_user(follow: Follow, res: Response):
    initiator_profile = db.users.find_one({"uid": follow.initiatorId},
                                          {"_id": 0, "name": 1, "username": 1, "profileImage": 1, "followingList": 1})
    if initiator_profile:
        to_be_followed_profile = db.users.find_one({"uid": follow.toBeFollowedId},
                                                   {"_id": 0, "name": 1, "username": 1, "FCM": 1})
        if follow.toBeFollowedId in initiator_profile['followingList']:
            response = {
                "message": initiator_profile['username'] + '  is already  following ' +
                           to_be_followed_profile['username'],
                "messageAr": initiator_profile['username'] + '  يتابع بالفعل ' +
                             to_be_followed_profile['username']

            }
            res.status_code = status.HTTP_400_BAD_REQUEST
            return response

        # following a user if he is not already followed
        db.users.update_one(
            {"uid": follow.initiatorId},
            {"$addToSet": {"followingList": follow.toBeFollowedId}}
        )

        db.users.update_one(
            {"uid": follow.toBeFollowedId},
            {"$addToSet": {"followersList": follow.initiatorId}}
        )

        initiator_name = initiator_profile['name']
        to_be_followed_name = to_be_followed_profile['name']

        log_obj = {
            'text': f'User with name {initiator_name} followed {to_be_followed_name}',
            'createdAt': str(datetime.datetime.utcnow()),
            'source': 'follow'
        }

        target_user = to_be_followed_profile
        if initiator_profile is not None:
            title = initiator_name
            text = f"قام {initiator_profile['username']}  بمتابعتك"
            image = initiator_profile['profileImage']
            link = f"/user/{target_user['username']}"
            target_uid = follow.toBeFollowedId
            sender_uid = follow.initiatorId
            notif_type = 'follow'
            target_fcm = None
            if 'FCM' in target_user:
                target_fcm = target_user['FCM']
            send_notification(title, text, image, link,
                              notif_type, target_uid, sender_uid, target_fcm)

        db.logs.insert_one(log_obj)


@router.delete("/unfollow/{initiator_id}/{to_be_unfollowed_id}", description="Use to unfollow a user", status_code=200)
async def unfollow_user(initiator_id: str, to_be_unfollowed_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(unfollow, initiator_id, to_be_unfollowed_id)
    return {"message": "The user has been unfollowed successfully"}


@router.put("/block", description="Use to block a user", status_code=201)
async def block_user(block_obj: Block, background_tasks: BackgroundTasks):
    background_tasks.add_task(block, block_obj)
    return {"message": "The user has been blocked successfully"}


@router.delete("/unblock/{initiator_id}/{to_be_unblocked_id}", description="Use to unblock a user", status_code=200)
async def unblock_user(initiator_id: str, to_be_unblocked_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(unblock, initiator_id, to_be_unblocked_id)
    return {"message": "The user has been unblocked successfully"}


@router.post("/add_subscription_info", description="Use to add subscription to a user", status_code=200)
async def add_subscription(subscription_info: SubscriptionInfo, background_tasks: BackgroundTasks):
    background_tasks.add_task(subscribe_user, subscription_info)
    return {"message": "The user's subscription info has been added successfully"}


@router.get("/check_user_subscription/{uid}", description="Use to check if a user subscription is valid",
            status_code=200)
async def check_valid_subscription(uid: str):
    user = db.users.find_one({'uid': uid})
    subscription_status = 'valid'
    if user['subscriptionExpiry'] is not None:
        current_date = datetime.datetime.utcnow()
        delta = datetime.datetime.strptime(
            user['subscriptionExpiry'], '%Y-%m-%d') - current_date
        if delta <= datetime.timedelta(0):
            subscription_status = 'expired'

    return {'subscriptionTier': user['subscriptionTier'], 'status': subscription_status}


@router.get("/get_user_story_lists/{initiator_id}", description="Use to get a user's story lists",
            status_code=200)
async def get_user_story_lists(initiator_id: str):
    result = list(db.users.find({'uid': initiator_id}, {'storyLists': 1}).collation(
        {'locale': 'en', 'strength': 2}))
    if len(result) == 0:
        raise HTTPException(status_code=400, detail="The user does not exist")

    story_lists = result[0]['storyLists']
    for story_list in story_lists:
        if len(story_list['listStoryIds']) > 0:
            list_stories = list(db.stories.aggregate([
                {"$match": {"$expr": {"$in": [{"$toString": "$_id"}, story_list['listStoryIds']]}}},
                {
                    "$project": {
                        "_id": 0,
                        "storyId": {"$toString": "$_id"},
                        "numPages": {"$size": "$content"},
                        "title": 1,
                        "slug": 1,
                        "storyCover": 1,
                        "categories": 1,
                        "description": 1,
                    }
                }
            ]))
            story_list['listStories'] = list_stories
        else:
            story_list['listStories'] = []

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    return JSONResponse(content=story_lists, headers=headers)


@router.put("/add_user_story_list", description="Use to create a new user's story list", status_code=201)
async def add_user_story_list(new_list: UserStoriesList, background_tasks: BackgroundTasks):
    background_tasks.add_task(new_stories_list, new_list)
    return {"message": "The story list has been created successfully"}


@router.post("/add_story_to_list", description="Use to add a story to a user's story list", status_code=200)
async def add_story_to_list(list_item: UserStoriesListItem, background_tasks: BackgroundTasks):
    background_tasks.add_task(add_story_to_the_list, list_item)
    return {"message": "The story has been added to the list successfully"}


@router.delete("/remove_story_from_list/{initiator_id}/{list_id}/{story_id}",
               description="Use to remove a story from a user's story list", status_code=200)
async def remove_story_from_list(initiator_id: str, list_id: str, story_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(remove_story_from_the_list, initiator_id, list_id, story_id)
    return {"message": "The story has been removed from the list successfully"}


@router.post("/update_user_story_list", description="Use to update a story list", status_code=200)
async def update_user_story_list(story_list: UserStoriesList, background_tasks: BackgroundTasks):
    background_tasks.add_task(update_story_list, story_list)
    return {"message": "The list has been updated successfully"}


@router.delete("/delete_story_list/{initiator_id}/{list_id}",
               description="Use to delete a story list", status_code=200)
async def delete_story_list(initiator_id: str, list_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(delete_list, initiator_id, list_id)
    return {"message": "The list has been deleted successfully"}


def create_user(user: User):
    referral_code = uuid.uuid4().hex[:12].upper()

    # ensure unique referral codes
    while True:
        if db.users.count_documents({"referralCode": referral_code}) == 0:
            break
        else:
            referral_code = uuid.uuid4().hex[:12].upper()

    user_dict = user.dict()
    user_dict['bio'] = ''
    user_dict['sex'] = 'undetermined'
    user_dict['coins'] = 0
    user_dict['referralCode'] = referral_code
    user_dict['paidChapters'] = {}
    user_dict['personalLink'] = ''
    user_dict['followersList'] = []
    user_dict['followingList'] = []
    user_dict['blockedUserList'] = []
    user_dict['createdAt'] = str(datetime.datetime.utcnow())
    user_dict['subscriptionTier'] = 'normal'
    user_dict['subscriptionExpiry'] = None
    user_dict['status'] = 'active'
    user_dict['readStories'] = []
    user_dict['likedStories'] = []
    user_dict['userStoryIds'] = []
    user_dict['storyLists'] = [
        {
            "listId": str(ObjectId()),
            "title": 'اقرأ لاحقا',
            "listStoryIds": [],
            "status": "private",
        }
    ]

    db.users.insert_one(user_dict)

    log_obj = {
        'text': f'New User Created!!! ({user.username} ) with email ({user.email})',
        'createdAt': str(datetime.datetime.utcnow()),
        'source': 'users'
    }
    db.logs.insert_one(log_obj)


def update_user(update_obj: UpdateUser):
    update_dict = update_obj.dict()
    filtered = {k: v for k, v in update_dict.items() if v is not None}
    update_dict.clear()
    update_dict.update(filtered)

    db.users.update_one(
        {'uid': update_obj.uid},
        {'$set': update_dict}
    )


def update_user_coins(update_coins: UpdateCoins):
    if update_coins.operation == "remove":
        db.users.update_one({"uid": update_coins.uid}, {"$inc": {"coins": -1 * update_coins.amount}})
    else:
        db.users.update_one({"uid": update_coins.uid}, {"$inc": {"coins": update_coins.amount}})


def block(block_obj: Block):
    db.users.update_one(
        {"uid": block_obj.initiatorId},
        {
            "$pull": {"followingList": block_obj.toBeBlockedId},
            "$addToSet": {"blockedUserList": block_obj.toBeBlockedId}
        }
    )


def unblock(initiator_id: str, to_be_unblocked_id: str):
    db.users.update_one(
        {"uid": initiator_id},
        {
            "$pull": {"blockedUserList": to_be_unblocked_id}
        }
    )


def unfollow(initiator_id: str, to_be_unfollowed_id: str):
    db.users.update_one(
        {"uid": initiator_id},
        {"$pull": {"followingList": to_be_unfollowed_id}}
    )

    db.users.update_one(
        {"uid": to_be_unfollowed_id},
        {"$pull": {"followersList": initiator_id}}
    )

    initiator_name = db.users.find_one({"uid": initiator_id}, {"_id": 0, "name": 1})['name']
    to_be_followed_name = db.users.find_one({"uid": to_be_unfollowed_id}, {"_id": 0, "name": 1})['name']
    log_obj = {
        'text': f'User with id {initiator_name} unfollowed {to_be_followed_name}',
        'createdAt': str(datetime.datetime.utcnow()),
        'source': 'follow'
    }
    db.logs.insert_one(log_obj)


def subscribe_user(subscription_info: SubscriptionInfo):
    db.users.update_one({'uid': subscription_info.uid},
                        {"$set": {'subscriptionTier': subscription_info.subscriptionTier,
                                  'subscriptionExpiry': subscription_info.subscriptionExpiry
                                  }
                         }
                        )
    target_user = db.users.find_one({"uid": subscription_info.uid}, {"_id": 0, "FCM": 1})
    title = "تم تفعيل الاشتراك الذهبي!😍"
    text = f"ينتهي الاشتراك في: {subscription_info.subscriptionExpiry}"
    link = ""
    image = ""
    target_uid = subscription_info.uid
    sender_uid = ''
    notif_type = 'subscription'
    if 'FCM' in target_user:
        target_fcm = target_user['FCM']
        send_notification(title, text, image, link,
                          notif_type, target_uid, sender_uid, target_fcm)

    log_obj = {
        'text': f'{target_user["username"]} just subscribed 🤑💰 until {subscription_info.subscriptionExpiry}',
        'createdAt': str(datetime.datetime.utcnow()),
        'source': 'subscription'
    }

    notify_admin(log_obj['text'])

    db.logs.insert_one(log_obj)


def new_stories_list(new_list: UserStoriesList):
    list_dict = new_list.dict()
    list_dict['listId'] = str(ObjectId())
    list_dict['listStoryIds'] = []

    user = db.users.find_one({"uid": new_list.initiatorId}, {'storyLists': 1})
    target_list = next((x for x in user['storyLists'] if x['title'] == new_list.title), None)
    if target_list is not None:
        raise HTTPException(status_code=400, detail="The list already exists")

    db.users.update_one(
        {"uid": new_list.initiatorId},
        {"$push": {"storyLists": list_dict}}
    )

    log_obj = {
        'text': f'Some user created a new story list ({new_list.title})',
        'createdAt': str(datetime.datetime.utcnow()),
        'source': 'userLists'
    }
    db.logs.insert_one(log_obj)


def add_story_to_the_list(list_item: UserStoriesListItem):
    db.users.update_one({"uid": list_item.initiatorId, "storyLists.listId": list_item.listId},
                        {"$addToSet": {"storyLists.$.listStoryIds": list_item.storyId}})


def remove_story_from_the_list(initiator_id: str, list_id: str, story_id: str):
    db.users.update_one(
        {"uid": initiator_id, "storyLists.listId": list_id},
        {"$pull": {"storyLists.$.listStoryIds": story_id}}
    )


def update_story_list(story_list: UserStoriesList):
    db.users.update_one(
        {"uid": story_list.initiatorId, "storyLists.listId": story_list.listId},
        {"$set": {"storyLists.$.title": story_list.title, "storyLists.$.status": story_list.status}}
    )


def delete_list(initiator_id: str, list_id: str):
    db.users.update_one(
        {"uid": initiator_id},
        {"$pull": {"storyLists": {"listId": list_id}}}
    )

import pymongo
from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse

from db import db
from src.Dashboard.schemas import AdminUpdateStory
from src.Story.schemas import StoryID
from src.utils import project_story_field
from src.utils import send_notification

router = APIRouter(tags=['Dashboard'])


@router.get("/get_dashboard_data", description="Use to get the dashboard stats and numbers", status_code=200)
async def get_dashboard_data():
    number_of_users = db.users.count_documents({})
    number_of_stories = db.stories.count_documents({'status': 'published'})
    number_of_comments = db.comments.count_documents({})
    number_of_shorts = db.shorts.count_documents({})
    number_of_views = list(db.stories.aggregate([{'$group': {'_id': None, 'sum': {'$sum': "$views"}}}]))[0]['sum']

    return {'numberOfUsers': number_of_users, 'numberOfStories': number_of_stories,
            'numberOfComments': number_of_comments, 'numberOfViews': number_of_views,
            'numberOfShorts': number_of_shorts}


@router.get("/get_logs", description="Use to get the server logs", status_code=200)
async def get_logs(nextPage: str = None):
    query = {}
    project_obj = {
        "_id": 0,
        "logId": {"$toString": "$_id"},
        "text": 1,
        "source": 1,
        "createdAt": 1
    }
    if nextPage is not None:
        query['_id'] = {'$lt': ObjectId(nextPage)}

    logs = list(db.logs.find(query, project_obj).sort('createdAt', pymongo.DESCENDING).limit(100))
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    return JSONResponse(content=logs, headers=headers)


@router.put("/admin_update_story_status", description="Use to update story status as an admin", status_code=200)
async def update_story_status(admin_update_story: AdminUpdateStory, background_tasks: BackgroundTasks):
    background_tasks.add_task(update_status, admin_update_story)
    return {"message": "The story has been updated successfully"}


@router.post("/increase_rank", description="Use to increase a story' rank", status_code=200)
async def increase_story_rank(story_id: StoryID, background_tasks: BackgroundTasks):
    background_tasks.add_task(increase_rank, story_id)
    return {"message": "The story's rank has been increased successfully"}


@router.delete("/decrease_rank/{story_id}", description="Use to decrease a story' rank", status_code=200)
async def decrease_story_rank(story_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(decrease_rank, story_id)
    return {"message": "The story's rank has been decreased successfully"}


@router.get("/get_all_stories", description="Get all pending stories", status_code=200)
async def get_pending_stories():
    pending_stories = list(db.stories.aggregate([
        {"$match": {'status': 'pending'}},
        {
            "$lookup": {
                "from": "User",
                "let": {"writerId": "$writerId"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$uid", "$$writerId"]}}},
                    {"$project": {"_id": 0, "uid": 1, "name": 1}},
                ],
                "as": "writer"
            },
        },
        {"$unwind": "$writer"},
        project_story_field,
    ]))
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    return JSONResponse(content=pending_stories, headers=headers)


def update_status(admin_update_story: AdminUpdateStory):
    db.stories.update_one(
        {'_id': ObjectId(admin_update_story.storyId)},
        {'$set': {"status": admin_update_story.status, "adminMessage": admin_update_story.adminMessage}}
    )

    story = db.stories.find_one({"_id": ObjectId(admin_update_story.storyId)},
                                {'_id': 0, 'title': 1, 'storyCover': 1, 'slug': 1, 'description': 1, 'writerId': 1})
    title = story['title']
    image = story['storyCover']
    link = f"/story/{story['slug']}"
    sender_uid = ''
    notif_type = 'story'
    if admin_update_story.status == "published" and admin_update_story.notify:
        target_uid = ''
        text = f"قصة جديدة: {story['description']}"
        target_fcm = '/topics/all'
        send_notification(title, text, image, link,
                          notif_type, target_uid, sender_uid, target_fcm)

    if admin_update_story.status == "rejected":
        writer = db.users.find_one({'uid': story['writerId']}, {'FCM': 1})
        target_uid = story['writerId']
        target_fcm = writer['FCM'] if 'FCM' in writer else ''
        text = f"تم رفض قصتك بسبب: {admin_update_story.adminMessage}"
        send_notification(title, text, image, link,
                          notif_type, target_uid, sender_uid, target_fcm)


def increase_rank(story_id: StoryID):
    db.stories.update_one(
        {'_id': ObjectId(story_id.storyId)},
        {'$inc': {'rank': 1}}
    )


def decrease_rank(story_id: str):
    db.stories.update_one(
        {'_id': ObjectId(story_id)},
        {'$inc': {'rank': -1}}
    )

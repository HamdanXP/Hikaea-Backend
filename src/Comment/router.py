from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks

from db import db
from src.Comment.schemas import Comment
from src.utils import send_notification

router = APIRouter(tags=['Comments'])


@router.post("/add_new_comment", description="Use to add a new comment to a story", status_code=201)
async def add_new_comment(new_comment: Comment, background_tasks: BackgroundTasks):
    background_tasks.add_task(create_new_comment, new_comment)
    return {"message": "The comment has been added successfully"}


@router.delete("/delete_comment/{comment_id}", description="Use to delete a story's comment", status_code=200)
async def delete_comment(comment_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(delete_a_comment, comment_id)
    return {"message": "The comment has been deleted successfully"}


@router.get("/get_story_comments/{story_id}", description="Use to get all the story's comments", status_code=200)
async def get_story_comments(story_id: str):
    comments = list(db.comments.aggregate([
        {"$match": {"storyId": story_id}},
        {
            "$lookup": {
                "from": "User",
                "let": {"commenterId": "$commenterId"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$uid", "$$commenterId"]}}},
                    {"$project": {"_id": 0, "name": 1, "username": 1, "profileImage": 1}},
                ],
                "as": "User"
            },
        },
        {"$unwind": "$User"},
        {
            "$project":
                {
                    "_id": 0,
                    "commentId": {"$toString": "$_id"},
                    "username": "$User.username",
                    "name": "$User.name",
                    "profileImage": "$User.profileImage",
                    "commenterId": 1,
                    "storyId": 1,
                    "isWriter": 1,
                    "comment": 1,
                    "status": 1,
                    "createdAt": 1,
                }
        },
    ]))
    return comments


def create_new_comment(new_comment: Comment):
    story = db.stories.find_one(
        {'_id': ObjectId(new_comment.storyId)}, {'_id': 0, 'writerId': 1, 'title': 1, 'slug': 1})
    commenter_profile = db.users.find_one({"uid": new_comment.commenterId},
                                          {'_id': 0, 'name': 1, 'username': 1, 'profileImage': 1})

    writer_id = story['writerId']
    story_name = story['title']
    commenter_name = commenter_profile['name']

    comment_dict = new_comment.dict()
    comment_dict['isWriter'] = writer_id == new_comment.commenterId
    comment_dict['status'] = 'published'
    comment_dict['createdAt'] = str(datetime.utcnow())
    db.comments.insert_one(comment_dict)

    log_obj = {
        'text': f'User ({commenter_name}) commented on story ({story_name}) with text ({new_comment.comment})',
        'createdAt': str(datetime.utcnow()),
        'source': 'comments'
    }
    db.logs.insert_one(log_obj)

    title = story_name
    link = f"/story/{story['slug']}"
    sender_uid = new_comment.commenterId
    notif_type = 'comment'
    image = commenter_profile['profileImage']

    if new_comment.commenterId != writer_id:
        text = f"قام {commenter_profile['username']} بالتعليق على قصتك"
        writer_profile = db.users.find_one({"uid": writer_id}, {'_id': 0, 'FCM': 1})
        target_uid = writer_id
        target_fcm = None
        if 'FCM' in writer_profile:
            target_fcm = writer_profile['FCM']
        send_notification(title, text, image, link, notif_type, target_uid, sender_uid, target_fcm)

    if new_comment.replyToId is not None and new_comment.replyToId != writer_id:
        text = f"قام {commenter_profile['username']} بالرد على تعليقك"
        replied_to_profile = db.users.find_one({"uid": new_comment.replyToId}, {'_id': 0, 'FCM': 1})
        target_uid = new_comment.replyToId
        target_fcm = None
        if 'FCM' in replied_to_profile:
            target_fcm = replied_to_profile['FCM']
        send_notification(title, text, image, link, notif_type, target_uid, sender_uid, target_fcm)


def delete_a_comment(comment_id: str):
    db.comments.update_one(
        {'_id': ObjectId(comment_id)},
        {"$set": {'status': 'deleted'}}
    )

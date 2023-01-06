import datetime

import pymongo
from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse

from db import db
from src.Short.schemas import Short, ShortComment, ShortCommentVote, ShortVote
from src.utils import send_notification

router = APIRouter(tags=['Shorts'])


@router.post("/add_short", description="Use to create a new short", status_code=201)
async def add_short(short: Short, background_tasks: BackgroundTasks):
    background_tasks.add_task(create_new_short, short)
    return {"message": "The short has been created successfully"}


@router.get("/get_shorts", description="Use to get all the shorts", status_code=200)
async def get_shorts(limit: int = 6, sort: str = "new", next_page: str = None):
    sort_obj = [('createdAt', pymongo.DESCENDING)]
    find_obj = {}

    sort_obj.insert(0, ('votes', pymongo.DESCENDING))
    sort_correct = True
    if sort == 'top_today':
        find_obj['createdAt'] = {
            "$gte": datetime.datetime.utcnow().strftime("%Y-%m-%d")}
    elif sort == "top_week":
        find_obj['createdAt'] = {
            "$gte": (datetime.datetime.utcnow() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")}
    elif sort == "top_month":
        find_obj['createdAt'] = {
            "$gte": (datetime.datetime.utcnow() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")}
    elif sort != "top_all_time":
        sort_obj.pop(0)
        sort_correct = False

    if next_page is not None:
        if sort_correct:
            cursor = db.shorts.find_one(
                {'_id': ObjectId(next_page)})
            find_obj['$expr'] = {
                '$cond': {
                    'if': {'$eq': ["$votes", cursor['votes']]},
                    'then': {'$lt': ['$_id', ObjectId(next_page)]},
                    'else': {'$lt': ["$votes", cursor['votes']]}
                }
            }
        else:
            find_obj['_id'] = {'$lt': ObjectId(next_page)}

    shorts = list(
        db.shorts
        .find(find_obj, {
            "_id": 0,
            "shortId": {"$toString": "$_id"},
            'text': 1,
            'createdAt': 1,
            'type': 1,
            'isAnon': 1,
            'writerId': 1,
            'tiktokId': 1,
            'isHidden': 1,
            'commentsCount': {"$size": "$comments"},
            'votes': 1
        })
        .sort(sort_obj)
        .limit(limit))
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    return JSONResponse(content=shorts, headers=headers)


@router.get("/get_short/{short_id}", description="Use to get a single short", status_code=200)
async def get_short(short_id: str):
    short = db.shorts.find_one({"_id": ObjectId(short_id)},
                               {
                                   "_id": 0,
                                   "shortId": {"$toString": "$_id"},
                                   'text': 1,
                                   'createdAt': 1,
                                   'type': 1,
                                   'isAnon': 1,
                                   'writerId': 1,
                                   'tiktokId': 1,
                                   'isHidden': 1,
                                   "comments": {
                                       "$map": {"input": "$comments", "in": {
                                           "$mergeObjects": ["$$this",
                                                             {"commentId": {"$toString": "$$this.commentId"}}]}}
                                   },
                                   'commentsCount': {"$size": "$comments"},
                                   'votes': 1
                               }
                               )

    if 'comments' in short:
        short['comments'].sort(key=lambda x: x['votes'], reverse=True)
    else:
        short['comments'] = []

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    return JSONResponse(content=short, headers=headers)


@router.get("/get_matched_shorts/{search_text}/{search_date}", description="Use to search the shorts",
            status_code=200)
async def get_matched_shorts(search_text: str, search_date: str):
    shorts = list(
        db.shorts
        .find(

            {'$and': [{'text': {'$regex': search_text}}, {'createdAt': {'$lt': search_date}}]},
            {
                "_id": 0,
                "shortId": {"$toString": "$_id"},
                'text': 1,
                'createdAt': 1,
                'type': 1,
                'isAnon': 1,
                'writerId': 1,
                'tiktokId': 1,
                'isHidden': 1,
                'commentsCount': {"$size": "$comments"},
                'votes': 1
            }
        )
        .sort('createdAt', pymongo.DESCENDING)
    )
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    return JSONResponse(content=shorts, headers=headers)


@router.post("/add_short_comment", description="Use to add a new short comment", status_code=201)
async def add_new_short_comment(short_comment: ShortComment, background_tasks: BackgroundTasks):
    background_tasks.add_task(add_new_comment, short_comment)
    return {"message": "The short's comment has been added successfully"}


@router.put("/upvote_short", description="Use to upvote a short", status_code=200)
async def short_upvote(short_vote: ShortVote, background_tasks: BackgroundTasks):
    background_tasks.add_task(upvote_short, short_vote)
    return {"message": "The short has been upvote successfully"}


@router.delete("/down_vote_short/{short_id}", description="Use to downvote a short",
               status_code=200)
async def short_downvote(short_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(downvote_short, short_id)
    return {"message": "The short has been down vote successfully"}


@router.put("/upvote_short_comment", description="Use to upvote a short comment", status_code=200)
async def upvote_short_comment(short_comment_vote: ShortCommentVote, background_tasks: BackgroundTasks):
    background_tasks.add_task(upvote_comment, short_comment_vote)
    return {"message": "The short's comment has been upvote successfully"}


@router.delete("/down_vote_short_comment/{short_id}/{comment_id}", description="Use to downvote a short comment",
               status_code=200)
async def downvote_short_comment(short_id: str, comment_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(downvote_comment, short_id, comment_id)
    return {"message": "The short's comment has been down vote successfully"}


def create_new_short(short: Short):
    short_dict = short.dict()
    short_dict['isHidden'] = False
    short_dict['votes'] = 0
    short_dict['comments'] = []
    short_dict['createdAt'] = str(datetime.datetime.utcnow())
    db.shorts.insert_one(short_dict)

    log_obj = {
        'text': f'Short Added with type {short.type} by tiktok ID: {short.type}',
        'createdAt': str(datetime.datetime.utcnow()),
        'source': 'shorts'
    }
    db.logs.insert_one(log_obj)


def add_new_comment(short_comment: ShortComment):
    short_id = ObjectId(short_comment.shortId)
    comment_obj = {
        'commentId': ObjectId(),
        'votes': 0,
        'comment': short_comment.comment,
        'status': 'published',
        'createdAt': str(datetime.datetime.utcnow()),
    }

    db.shorts.update_one(
        {'_id': short_id}, {"$addToSet": {"comments": comment_obj}})

    target_short = db.shorts.find_one({'_id': short_id}, {'FCM': 1})
    if 'FCM' in target_short:
        title = "تعليق على مشاركتك القصيرة"
        text = "قام شخص بالتعليق على مشاركتك القصيرة"
        image = None
        link = f"/shorts/{short_id}"
        target_uid = None
        sender_uid = None
        notif_type = 'comment'
        target_fcm = target_short['FCM']
        send_notification(title, text, image, link,
                          notif_type, target_uid, sender_uid, target_fcm)


def upvote_short(short_vote: ShortVote):
    db.shorts.update_one({'_id': ObjectId(short_vote.shortId)},
                         {'$inc': {'votes': 1}})


def downvote_short(short_id: str):
    db.shorts.update_one({'_id': ObjectId(short_id)},
                         {'$inc': {'votes': -1}})


def upvote_comment(short_comment_vote: ShortCommentVote):
    db.shorts.update_one(
        {'_id': ObjectId(short_comment_vote.shortId), 'comments.commentId': ObjectId(short_comment_vote.commentId)},
        {'$inc': {'comments.$.votes': 1}})


def downvote_comment(short_id: str, comment_id: str):
    db.shorts.update_one({'_id': ObjectId(short_id), 'comments.commentId': ObjectId(comment_id)},
                         {'$inc': {'comments.$.votes': -1}})

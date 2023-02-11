import datetime
import json

import pymongo
from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from fastapi_redis_cache import cache_one_minute, cache_one_hour
from slugify import slugify

from db import db
from src.Story.schemas import Story, StoriesQuery, UpdateStory, StoryID, StoryReader, StoryLiker, BuyChapter
from src.utils import story_comments, story_writer, send_notification, project_full_story, notify_admin

router = APIRouter(tags=['Story'])


@router.post("/add_story", description="Use to create a new story", status_code=201)
async def add_story(story: Story, background_tasks: BackgroundTasks):
    background_tasks.add_task(create_story, story)
    return {"message": "The story has been created successfully"}


@router.get("/get_story/{slug}", description="Use to get a story by its slug", status_code=200)
@cache_one_minute()
async def get_story(slug: str):
    story = list(db.stories.aggregate([
        {"$match": {'slug': slug}},
        story_writer,
        {"$unwind": "$writer"},
        story_comments,
    ]))

    if len(story) == 0:
        raise HTTPException(status_code=400, detail="The story does not exist")

    story_obj = story[0]
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    return JSONResponse(content=get_single_story_obj(story_obj), headers=headers)


@router.post("/get_all_stories", description="Use to get all the stories", status_code=200)
async def get_all_stories(storiesQuery: StoriesQuery, limit: int = 12, include_chat: bool = False):
    if storiesQuery.sortWay == 'top':
        sort_key = 'views'
    elif storiesQuery.sortWay == 'trending':
        sort_key = f'dailyViews.{str(datetime.date.today())}'
    else:
        sort_key = 'createdAt'

    query_list = [{'status': 'published'}]
    # get all stories the have one or more of requested categories
    categories_filters = []
    for category in storiesQuery.categories:
        categories_filters.append({'categories': category})

    if len(categories_filters) != 0:
        query_list.append({'$and': categories_filters})

    if not include_chat:
        query_list.append({'type': {'$ne': 'chat'}})

    if storiesQuery.nextPage is not None:
        find_obj = {}
        cursor = db.stories.find_one(
            {'_id': ObjectId(storiesQuery.nextPage)}, {'_id': 0, 'rank': 1})

        find_obj['$expr'] = {
            '$cond': {
                'if': {'$eq': ["$rank", 0 if 'rank' not in cursor else cursor['rank']]},
                'then': {'$lt': ['$_id', ObjectId(storiesQuery.nextPage)]},
                'else': {'$lt': ["$rank", 0 if 'rank' not in cursor else cursor['rank']]}
            }
        }

        query_list.insert(0, find_obj)

    stories = list(db.stories.aggregate([
        {"$match": {'$and': query_list}},
        story_writer,
        {"$unwind": "$writer"},
        story_comments,
        {
            "$sort": {
                'rank': pymongo.DESCENDING,
                sort_key: pymongo.DESCENDING
            }
        },
        {"$limit": limit} if limit > 0 else {
            "$addFields": {}
        },
        {
            "$addFields": {"emptyArray": []}
        },
        project_full_story
    ]))

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    return JSONResponse(content=stories, headers=headers)


@router.delete("/story_id/{initiator_id}/{story_id}", description="Use to delete a user's story", status_code=200)
async def delete_story(initiator_id: str, story_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(mark_story_as_deleted, initiator_id, story_id)
    return {"message": "The story has been deleted successfully"}


@router.put("/update_story", description="Use to update a single story", status_code=200)
async def update_story(update_obj: UpdateStory, background_tasks: BackgroundTasks):
    background_tasks.add_task(update_story_fields, update_obj)
    return {"message": "The story has been updated successfully"}


@router.get("/get_matched_stories/{search_text}", description="Use to search the stories by the title", status_code=200)
@cache_one_hour()
async def search_stories(search_text: str):
    if len(search_text) < 3:
        return []
    stories = list(db.stories.aggregate([
        {"$match": {'title': {'$regex': search_text}, 'status': 'published'}},
        story_writer,
        {"$unwind": "$writer"},
        story_comments,
        {
            "$addFields": {"emptyArray": []}
        },
        project_full_story
    ]))
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    return JSONResponse(content=stories, headers=headers)


@router.get("/get_random_story", description="Use to get a random story", response_model=Story, status_code=200)
async def get_random_story():
    story = list(db.stories.aggregate([
        {'$match': {'status': 'published'}}, {'$sample': {'size': 1}},
        story_writer,
        {"$unwind": "$writer"},
        story_comments,
    ]))[0]
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    return JSONResponse(content=get_single_story_obj(story), headers=headers)


@router.put("/add_story_view", description="Use to add a story view", status_code=200)
async def add_story_view(storyId: StoryID, background_tasks: BackgroundTasks):
    background_tasks.add_task(add_view, storyId)
    return {"message": "The story's view has been added successfully"}


@router.delete("/remove_story_view/{story_id}", description="Use to remove a story view", status_code=200)
async def delete_story_view(story_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(remove_view, story_id)
    return {"message": "The story's view has been removed successfully"}


@router.put("/add_story_reader", description="Use to add a story reader", status_code=200)
async def add_story_reader(story_reader: StoryReader, background_tasks: BackgroundTasks):
    background_tasks.add_task(add_reader, story_reader)
    return {"message": "The story's reader has been added successfully"}


@router.put("/add_story_liker", description="Use to add a story liker", status_code=200)
async def add_story_liker(story_liker: StoryLiker, background_tasks: BackgroundTasks):
    background_tasks.add_task(add_liker, story_liker)
    return {"message": "The story's liker has been added successfully"}


@router.delete("/delete_story_liker/{liker_id}/{story_id}", description="Use to delete a story liker", status_code=200)
async def delete_story_liker(liker_id: str, story_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(remove_liker, liker_id, story_id)
    return {"message": "The story's liker has been removed successfully"}


@router.post("/buy_story_chapter", description="Use to buy a story's chapter", status_code=200)
async def buy_story_chapter(info: BuyChapter, background_tasks: BackgroundTasks):
    background_tasks.add_task(buy_chapter, info)
    return {"message": "The story's chapter has been bought successfully"}


@router.get("/get_user_stories/{writer_id}", description="Use to get all the stories related to a writer",
            status_code=200)
async def get_user_stories(writer_id: str):
    stories = list(db.stories.aggregate([
        {"$match": {'$and': [{'writerId': writer_id}, {'status': {'$ne': 'deleted'}}]}},
        story_writer,
        {"$unwind": "$writer"},
        story_comments,
        {
            "$addFields": {"emptyArray": []}
        },
        project_full_story
    ]))
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    return JSONResponse(content=stories, headers=headers)


@router.get("/get_list_stories/{creator}/{list_id}", description="Use to get a list's stories",
            status_code=200)
async def get_user_stories(creator: str, list_id: str):
    result = list(db.users.find({'username': creator}, {'storyLists': 1}).collation(
        {'locale': 'en', 'strength': 2}))
    if len(result) == 0:
        raise HTTPException(status_code=400, detail="The user does not exist")

    story_lists = result[0]['storyLists']

    target_list = next((x for x in story_lists if x['listId'] == list_id), None)

    if target_list is None:
        raise HTTPException(status_code=400, detail="The list does not exist")

    if len(target_list['listStoryIds']) == 0:
        return []
    else:
        list_stories = list(db.stories.aggregate([
            {"$match": {"$expr": {"$in": [{"$toString": "$_id"}, target_list['listStoryIds']]}}},
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
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json; charset=UTF-8'
        }
        return JSONResponse(content=list_stories, headers=headers)


def create_story(story: Story):
    story_db = db.stories.find_one({'writerId': story.writerId, 'title': story.title})
    if story_db is not None:
        update_obj = {"content": story.content, "categories": story.categories, "description": story.description,
                      "storyCover": story.storyCover}

        if story.storyCover is None:
            update_obj.pop('storyCover', None)

        db.stories.update_one(
            {'_id': story_db['_id']},
            {"$set": {"content": story.content, "categories": story.categories, "description": story.description,
                      "storyCover": story.storyCover}}
        )

        if story_db.status.lower() == 'published':
            notify_admin("تم تحديث قصة منشورة!!", f"لقد تم تحديث القصة {story_db.title}")

        log_obj = {
            'text': f'Story Updated ({story_db.title}) with status ({story_db.status.lower()})',
            'createdAt': str(datetime.datetime.utcnow()),
            'source': 'stories'
        }
        db.logs.insert_one(log_obj)

    slug = slugify(story.title, allow_unicode=True)
    matches_len = db.stories.count_documents({'slug': {'$regex': f'{slug}'}})

    if matches_len > 0:
        slug = f'{slug}-{matches_len}'

    story_dict = story.dict()
    if type(story_dict['content']) is str:
        story_dict['content'] = json.loads(story_dict['content'], strict=False)

    if type(story_dict['categories']) is str:
        story_dict['categories'] = json.loads(story_dict['categories'], strict=False)

    story_dict['status'] = story.status.lower()
    story_dict['slug'] = slug
    story_dict['views'] = 0
    story_dict['rank'] = 0
    story_dict['dailyViews'] = {}
    story_dict['likerList'] = []
    story_dict['createdAt'] = datetime.datetime.utcnow()
    story_dict['updatedAt'] = datetime.datetime.utcnow()

    story_id = db.stories.insert_one(story_dict).inserted_id
    story_id = str(story_id)

    db.users.update_one(
        {"uid": story.writerId},
        {"$addToSet": {"userStoryIds": story_id}}
    )

    log_obj = {
        'text': f'New Story Created ({story.title}) with status ({story.status.lower()})',
        'createdAt': str(datetime.datetime.utcnow()),
        'source': 'stories'
    }
    db.logs.insert_one(log_obj)
    if story.status.lower() == 'pending':
        notify_admin("تم نشر قصة جديدة!!", f"لقد قام مستخدم بنشر قصة جديدة بعنوان {story.title}")


def mark_story_as_deleted(initiator_id: str, story_id: str):
    db.stories.update_one({'_id': ObjectId(story_id)}, {
        '$set': {'status': 'deleted'}})

    # deleting the story from the user collection
    db.users.update_one(
        {"uid": initiator_id},
        {"$pull": {"userStoryIds": story_id}}
    )

    story_name = db.stories.find_one({'_id': ObjectId(story_id)}, {'_id': 0, 'title': 1})['title']

    log_obj = {
        'text': f'Story Deleted ({story_name}))',
        'createdAt': str(datetime.datetime.utcnow()),
        'source': 'stories'
    }
    db.logs.insert_one(log_obj)


def update_story_fields(update_obj: UpdateStory):
    slug = slugify(update_obj.title, allow_unicode=True)
    matches_len = db.stories.count_documents({'slug': {'$regex': f'{slug}'}})

    if matches_len > 0:
        slug = f'{slug}-{matches_len}'

    story_dict = update_obj.dict()
    story_dict['slug'] = slug
    story_dict['updatedAt'] = datetime.datetime.utcnow()

    db.stories.update_one(
        {'_id': ObjectId(update_obj.storyId)},
        {"$set": story_dict}
    )

    if update_obj.status.lower() == 'published':
        notify_admin("تم تحديث قصة منشورة!!", f"لقد تم تحديث القصة {update_obj.title}")

    log_obj = {
        'text': f'Story Updated ({update_obj.title}) with status ({update_obj.status.lower()})',
        'createdAt': str(datetime.datetime.utcnow()),
        'source': 'stories'
    }
    db.logs.insert_one(log_obj)


def add_view(storyId: StoryID):
    story_id = storyId.storyId
    # Note: Daily view dates are dynamically created and incremented when it does not exist.
    db.stories.update_one({'_id': ObjectId(story_id)},
                          {'$inc': {'views': 1, f'dailyViews.{str(datetime.date.today())}': 1}})

    story_name = db.stories.find_one({'_id': ObjectId(story_id)}, {'title': 1})['title']
    log_obj = {
        'text': f'Some User Viewed Story ({story_name}))',
        'createdAt': str(datetime.datetime.utcnow()),
        'source': 'storyViews'
    }
    db.logs.insert_one(log_obj)


def remove_view(story_id: str):
    # Note: Daily view dates are dynamically created and incremented when it does not exist.
    db.stories.update_one({'_id': ObjectId(story_id)},
                          {'$inc': {'views': -1, f'dailyViews.{str(datetime.date.today())}': -1}})


def add_reader(story_reader: StoryReader):
    db.users.update_one(
        {'uid': story_reader.readerId},
        {'$addToSet': {"readStories": story_reader.storyId}}
    )


def add_liker(story_liker: StoryLiker):
    db.stories.update_one(
        {'_id': ObjectId(story_liker.storyId)},
        {'$addToSet': {"likerList": story_liker.likerId}}
    )
    db.users.update_one(
        {'uid': story_liker.likerId}, {'$addToSet': {"likedStories": story_liker.storyId}})

    story = list(db.stories.aggregate([
        {"$match": {'_id': ObjectId(story_liker.storyId)}},
        {
            "$lookup": {
                "from": "User",
                "let": {"writerId": "$writerId"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$uid", "$$writerId"]}}},
                    {"$project": {"_id": 0, 'FCM': 1}},
                ],
                "as": "writer"
            },
        },
        {"$unwind": "$writer"},
        {
            "$project": {
                "_id": 0,
                "storyId": {"$toString": "$_id"},
                "FCN": "$writer.FCM",
                "writerId": 1,
                "title": 1,
                "slug": 1,
            }
        }
    ]))[0]

    story_name = story['title']

    # notification part
    sender = db.users.find_one({"uid": story_liker.likerId}, {'_id': 0, 'username': 1, 'profileImage': 1})
    if sender is not None and story_liker.likerId != story['writerId']:
        title = story_name
        text = f"قام {sender['username']}  بالإعجاب بقصتك"
        image = sender['profileImage']
        link = f"/story/{story['slug']}"
        target_uid = story['writerId']
        sender_uid = story_liker.likerId
        notif_type = 'like'
        target_fcm = None
        if 'FCM' in story:
            target_fcm = story['FCM']
        send_notification(title, text, image, link,
                          notif_type, target_uid, sender_uid, target_fcm)

    log_obj = {
        'text': f'Some user liked the story ({story_name}))',
        'createdAt': str(datetime.datetime.utcnow()),
        'source': 'stories'
    }
    db.logs.insert_one(log_obj)


def remove_liker(liker_id: str, story_id: str):
    db.stories.update_one(
        {'_id': ObjectId(story_id)},
        {'$pull': {"likerList": liker_id}}
    )

    db.users.update_one(
        {'uid': liker_id}, {'$pull': {"likedStories": story_id}})


def get_single_story_obj(story):
    story['storyId'] = str(story['_id'])
    story.pop('_id', None)

    story['username'] = story['writer']['username']
    story['profileImage'] = story['writer']['profileImage']
    story['bio'] = story['writer']['bio']
    story['writerName'] = story['writer']['name']
    story.pop('writer', None)

    story['commentsCount'] = len(story['comments'])
    story['likes'] = len(story['likerList'])
    story['numPages'] = len(story['content'])
    story['createdAt'] = str(story['createdAt'])
    story['updatedAt'] = str(story['updatedAt']) if 'updatedAt' in story else str(story['createdAt'])
    story.pop('dailyViews', None)

    if 'type' not in story or story['type'] != 'chat':
        if type(story['content']) is str:
            story['content'] = json.loads(story['content'], strict=False)

    return story


def buy_chapter(info: BuyChapter):
    db.users.update_one({"uid": info.uid},
                        {"$push": {f"paidChapters.{info.storyId}": info.chapterNumber}, "$inc": {"coins": -40}})

from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, BackgroundTasks

from db import db
from src.AdminList.schemas import AdminList, UpdateAdminList
from src.utils import project_story_field
router = APIRouter(tags=['AdminList'])


@router.get(path="/get_admin_lists", description="Get all the admin story list", status_code=200)
async def get_admin_lists():
    admin_lists = list(db.admin_lists.aggregate([
        {
            "$lookup": {
                "from": "Story",
                "let": {"listStoryIds": "$listStoryIds"},
                "pipeline": [
                    {"$match": {"$expr": {"$in": [{"$toString": "$_id"}, "$$listStoryIds"]}}},
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
                    {
                        "$project": {
                            "_id": 0,
                            "storyId": {"$toString": "$_id"},
                            "writerName": "$writer.name",
                            "writerId": 1,
                            "title": 1,
                            "slug": 1,
                            "storyCover": 1,
                            "categories": 1,
                            "description": 1,
                            "rank": 1,
                            "type": 1,
                            "status": 1
                        }
                    }
                ],
                "as": "stories"
            }
        },
        {
            "$project": {
                "_id": 0,
                "listId": {"$toString": "$_id"},
                "title": 1,
                "status": 1,
                "stories": 1
            },
        },
    ]))
    return admin_lists


@router.put(path="/create_new_admin_list", description="Create a new admin list", status_code=201)
async def create_new_admin_list(admin_list: AdminList, background_tasks: BackgroundTasks):
    is_duplicate = db.admin_lists.count_documents({"title": admin_list.title}) > 0

    if is_duplicate:
        raise HTTPException(status_code=400, detail="The list already exists")

    background_tasks.add_task(create_an_admin_list, admin_list)
    return {"message": "The list has been created successfully"}


@router.post(path="/update_admin_list", description="Add or Remove a story from an admin list", status_code=200)
async def create_new_admin_list(update_admin_list: UpdateAdminList, background_tasks: BackgroundTasks):
    if update_admin_list.operation != 'add' and update_admin_list.operation != 'remove':
        raise HTTPException(status_code=400, detail="Operation is not allowed")

    background_tasks.add_task(update_an_admin_list, update_admin_list)
    return {"message": "The list has been updated successfully"}


@router.delete(path="/delete_admin_list/{list_id}", description="Delete an admin list", status_code=200)
async def create_new_admin_list(list_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(delete_an_admin_list, list_id)
    return {"message": "The list has been deleted successfully"}


def create_an_admin_list(admin_list: AdminList):
    list_dict = admin_list.dict()
    list_dict['listStoryIds'] = []

    db.admin_lists.insert_one(list_dict)

    log_obj = {
        'text': f'New admin list created ({admin_list.title})',
        'createdAt': str(datetime.utcnow()),
        'source': 'adminLists'
    }
    db.logs.insert_one(log_obj)


def update_an_admin_list(update_list: UpdateAdminList):
    if update_list.operation == 'add':
        db.admin_lists.update_one(
            {"_id": ObjectId(update_list.listId)},
            {"$addToSet": {"listStoryIds": update_list.storyId}}
        )
    elif update_list.operation == 'remove':
        db.admin_lists.update_one(
            {"_id": ObjectId(update_list.listId)},
            {"$pull": {"listStoryIds": update_list.storyId}}
        )


def delete_an_admin_list(list_id: str):
    db.admin_lists.delete_one({'_id': ObjectId(list_id)})

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi_redis_cache import cache_one_month

from db import db
from src.Category.schemas import Category

router = APIRouter(tags=['Categories'])


@router.get("/list_of_categories", description="Use to get all the categories", status_code=200)
@cache_one_month()
async def get_categories():
    project_obj = {
        "_id": 0,
        "id": {"$toString": "$_id"},
        "name": 1,
        "nameAr": 1,
    }
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    return JSONResponse(content=list(db.categories.find({}, project_obj)), headers=headers)


@router.put("/add_new_category", description="Use to add a new category", status_code=200)
async def add_new_category(new_category: Category, background_tasks: BackgroundTasks):
    background_tasks.add_task(create_new_category, new_category)
    return {"message": "The category has been created successfully"}


def create_new_category(new_category: Category):
    db.blogs.insert_one(new_category.dict())

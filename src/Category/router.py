from fastapi import APIRouter, BackgroundTasks

from db import db
from src.Category.schemas import Category

router = APIRouter(tags=['Categories'])


@router.get("/list_of_categories", description="Use to get all the categories", status_code=200)
async def get_categories():
    project_obj = {
        "id": {"$toString": "$_id"},
        "name": 1,
        "nameAr": 1,
    }
    return list(db.categories.find({}, project_obj))


@router.put("/add_new_category", description="Use to add a new category", status_code=200)
async def add_new_category(new_category: Category, background_tasks: BackgroundTasks):
    background_tasks.add_task(create_new_category, new_category)
    return {"message": "The category has been created successfully"}


def create_new_category(new_category: Category):
    db.blogs.insert_one(new_category.dict())

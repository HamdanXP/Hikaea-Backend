from datetime import datetime

import pymongo
from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks
from slugify import slugify

from db import db
from src.Blog.schemas import Blog

router = APIRouter(tags=['Blog'])


@router.post(path="/add_new_blog", description="Create a new blog", status_code=201)
async def add_new_blog(new_blog: Blog, background_tasks: BackgroundTasks):
    background_tasks.add_task(create_new_blog, new_blog)
    return {"message": "The blog has been created successfully"}


@router.get(path="/get_all_blogs", description="Get all blogs", status_code=200)
async def get_all_blogs(limit: int = 6, nextPage: str = ""):
    find_obj = {}
    project_obj = {
        "_id": 0,
        "blogId": {"$toString": "$_id"},
        "title": 1,
        "content": 1,
        "slug": 1,
        "writerName": 1,
        "blogCover": 1,
        "categories": 1,
        "createdAt": 1
    }

    if nextPage != "":
        find_obj['_id'] = {'$lt': ObjectId(nextPage)}

    blogs = list(db.blogs.find(find_obj, project_obj).sort('createdAt', pymongo.DESCENDING).limit(limit))
    return blogs


@router.get(path="/get_blog/{slug}", description="Get a single blog", status_code=200)
async def get_blog(slug: str):
    project_obj = {
        "_id": 0,
        "blogId": {"$toString": "$_id"},
        "title": 1,
        "content": 1,
        "slug": 1,
        "writerName": 1,
        "blogCover": 1,
        "categories": 1,
        "createdAt": 1
    }

    return db.blogs.find_one({'slug': slug}, project_obj)


def create_new_blog(new_blog: Blog):
    slug = slugify(new_blog.title, allow_unicode=True)
    matches_len = db.blogs.count_documents({'slug': {'$regex': f'{slug}'}})

    if matches_len > 0:
        slug = f'{slug}-{matches_len}'

    blog_dict = new_blog.dict()
    blog_dict['slug'] = slug
    blog_dict['createdAt'] = str(datetime.utcnow())

    db.blogs.insert_one(blog_dict)

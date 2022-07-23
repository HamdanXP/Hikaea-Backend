import os
import ssl
import datetime

from fastapi import FastAPI, Request, Response, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi_redis_cache import FastApiRedisCache, cache
from server.routers import user, short, story, comment, category
from pymongo import MongoClient


async def verify_token(Authorization: str = Header()):
    if Authorization != "Bearer bcfb0889-6899-438c-b34d-ea13d29c167f":
        raise HTTPException(status_code=401, detail="Authorization header invalid")


LOCAL_REDIS_URL = "redis://127.0.0.1:6379"

app = FastAPI(dependencies=[Depends(verify_token)])
app.add_middleware(GZipMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    redis_cache = FastApiRedisCache()
    redis_cache.init(
        host_url=os.environ.get("REDIS_URL", LOCAL_REDIS_URL),
        prefix="myapi-cache",
        response_header="X-MyAPI-Cache",
        ignore_arg_types=[Request, Response]
    )


# db_username = 'hikaya'
# db_password = 'hikaya308'
# db_name = 'hikayaDB'
# cluster = MongoClient(
#     f'mongodb+srv://{db_username}:{db_password}@hikaya.hwclb.mongodb.net/{db_name}?retryWrites=true&w=majority',
#     connectTimeoutMS=30000, socketTimeoutMS=None, socketKeepAlive=True, connect=False,
#     maxPoolsize=1, ssl_cert_reqs=ssl.CERT_NONE)
#
# db = cluster['Hikaya']
# user_collection = db['User']
# story_collection = db['Story']
# categories_collection = db['Category']
# comments_collection = db['Comments']
# admin_lists_collection = db['AdminLists']
# log_collection = db['Log']
# report_collection = db['Report']
# short_collection = db['Short']


app.include_router(user.router)
app.include_router(short.router)
app.include_router(story.router)
app.include_router(category.router)
# app.include_router(comment.router)
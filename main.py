import os

from fastapi import FastAPI, Request, Response, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi_redis_cache import FastApiRedisCache

from db import db
from src.AdminList.router import router as admin_list_router
from src.Blog.router import router as blog_router
from src.Category.router import router as category_router
from src.Comment.router import router as comment_router
from src.Control.router import router as control_router
from src.Dashboard.router import router as dashboard_router
from src.Notification.router import router as notification_router
from src.Report.router import router as report_router
from src.Short.router import router as short_router
from src.Story.router import router as story_router
from src.User.router import router as user_router


async def verify_token(Authorization: str = Header()):
    if Authorization != "Bearer bcfb0889-6899-438c-b34d-ea13d29c167f":
        raise HTTPException(status_code=401, detail="Authorization header invalid")


async def set_content_type(response: Response):
    response.media_type = "application/json"
    response.charset = "UTF-8"


LOCAL_REDIS_URL = "redis://127.0.0.1:6379"

app = FastAPI(dependencies=[Depends(verify_token), Depends(set_content_type)])
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
    db_username = 'hikaya'
    db_password = 'hikaya308'
    db_name = 'hikayaDB'
    connection_string = f'mongodb+srv://{db_username}:{db_password}@hikaya.hwclb.mongodb.net/{db_name}?retryWrites=true&w=majority'
    db.connect_to_database(path=connection_string)

    redis_cache = FastApiRedisCache()
    redis_cache.init(
        host_url=os.environ.get("REDIS_URL", LOCAL_REDIS_URL),
        prefix="myapi-cache",
        response_header="X-MyAPI-Cache",
        ignore_arg_types=[Request, Response]
    )


@app.on_event("shutdown")
async def shutdown():
    await db.close_database_connection()

app.include_router(admin_list_router)
app.include_router(blog_router)
app.include_router(category_router)
app.include_router(comment_router)
app.include_router(control_router)
app.include_router(dashboard_router)
app.include_router(notification_router)
app.include_router(report_router)
app.include_router(short_router)
app.include_router(story_router)
app.include_router(user_router)

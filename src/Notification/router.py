from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse

from db import db

router = APIRouter(tags=['Notification'])


@router.get("/get_notifications/{user_id}", description="Use to get a user's notifications list", status_code=200)
async def get_user_notifications(user_id: str):
    user_notifications = list(db.notifications.aggregate([
        {"$match": {"targetUid": user_id}},
        {
            "$project": {
                "_id": 0,
                "notifId": {"$toString": "$_id"},
                "title": 1,
                "text": 1,
                "createdAt": 1,
                "image": 1,
                "link": 1,
                "type": 1,
                "targetUid": 1,
                "senderUid": 1,
                "targetFCM": 1,
            },
        },
    ]))
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    return JSONResponse(content=user_notifications, headers=headers)


@router.delete("/clear_notifications/{user_id}")
async def clear_notifications(user_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(clear_user_notifications, user_id)
    return {"message": "The comment has been cleared successfully"}


def clear_user_notifications(user_id: str):
    db.notifications.delete_many({'targetUid': user_id})

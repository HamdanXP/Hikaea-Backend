from fastapi import APIRouter, BackgroundTasks

from db import db

router = APIRouter(tags=['Notification'])


@router.get("/get_notifications/{user_id}", description="Use to get a user's notifications list", status_code=200)
async def get_user_notifications(user_id: str):
    user_notifications = db.notifications.find_one({"targetUid": user_id})
    user_notifications['notifId'] = str(user_notifications['_id'])
    user_notifications.pop('_id', None)

    return user_notifications


@router.delete("/clear_notifications/{user_id}")
async def clear_notifications(user_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(clear_user_notifications, user_id)
    return {"message": "The comment has been cleared successfully"}


def clear_user_notifications(user_id: str):
    db.notifications.delete_many({'targetUid': user_id})

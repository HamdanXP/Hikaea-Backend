from datetime import datetime

import pymongo
import requests

from db import db

project_story_field = {
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
        "numPages": {"$size": "$content"},
        "status": 1
    }
}

project_full_story = {
    "$project": {
        "_id": 0,
        "storyId": {"$toString": "$_id"},
        "writerName": "$writer.name",
        "bio": "$writer.bio",
        "username": "$writer.username",
        "profileImage": "$writer.profileImage",
        "writerId": 1,
        "title": 1,
        "slug": 1,
        "storyCover": 1,
        "categories": 1,
        "description": 1,
        "views": 1,
        "rank": 1,
        "type": 1,
        "numPages": {"$size": "$content"},
        "likes": {"$size": "$likerList"},
        "commentsCount": {"$size": "$comments"},
        "comments": "$emptyArray",
        "status": 1,
        "createdAt": {"$toString": "$createdAt"},
        "updatedAt": {"$toString": "$updatedAt"},
    }
}

story_writer = {
    "$lookup": {
        "from": "User",
        "let": {"writerId": "$writerId"},
        "pipeline": [
            {"$match": {"$expr": {"$eq": ["$uid", "$$writerId"]}}},
            {"$project": {"_id": 0, 'uid': 1, 'name': 1, 'username': 1, 'profileImage': 1, 'bio': 1}},
        ],
        "as": "writer"
    },
}

story_comments = {
    "$lookup": {
        "from": "Comments",
        "let": {"storyId": {"$toString": "$_id"}},
        "pipeline": [
            {"$match": {"$expr": {"$eq": ["$storyId", "$$storyId"]}}},
            {
                "$lookup": {
                    "from": "User",
                    "let": {"commenterId": "$commenterId"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$uid", "$$commenterId"]}}},
                        {
                            "$project": {
                                "_id": 0, 'uid': 1, 'name': 1, 'username': 1, 'profileImage': 1,
                                'bio': 1
                            }
                        },
                    ],
                    "as": "commenter"
                },
            },
            {"$unwind": "$commenter"},
            {
                "$project": {
                    "_id": 0,
                    "commentId": {"$toString": "$_id"},
                    "commenterId": 1,
                    "storyId": 1,
                    "isWriter": 1,
                    "comment": 1,
                    "status": 1,
                    "createdAt": 1,
                    "replyToId": 1,
                    'name': '$commenter.name',
                    'username': '$commenter.username',
                    'profileImage': '$commenter.profileImage'
                }
            },
            {
                "$sort": {
                    'createdAt': pymongo.DESCENDING,
                }
            },
        ],
        "as": "comments"
    },
}


def send_notification(title, text, image, link, notif_type, target_uid, sender_uid, target_fcm):
    notif_obj = {
        'title': title,
        'text': text,
        'createdAt': str(datetime.utcnow()),
        'image': image,
        'link': link,
        'type': notif_type,
        'targetUid': target_uid,
        'senderUid': sender_uid,
        'targetFCM': target_fcm
    }

    # return if notification is duplicate
    not_unique_notif = db.notifications.find_one({'title': title,
                                                  'text': text,
                                                  'image': image,
                                                  'link': link,
                                                  'type': notif_type,
                                                  'targetUid': target_uid,
                                                  'senderUid': sender_uid,
                                                  'targetFCM': target_fcm})

    if not_unique_notif is not None:
        return

    # save notification
    db.notifications.insert_one(notif_obj)
    send_fcm_notification(target_fcm, text, title, image)


def notify_admin(title, text):
    turki = db.users.find_one({"username": "Turki"}, {'FCM': 1})
    send_fcm_notification(turki['FCM'], text, title, 'https://a.top4top.io/p_22286og1w1.jpeg')

    hamdan = db.users.find_one({"username": "Hamdan"}, {'FCM': 1})
    send_fcm_notification(hamdan['FCM'], text, title, 'https://a.top4top.io/p_22286og1w1.jpeg')


def send_fcm_notification(target_fcm, text, title, image):
    headers = {'Content-Type': 'application/json',
               'Authorization': 'key=AAAAQR0QZ0w:APA91bE9xQE_0H6Cuz5HYBTweplhC96xA6Bzi3Hoo0tHK3LptRbd_6BtiFWSxH_DCk3t6Q4oK8BidYX0geVn3UwTbLuzr2jpdsMlvABwAZ5meA2QcEK559Gwp3Lw6-qGAFlZN2GR8Lop'}

    obj = {
        "to": target_fcm,
        "priority": "high",
        "mutable_content": True,
        "notification": {
            "body": text,
            "title": title,
            "sound": "default"
        },
        "data": {
            "content": {
                "id": 1,
                "channelKey": "alerts",
                "displayOnForeground": True,
                "notificationLayout": "BigPicture",
                "bigPicture": image,
                "showWhen": True,
                "autoDismissible": True,
            }
        }
    }

    url = 'https://fcm.googleapis.com/fcm/send'

    try:
        requests.post(url, headers=headers, json=obj)
    except:
        print(f'failed to send fcm: target FCM ({target_fcm})')

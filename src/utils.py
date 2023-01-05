import json
from datetime import datetime

import httpx
from bson import json_util, ObjectId

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
        ],
        "as": "comments"
    },
}


def get_user_profile(uid):
    profile = db.users.find_one({'uid': uid})
    if profile:
        profile = json_util.dumps(profile)
        profile = json.loads(profile)
        return profile

    else:
        return None


def get_story_jsonFormat(story_id):
    return json.loads(json_util.dumps(db.stories.find_one({"_id": ObjectId(story_id)})))


def get_story_comments_and_writer(story):
    profiles_ids = []
    comments = list(db.comments.find(
        {'$and': [{'storyId': str(story['_id']), 'status': 'published'}]}))
    for comment in comments:
        if {'uid': comment['commenterId']} not in profiles_ids:
            profiles_ids.append({'uid': comment['commenterId']})

    profiles_ids.append({'uid': story['writerId']})
    profiles = list(
        db.users.find({'$or': profiles_ids},
                      {'uid': 1, 'name': 1, 'username': 1, 'profileImage': 1, 'bio': 1}))

    writer = [writer for writer in profiles if writer['uid']
              == story['writerId']][0]

    format_comments(comments, profiles)
    return writer, comments


def get_story_info(story, profile, comments, without_content=False):
    if 'type' not in story or story['type'] != 'chat':
        if type(story['content']) is str:
            story['content'] = json.loads(story['content'], strict=False)

        for page in story['content']:
            if '<pre>' not in page['text']:
                page['text'] = f"<pre>{page['text']}</pre>"

    story['storyId'] = str(story['_id'])
    story['bio'] = profile['bio']
    story['writerName'] = profile['name']
    story['username'] = profile['username']
    story['profileImage'] = profile['profileImage']
    story['likes'] = len(story['likerList'])
    story['createdAt'] = str(story['createdAt'])
    story['commentsCount'] = len(comments)
    story['numPages'] = len(story['content'])
    story['comments'] = comments
    story['rank'] = 0 if 'rank' not in story else story['rank']
    story.pop('_id', None)
    story.pop('dailyViews', None)
    if without_content:
        story.pop('content', None)
        story.pop('likerList', None)
        story.pop('adminMessage', None)
    return story


def format_comments(comments, profiles):
    for comment in comments:
        commenter = [
            commenter for commenter in profiles if comment['commenterId'] == commenter['uid']][0]
        comment['username'] = commenter['username']
        comment['name'] = commenter['name']
        comment['profileImage'] = commenter['profileImage']
        comment['commentId'] = str(comment['_id'])
        comment.pop('_id', None)


def get_full_stories_json(stories):
    profiles_ids = []
    stories_ids = []
    for story in stories:
        if {'uid': story['writerId']} not in profiles_ids:
            profiles_ids.append({'uid': story['writerId']})
        stories_ids.append(
            {'storyId': str(story['_id']), 'status': 'published'})

    if len(stories) == 0:
        return []

    stories_comments = list(db.comments.find({'$or': stories_ids}))
    for comment in stories_comments:
        if {'uid': comment['commenterId']} not in profiles_ids:
            profiles_ids.append({'uid': comment['commenterId']})

    profiles = list(
        db.users.find({'$or': profiles_ids},
                      {'uid': 1, 'name': 1, 'username': 1, 'profileImage': 1, 'bio': 1}))

    format_comments(stories_comments, profiles)

    full_stories = []
    for story in stories:
        try:
            writer = [writer for writer in profiles if writer['uid']
                      == story['writerId']][0]
            comments = [
                comment for comment in stories_comments if comment['storyId'] == str(story['_id'])]
            full_stories.append(get_story_info(story, writer, comments, True))
        except:
            continue
    return full_stories


async def get_stories_json(stories):
    stories_json = []
    writers_ids = []
    stories = list(stories)
    for story in stories:
        if {'uid': story['writerId']} not in writers_ids:
            writers_ids.append({'uid': story['writerId']})

    if len(writers_ids) == 0:
        return []

    profiles = list(db.users.find(
        {'$or': writers_ids}, {'uid': 1, 'name': 1}))

    for story in stories:
        writer_name = [writer for writer in profiles if writer['uid']
                       == story['writerId']][0]['name']
        story_json = {
            "storyId": str(story['_id']),
            "title": story['title'],
            "writerName": writer_name,
            "slug": story['slug'],
            "storyCover": story['storyCover'],
            "categories": story['categories'],
            "description": story['description'],
            "rank": story['rank'] if 'rank' in story else 0,
            "type": story['type'] if 'type' in story else None,
            "numPages": len(story['content']),
            "status": story['status']
        }
        stories_json.append(story_json)
    return stories_json


def get_short_json(shorts):
    shorts_json = []
    for short in shorts:
        shorts_json.append({
            'shortId': str(short['_id']),
            'text': short['text'],
            'createdAt': short['createdAt'],
            'type': short['type'],
            'isAnon': short['isAnon'],
            'writerId': short['writerId'],
            'tiktokId': short['tiktokId'],
            'isHidden': short['isHidden'],
            'commentsCount': len(short['comments']) if 'comments' in short else 0,
            'votes': short['votes']
        })
    return shorts_json


def get_single_short_json(short):
    short['shortId'] = str(short['_id'])
    short.pop('_id')

    if 'comments' in short:
        short['commentsCount'] = len(short['comments'])
        for comment in short['comments']:
            comment["commentId"] = str(comment['commentId'])

        short['comments'].sort(key=lambda x: x['votes'], reverse=True)
    else:
        short['comments'] = []
        short['commentsCount'] = 0

    return short


def get_list_of_stories(ids):
    stories = list(db.stories.find({'$or': ids},
                                   {'_id': 1, 'title': 1, 'slug': 1, 'storyCover': 1,
                                    'categories': 1, 'content': 1,
                                    'description': 1}))
    for story in stories:
        story['storyId'] = str(story['_id'])
        story['numPages'] = len(story['content'])
        story.pop('_id', None)
    return stories


def get_story_comments(story_id):
    comments = list(db.comments.find(
        {'$and': [{'storyId': story_id, 'status': 'published'}]}))
    commenter_ids = []
    for comment in comments:
        if {'uid': comment['commenterId']} not in commenter_ids:
            commenter_ids.append({'uid': comment['commenterId']})

    if len(commenter_ids) == 0:
        return []

    profiles = list(
        db.users.find({'$or': commenter_ids}, {'uid': 1, 'username': 1, 'name': 1, 'profileImage': 1}))
    format_comments(comments, profiles)
    return comments


async def send_notification(title, text, image, link, notif_type, target_uid, sender_uid, target_fcm):
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

    headers = {'Content-Type': 'application/json',
               'Authorization': 'key=AAAAQR0QZ0w:APA91bE9xQE_0H6Cuz5HYBTweplhC96xA6Bzi3Hoo0tHK3LptRbd_6BtiFWSxH_DCk3t6Q4oK8BidYX0geVn3UwTbLuzr2jpdsMlvABwAZ5meA2QcEK559Gwp3Lw6-qGAFlZN2GR8Lop'}

    obj = {
        "to": target_fcm,
        "notification": {
            "body": text,
            "title": title,
            "image": image,
            "sound": "default",
        },
        "apns": {
            "payload": {
                "aps": {
                    "mutable-content": 1
                }
            }
        },
    }

    url = 'https://fcm.googleapis.com/fcm/send'

    try:
        response = httpx.post(url, headers=headers, json=obj)
    except:
        response = 'failed to send fcm'

    return response

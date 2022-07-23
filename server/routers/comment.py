from fastapi import APIRouter

from server.models.comment import Comment, CommentsList

router = APIRouter(tags=['Comments'])


@router.post("/add_new_comment", description="Use to add a new comment to a story", status_code=201)
def add_new_comment(comment: Comment):
    return comment.commentId


@router.delete("/delete_comment/{comment_id}", description="Use to delete a story's comment", status_code=200)
def delete_comment(comment_id: str):
    return None


@router.get("/get_story_comments/{story_id}", description="Use to get all the story's comments",
            response_model=CommentsList, status_code=200)
def get_story_comments(story_id: str):
    return CommentsList()
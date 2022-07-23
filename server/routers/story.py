from fastapi import APIRouter

from server.models.story import Story, SimplifiedStoriesList, StoriesList, UpdateStoryModel, StoryID, StoryReader, \
    StoryLiker, StoriesQuery

router = APIRouter(tags=['Stories'])


@router.post("/add_story", description="Use to create a new story", status_code=201)
def add_story(story: Story):
    return {"storyId": story.storyId, "slug": story.slug}


@router.get("/get_story/{slug}", description="Use to get a story by its slug", response_model=Story, status_code=200)
def get_story(slug: str):
    return Story()


@router.post("/get_all_stories", description="Use to get all the stories", response_model=StoriesList, status_code=200)
def get_all_stories(storiesQuery: StoriesQuery, limit: int = 12, type: str = None):
    return StoriesList()


@router.delete("/delete_story/{initiator_id}/{story_id}", description="Use to delete a user's story", status_code=200)
def delete_story(initiator_id: str, story_id: str):
    return None


@router.put("/update_story", description="Use to update a single story", status_code=200)
def update_story(story: UpdateStoryModel):
    return {"storyId": story.storyId, "slug": story.slug}


@router.get("/get_matched_stories/{search_text}", description="Use to search the stories by the title",
            response_model=SimplifiedStoriesList, status_code=200)
def search_stories():
    return SimplifiedStoriesList()


@router.get("/get_random_story", description="Use to get a random story", response_model=Story, status_code=200)
def get_random_story():
    return Story()


@router.put("/add_story_view", description="Use to add a story view", status_code=200)
def add_story_view(storyId: StoryID):
    return "A story view has been registered"


@router.delete("/remove_story_view/{story_id}", description="Use to remove a story view", status_code=200)
def delete_story_view(story_id: str):
    return "A story view has been deleted"


@router.put("/add_story_reader", description="Use to add a story reader", status_code=200)
def add_story_reader(story_reader: StoryReader):
    return None


@router.put("/add_story_liker", description="Use to add a story liker", status_code=200)
def add_story_liker(story_liker: StoryLiker):
    return None


@router.delete("/delete_story_liker/{liker_id}/{story_id}", description="Use to delete a story liker", status_code=200)
def delete_story_liker(liker_id: str, story_id: str):
    return None


@router.get("/get_user_stories/{writer_id}", description="Use to get all the stories related to a writer",
            response_model=StoriesList, status_code=200)
def get_user_stories(writer_id: str):
    return StoriesList()

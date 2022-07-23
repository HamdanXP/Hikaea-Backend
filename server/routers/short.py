from fastapi import APIRouter
from server.models.short import Short, ShowShorts

router = APIRouter(tags=['Shorts'])


@router.post("/add_short", description="Use to create a new short", status_code=201)
def add_short(short: Short):
    return None


@router.get("/get_shorts", description="Use to get all the shorts", response_model=ShowShorts, status_code=200)
def get_shorts(limit: int = 0, next_page: str = None):
    return {"message": "User information is valid and unique"}

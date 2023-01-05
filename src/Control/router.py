from fastapi import APIRouter

from db import db

router = APIRouter(tags=['Control'])


@router.get("/get_controls", description="Use to get all the application controls", status_code=200)
async def get_controls():
    control = db.controls.find_one()
    control['controlId'] = str(control['_id'])
    control.pop('_id', None)

    return control

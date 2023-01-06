from fastapi import APIRouter
from fastapi.responses import JSONResponse

from db import db

router = APIRouter(tags=['Control'])


@router.get("/get_controls", description="Use to get all the application controls", status_code=200)
async def get_controls():
    control = db.controls.find_one()
    control['controlId'] = str(control['_id'])
    control.pop('_id', None)

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    return JSONResponse(content=control, headers=headers)

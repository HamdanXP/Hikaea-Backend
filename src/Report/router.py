from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks

from db import db
from src.Report.schemas import Report, UpdateReport

router = APIRouter(tags=['Report'])


@router.post("/post_report", description="Use to report on a user or a story", status_code=201)
async def create_report(report: Report, background_tasks: BackgroundTasks):
    background_tasks.add_task(create_new_report, report)
    return {"message": "The report has been created successfully"}


@router.get("/get_reports/{report_type}", description="Use to get the reported things", status_code=200)
async def get_reports(report_type: str = None):
    query = {}
    if report_type is not None:
        query['type'] = report_type

    findBy = [{'status': 'pending'}, query]

    reports = list(db.reports.aggregate([
        {"$match": findBy},
        {
            "$project": {
                "reportID": {"$toString": "$_id"},
                "content": 1,
                "status": 1,
                "type": 1,
                "reportedId": 1,
                "reporterId": 1
            }
        }
    ]))

    return reports


@router.put("/update_report_status", description="Use to update the status of a reported thing", status_code=200)
async def update_report_status(update_report: UpdateReport, background_tasks: BackgroundTasks):
    background_tasks.add_task(update_status, update_report)
    return {"message": "The report has been updated successfully"}


def create_new_report(report: Report):
    report_dict = report.dict()
    report_dict['status'] = 'pending'
    db.reports.insert_one(report_dict)

    log_obj = {
        'text': f'Report Added:{report.content}',
        'createdAt': str(datetime.utcnow()),
        'source': 'reports'
    }
    db.logs.insert_one(log_obj)


def update_status(update_report: UpdateReport):
    db.reports.update_one(
        {"_id": ObjectId(update_report.reportID)},
        {"$set": {'status': update_report.status}}
    )

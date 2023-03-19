import logging
import random
from string import ascii_lowercase

import requests
from celery.result import AsyncResult
from fastapi import FastAPI, Request, Body, Depends, File, UploadFile
from sqlalchemy.orm import Session

from . import stores_router
from .models import StoreMenuHours, StoreTimeZones, StoreStatus, Report, ReportData
from project.database import get_db_session
import pandas as pd
from io import BytesIO
import datetime
from .schemas import ReportStatus
from fastapi import status, HTTPException
from .tasks import generate_report


@stores_router.post("/uploadstoresstatuscsv")
def upload_stores_status_csv(db: Session, csv_file: UploadFile = File(...)):
    contents = csv_file.file.read()
    buffer = BytesIO(contents)
    df = pd.read_csv(buffer)
    buffer.close()
    csv_file.file.close()
    data = df.to_dict(orient='records')
    objects = []
    store_status = db.query(StoreStatus).all()
    for value in data:
        temp_dict = value.dict()
        filter_data = list(filter(lambda a: a['store_id'] == temp_dict['store_id']
                             and a['timestamp'] == temp_dict['timestamp_utc'], store_status))
        if not filter_data:
            db_item = StoreStatus(**temp_dict)
            objects.append(db_item)
    db.bulk_save_objects(objects)
    db.commit()
    return {"status": "Success"}


@stores_router.post("/uploadstoremenuhourscsv")
def upload_stores_menu_hours_csv(db: Session, csv_file: UploadFile = File(...)):
    contents = csv_file.file.read()
    buffer = BytesIO(contents)
    df = pd.read_csv(buffer)
    buffer.close()
    csv_file.file.close()
    data = df.to_dict(orient='records')
    store_hours = db.query(StoreMenuHours).all()
    objects = []
    for value in data:
        temp_dict = value.dict()
        filter_data = list(filter(lambda a: a['store_id'] == temp_dict['store_id']
                                            and a['day'] == temp_dict['day']
                                  and a['start_time'] == temp_dict['start_time_local'], store_hours))

        if not filter_data:
            db_item = StoreMenuHours(**temp_dict)
            objects.append(db_item)
    db.bulk_save_objects(objects)
    db.commit()
    return {"status": "Success"}


@stores_router.post("/uploadstorestimezonecsv")
def upload_stores_timezone__csv(db: Session, csv_file: UploadFile = File(...)):
    contents = csv_file.file.read()
    buffer = BytesIO(contents)
    df = pd.read_csv(buffer)
    buffer.close()
    csv_file.file.close()
    data = df.to_dict(orient='records')
    store_time_zones = db.query(StoreTimeZones).all()
    objects = []
    for value in data:
        temp_dict = value.dict()
        filter_data = list(filter(lambda a: a['store_id'] == temp_dict['store_id'], store_time_zones))
        if not filter_data:
            db_item = StoreTimeZones(**temp_dict)
            objects.append(db_item)
    db.bulk_save_objects(objects)
    db.commit()
    return {"status": "Success"}


@stores_router.post("/trigger_report_endpoint")
async def trigger_report_endpoint(db: Session,):
    report = Report(created=datetime.datetime.utcnow)
    db.add(report)
    db.commit()
    db.refresh(report)
    generate_report.apply_async()
    return {"report_id": report.id}


@stores_router.post("/get_report_endpoint")
async def get_report_endpoint(db: Session, report_day: ReportStatus):
    report = db.query(Report).filter(Report.id == report_day.id).all()
    if report:
        report = report[0]
        if report['status'] == 'Completed':
            data = db.query(ReportData).filter(ReportData.report == report['id']).all()
            return data
        else:
            return {'status': report['status']}

    else:
        return {"message": "Invalid Report ID"}














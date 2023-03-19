import random
import logging

import requests
from asgiref.sync import async_to_sync
from celery import shared_task
from celery.signals import task_postrun
from celery.utils.log import get_task_logger
from project.database import db_context
from celery.signals import after_setup_logger
from project.celery_utils import custom_celery_task
from project.loop.models import *
from datetime import datetime
from dateutil import parser



logger = get_task_logger(__name__)


@shared_task(name="generate_report")
def generate_report(self):
    with db_context() as session:
        try:
            reports = session.query(Report).filter(Report.status == 'Open').all()
            store_status = session.query(Report).all()
            store_menu_hours = session.query(StoreMenuHours).all()
            store_time_zones = session.query(StoreTimeZones).all()
            for report in reports:
                try:
                    logger.info(f"Starting Creating Reports for Reporting ID {report['id']}")
                    report_object = session.query(Report).get(report['id'])
                    report_object.status = 'Running'
                    session.commit()
                    # Logic for generating Report
                    final_report = process_reports(store_status, store_menu_hours, store_time_zones)
                    # Perform Bulk insert
                    if final_report['status'] is True:
                        session.bulk_insert_mappings(
                            ReportData, final_report
                        )
                        session.commit()

                    else:
                        raise Exception('No Report Data Processed')

                    report_object.status = 'Completed'
                    session.commit()

                except Exception as e:
                    logger.error(f"Error Occurrred due to {str(e)}")
                    report_object = session.query(Report).get(report['id'])
                    report_object.status = 'Failed'

        except Exception as exc:
            raise self.retry(exc=exc)


def process_reports(store_status, store_menu_hours, store_time_zones):

    try:
        result ={
            "status": False,
            "report_created": []
        }
        processed_store_id = []
        default_timezone_name = 'America/Chicago'
        for store in store_status:
            try:
                if store['store_id'] not in store_status:
                    processed_store_id.append(store['store_id'])
                    # time_zone_name = next((x.get('status') for x in store_time_zones if x.get('store_id', None) == store['store_id']), default_timezone_name)
                    current_store_id_data = list(filter(lambda z: z['store_id'] == store['store_id'] , store_status))
                    # Recent Most Data of taht particular store
                    max_data = max(current_store_id_data, key=lambda k: k["timestamp"])
                    day_of_week = parser.parse(max_data['timestamp']).date
                    # get the recent store hours data
                    filter_recent_store_working_hours = list(filter(lambda u: u['store_id'] == store['store_id'] , store_menu_hours))
                    if filter_recent_store_working_hours:
                        recent_most_working = next((l for l in filter_recent_store_working_hours if l['day'] == day_of_week and l['store_id'] ==store['store_id']  ), {})
                        uptime_last_week = 0
                        for up in filter_recent_store_working_hours:
                            uptime_last_week = (up.get('start_time_local', None) - up.get('end_time_local',
                                                                                          None)).hour + uptime_last_week

                        downtime_last_week = (24*7) - uptime_last_week
                        if not recent_most_working :
                            recent_most_working = max(filter_recent_store_working_hours, key=lambda k: k["day"])

                    else:
                        # Store is Working 24 hours
                        recent_most_working = {}
                        uptime_last_week = 24*7
                        downtime_last_week = 0
                        downtime_last_hour = 0.0
                        downtime_last_day = 0.0
                        downtime_last_week = 0.0

                    uptime_last_hour = (recent_most_working.get('start_time_local', None) - recent_most_working.get('end_time_local', None)).minutes  if recent_most_working.get('start_time_local', None) else 24*60
                    uptime_last_day = (recent_most_working.get('start_time_local', None) - recent_most_working.get('end_time_local', None)).hour  if recent_most_working.get('start_time_local', None) else 24
                    downtime_last_hour =  (24*60)- uptime_last_hour
                    downtime_last_day = 24 - uptime_last_day
                    downtime_last_week = 24*7 - uptime_last_week
                    temp = {
                        'store_id': store['store_id'],
                        'uptime_last_hour': uptime_last_hour,
                        'uptime_last_day': uptime_last_day,
                        'uptime_last_week': uptime_last_week,
                        'downtime_last_hour': downtime_last_hour,
                        'downtime_last_day': downtime_last_day,
                        'downtime_last_week': downtime_last_week,
                        'report': store['id']
                    }
                    result['report_created'].append(temp)

            except Exception as e:
                logger.error(f"Error Occurrred during processing reports for store status with store id {store['store_id']} due to {str(e)}")

    except Exception as e:
        logger.error(
            f"Error Occurrred during processing reports  due to {str(e)}")

    finally:
        result.update(status=True)
        return result


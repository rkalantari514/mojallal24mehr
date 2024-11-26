from celery import shared_task
import requests
import logging

logger = logging.getLogger(__name__)

@shared_task
def update_all_tables_job():
    try:
        logger.info("Job update_all_tables_job started.")
        response = requests.get('http://localhost:8000/updateall')
        if response.status_code == 200:
            logger.info("Job executed successfully.")
        else:
            logger.error(f"Failed to execute job, status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Error executing job: {str(e)}")
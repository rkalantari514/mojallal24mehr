# jobs.py
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_job
from .views import Updateall
from django.test import RequestFactory
import logging

logger = logging.getLogger(__name__)

# ایجاد scheduler
scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")

# بررسی و ثبت job برای اجرا هر ساعت
try:
    job = scheduler.get_job('update_all_tables_job')
    if job is None:
        @register_job(scheduler, "interval", minutes=60, id='update_all_tables_job')
        def update_all_tables_job():
            # ایجاد یک request ساختگی
            factory = RequestFactory()
            request = factory.get('/fake-path')
            logger.info("Job update_all_tables_job started.")
            Updateall(request)
except Exception as e:
    logger.error("Error registering job: %s", str(e))

# شروع scheduler
try:
    scheduler.start()
except Exception as e:
    logger.error("Error starting scheduler: %s", str(e))

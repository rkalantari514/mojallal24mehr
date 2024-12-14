# # jobs.py
# from apscheduler.schedulers.background import BackgroundScheduler
# from django_apscheduler.jobstores import DjangoJobStore
# from .views import Updateall
# from django.test import RequestFactory
# import logging
#
# logger = logging.getLogger(__name__)
#
# # ایجاد scheduler
# scheduler = BackgroundScheduler()
# scheduler.add_jobstore(DjangoJobStore(), "default")
#
# # ثبت job برای اجرا هر ساعت به صورت دستی
# def update_all_tables_job():
#     try:
#         # ایجاد یک request ساختگی
#         factory = RequestFactory()
#         request = factory.get('/fake-path')
#         logger.info("Job update_all_tables_job started.")
#         Updateall(request)
#     except Exception as e:
#         logger.error(f"Error executing job {job_id}: {str(e)}")
#
# job_id = 'update_all_tables_job'
# # بررسی و ثبت job تنها اگر وجود ندارد
# try:
#     existing_job = scheduler.get_job(job_id)
#     if not existing_job:
#         scheduler.add_job(update_all_tables_job, 'interval', minutes=60, id=job_id, replace_existing=True, misfire_grace_time=600, coalesce=True)
#         logger.info(f"Job {job_id} added.")
#     else:
#         logger.info(f"Job {job_id} already exists.")
# except Exception as e:
#     logger.error(f"Error handling job {job_id}: {str(e)}")
#
# # شروع scheduler
# try:
#     scheduler.start()
#     logger.info("Scheduler started successfully.")
# except Exception as e:
#     logger.error(f"Error starting scheduler: {str(e)}")

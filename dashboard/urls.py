from django.urls import path
from .views import CreateReport, Home1, CreateMonthlyReport, ReportsDailySummary




urlpatterns = [
    path('', Home1,name="home1"),
    path('reports/daily/summary', ReportsDailySummary, name="reports-daily-summary"),

# /reports/daily/summary           /reports/daily/detail (گزارش جزئی روزانه)



    path('createreport', CreateReport,name="create-report"),
    path('create_monthly_report', CreateMonthlyReport,name="create-monthly-report"),


]


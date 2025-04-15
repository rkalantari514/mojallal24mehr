from django.urls import path
from .views import CreateReport, Home1, CreateMonthlyReport, ReportsDailySummary, ReportsDailyDetile, CreateTotalReport

urlpatterns = [
    path('', Home1,name="home1"),
    path('reports/daily/summary', ReportsDailySummary, name="reports-daily-summary"),
    path('reports/daily/detile/<day>', ReportsDailyDetile, name="reports-daily-summary"),

# /reports/daily/summary           /reports/daily/detail (گزارش جزئی روزانه)



    path('create_total_report', CreateTotalReport,name="create-total-report"),
    path('createreport', CreateReport,name="create-report"),
    path('create_monthly_report', CreateMonthlyReport,name="create-monthly-report"),


]


from django.urls import path
from .views import CreateReport, Home1, CreateMonthlyReport, ReportsDailySummary, ReportsDailyDetile, CreateTotalReport, \
    CalendarTotal, YealyChart, Home2

urlpatterns = [
    path('', Home1,name="home1"),
    path('2', Home2,name="home2"),
    path('calendar', CalendarTotal,name="calendar-total"),
    path('reports/daily/summary', ReportsDailySummary, name="reports-daily-summary"),
    path('reports/daily/detile/<day>', ReportsDailyDetile, name="reports-daily-detile"),

    path('reports/yealy_chart/', YealyChart, name='yealychart'),


    path('create_total_report', CreateTotalReport,name="create-total-report"),
    path('createreport', CreateReport,name="create-report"),
    path('create_monthly_report', CreateMonthlyReport,name="create-monthly-report"),


]


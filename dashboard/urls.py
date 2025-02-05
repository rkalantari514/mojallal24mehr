from django.urls import path

from dashkala.views import DsshKala
from .views import CreateReport, Home1, CreateMonthlyReport

urlpatterns = [
    path('', Home1,name="home1"),



    # path('', Home5,name="home1"),
    # path('', DsshKala,name="home1"),



    path('createreport', CreateReport,name="create-report"),
    path('create_monthly_report', CreateMonthlyReport,name="create-monthly-report"),


]


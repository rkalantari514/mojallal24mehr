from django.urls import path

from mahakupdate.views import Update_from_mahak

urlpatterns = [
    path('1', Update_from_mahak,name="update"),


]


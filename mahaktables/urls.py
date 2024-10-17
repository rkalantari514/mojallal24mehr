from django.urls import path

from mahaktables.views import MTables

urlpatterns = [
    path('mahaktables', MTables,name="mtables"),


]


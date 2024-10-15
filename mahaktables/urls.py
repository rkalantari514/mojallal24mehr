from django.urls import path

from mahaktables.views import MTables

urlpatterns = [
    path('2', MTables,name="mtables"),


]


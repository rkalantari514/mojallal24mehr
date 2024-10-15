from django.urls import path
from .views import Home1
from mahaktables.views import MTables

urlpatterns = [
    path('', Home1,name="home1"),
]


from django.urls import path

from dashkala.views import DsshKala
from .views import Home1
from mahaktables.views import MTables

urlpatterns = [
    # path('', Home1,name="home1"),
    path('', DsshKala,name="home1"),


]


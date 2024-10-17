from django.urls import path
from .views import Home1, DsshKala
from mahaktables.views import MTables

urlpatterns = [
    path('', Home1,name="home1"),
    path('dash/kala', DsshKala,name="dashkala"),

]


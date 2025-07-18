from django.urls import path

from jariashkhas.views import JariAshkasList


urlpatterns = [

    path('', JariAshkasList, name='jari-ashkas-list'),  # لیست اصلی رویدادها

]

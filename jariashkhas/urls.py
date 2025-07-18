from django.urls import path

from jariashkhas.views import JariAshkasList


urlpatterns = [

    path('<km>/<int:moin>', JariAshkasList, name='jari-ashkas-list'),  # لیست اصلی رویدادها

]

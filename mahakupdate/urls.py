from django.urls import path

from mahakupdate.views import Update_from_mahak, Kala_group

urlpatterns = [
    path('1', Update_from_mahak,name="update"),




    path('kalagroup', Kala_group,name="kala_group"),


]


from django.urls import path
from django.shortcuts import redirect

from accounting.views import TarazKol, ChequesRecieveTotal

urlpatterns = [





    path('acc/<col>/<moin>/<tafzili>', TarazKol, name='taraz-kol'),
    path('acc/cheques_recieve_total', ChequesRecieveTotal, name='cheques-recieve-total'),







]

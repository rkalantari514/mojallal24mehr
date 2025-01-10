from django.urls import path
from django.shortcuts import redirect

from accounting.views import TarazKol

urlpatterns = [





    path('acc/<col>/<moin>/<tafzili>', TarazKol, name='taraz-kol'),







]

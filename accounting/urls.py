from django.urls import path
from django.shortcuts import redirect

from accounting.views import TarazKol, ChequesRecieveTotal, balance_sheet_kol, balance_sheet_moin, balance_sheet_tafsili

urlpatterns = [

    path('acc/<col>/<moin>/<tafzili>', TarazKol, name='taraz-kol'),
    path('acc/cheques_recieve_total', ChequesRecieveTotal, name='cheques-recieve-total'),
    path('balance-sheet-kol/', balance_sheet_kol, name='balance_sheet_kol'),

    path('balance-sheet-moin/<int:kol_code>/', balance_sheet_moin, name='balance_sheet_moin'),

    path('balance-sheet-kol/', balance_sheet_kol, name='balance_sheet_kol'),
    path('balance-sheet-moin/<int:kol_code>/', balance_sheet_moin, name='balance_sheet_moin'),
    path('balance-sheet-tafsili/<int:kol_code>/<int:moin_code>/', balance_sheet_tafsili,
         name='balance_sheet_tafsili'),
]

from django.urls import path
from django.shortcuts import redirect

from accounting.views import TarazKol, ChequesRecieveTotal, balance_sheet_kol, balance_sheet_moin, \
    balance_sheet_tafsili, SanadTotal, ChequesPayTotal, BedehkaranMoshtarian, JariAshkhasMoshtarian, \
    JariAshkhasMoshtarianDetail, HesabMoshtariDetail, LoanTotal, loan_summary_api

urlpatterns = [
    path('acc/loan_total', LoanTotal, name='loan-total'),

    path('acc/jariashkhas/moshtari/<int:tafsili>', HesabMoshtariDetail, name='hesab-moshtari-detail'),
    path('acc/jariashkhas/moshtarian/detaile/<int:filter_id>', JariAshkhasMoshtarianDetail, name='jari_ashkhas_moshtarian_detail'),
    path('acc/jariashkhas/moshtarian/total', JariAshkhasMoshtarian, name='jari-ashkhas-moshtarian'),

    path('acc/bedehkaran/moshtarian/<state>', BedehkaranMoshtarian, name='bedehkaran-moshtarian'),
    path('acc/cheques_recieve_total', ChequesRecieveTotal, name='cheques-recieve-total'),
    path('acc/cheques_pay_total', ChequesPayTotal, name='cheques-pay-total'),

    path('acc/<col>/<moin>/<tafzili>', TarazKol, name='taraz-kol'),
    path('acc/cheques_recieve_total', ChequesRecieveTotal, name='cheques-recieve-total'),
    path('balance-sheet-kol/', balance_sheet_kol, name='balance_sheet_kol'),

    path('balance-sheet-moin/<int:kol_code>/', balance_sheet_moin, name='balance_sheet_moin'),

    path('balance-sheet-kol/', balance_sheet_kol, name='balance_sheet_kol'),
    path('balance-sheet-moin/<int:kol_code>/', balance_sheet_moin, name='balance_sheet_moin'),
    path('balance-sheet-tafsili/<int:kol_code>/<int:moin_code>/', balance_sheet_tafsili,
         name='balance_sheet_tafsili'),
    path('sanad_total/<kol_code>/<moin_code>/<tafzili_code>/', SanadTotal,
         name='sanad_total'),






# for api
    path('api/loan-summary/', loan_summary_api, name='loan_summary'),

]


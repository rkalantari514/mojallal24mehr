from django.urls import path
from accounting.views import (
    TarazKol, ChequesRecieveTotal, balance_sheet_kol, balance_sheet_moin,
    balance_sheet_tafsili, SanadTotal, ChequesPayTotal, BedehkaranMoshtarian,
    JariAshkhasMoshtarian, JariAshkhasMoshtarianDetail, HesabMoshtariDetail,
    LoanTotal, loan_summary_api, SaleTotal
)
from mahakupdate.sendtogap import run_dial_script, stop_dialer

# from mahakupdate.sendtogap import dial_number

urlpatterns = [
    path('sale/total/', SaleTotal, name='sale-total'),


    path('acc/loan_total/<str:status>/', LoanTotal, name='loan-total'),
    path('api/loan-summary/', loan_summary_api, name='loan_summary'),

    # Jari Ashkhas Moshtarian paths
    path('acc/jariashkhas/moshtari/<int:tafsili>', HesabMoshtariDetail, name='hesab-moshtari-detail'),
    path('acc/jariashkhas/moshtarian/detaile/<int:filter_id>', JariAshkhasMoshtarianDetail, name='jari_ashkhas_moshtarian_detail'),
    path('acc/jariashkhas/moshtarian/total', JariAshkhasMoshtarian, name='jari-ashkhas-moshtarian'),

    # Bedehkaran paths
    path('acc/bedehkaran/moshtarian/<state>', BedehkaranMoshtarian, name='bedehkaran-moshtarian'),

    # Cheques paths
    path('acc/cheques_recieve_total', ChequesRecieveTotal, name='cheques-recieve-total'),
    path('acc/cheques_pay_total', ChequesPayTotal, name='cheques-pay-total'),

    # Taraz Kol path
    path('acc/<col>/<moin>/<tafzili>', TarazKol, name='taraz-kol'),

    # Balance sheet paths
    path('balance-sheet-kol/', balance_sheet_kol, name='balance_sheet_kol'),
    path('balance-sheet-moin/<int:kol_code>/', balance_sheet_moin, name='balance_sheet_moin'),
    path('balance-sheet-tafsili/<int:kol_code>/<int:moin_code>/', balance_sheet_tafsili, name='balance_sheet_tafsili'),

    # Sanad Total path
    path('sanad_total/<kol_code>/<moin_code>/<tafzili_code>/', SanadTotal, name='sanad_total'),

    # path('dial/', dial_number, name='dial_number'),

    path('run-dial-script/', run_dial_script, name='run_dial_script'),
    path('stop-dialer/', stop_dialer, name='stop_dialer'),

]

from django.urls import path
from mahakupdate.views import Update_from_mahak, Kala_group, Updatedb, \
    UpdateFactor, UpdateKala, UpdateFactorDetail, Updateall, UpdateKardex, UpdatePerson, UpdateKalaGroupinfo, \
    CreateKalaGroup, UpdateKalaGroup, UpdateStorage, UpdateMojodi, Update_Sales_Mojodi_Ratio, UpdateSanad, \
    UpdateSanadDetail, UpdateAccCoding, Cheques_Recieve, UpdateSanadConditions, Cheque_Pay, UpdateBank, UpdateLoan, \
    UpdateLoanDetail, UpdateBedehiMoshtari, CompleLoan, UpdateMyCondition, UpdateBackFactor, UpdateBackFactorDetail, \
    DeleteDublicateData, AfterTakhfifKol, UpdateSleepInvestment, LoanBedehiMoshtari, UpdateGoodConsign, \
    UpdateBrandGroupinfo, CreateBrandsFromRules, UpdateKalaBrands

urlpatterns = [
    path('1', Update_from_mahak, name="update"),
    path('updatedb', Updatedb, name="updatedb"),
    path('updateall', Updateall, name="updateall"),

    path('update/factor', UpdateFactor, name="updatefactor"),
    path('update/backfactor', UpdateBackFactor, name="updatebackfactor"),
    path('update/factor-detail', UpdateFactorDetail, name="updatefactordetail"),
    path('update/back-factor-detail', UpdateBackFactorDetail, name="updatebackfactordetail"),
    path('update/kala', UpdateKala, name="updatekala"),
    path('update/storage', UpdateStorage, name="updatestorage"),
    path('update/person', UpdatePerson, name="updateperson"),
    path('update/kardex', UpdateKardex, name="updatekardex"),
    path('update/mojodi', UpdateMojodi, name="updatemojodi"),
    path('update/updatekalagroupinfo', UpdateKalaGroupinfo, name="updatekalagroupinfo"),
    path('update/createkalagroup', CreateKalaGroup, name="createkalagroup"),
    path('update/updatekalagroup', UpdateKalaGroup, name="updatekalagroup"),
    path('update/updatsmratio', Update_Sales_Mojodi_Ratio, name="update_sales_mojodi_ratio"),
    path('update/sanad', UpdateSanad, name="Update_Sanad"),
    path('update/sanaddetail', UpdateSanadDetail, name="Update_Sanad-Detail"),
    path('update/acccoding', UpdateAccCoding, name="Update_Sanad-Detail"),
    path('update/bank', UpdateBank, name="updatebank"),
    path('update/chequesrecieve', Cheques_Recieve, name="chequesrecieve"),
    path('update/chequepay', Cheque_Pay, name="chequepay"),
    path('update/updatemycondition', UpdateMyCondition, name="updatemycondition"),
    path('update/updatesanadconditions', UpdateSanadConditions, name="updatesanadconditions"),
    path('update/loan', UpdateLoan, name="updateloan"),
    path('update/loandetail', UpdateLoanDetail, name="updateloan-detail"),
    path('update/bedehimoshtari', UpdateBedehiMoshtari, name="update-bedehi-moshtari"),
    path('update/sleepinvestment', UpdateSleepInvestment, name="update-sleep-investment"),
    path('update/compleloan', CompleLoan, name="completloan"),
    path('update/delete_dublicate_data', DeleteDublicateData, name="delete-dublicate-data"),
    path('update/after_takhfif_kol', AfterTakhfifKol, name="after-takhfif-kol"),
    path('update/loan_bedehi_moshtari', LoanBedehiMoshtari, name="loan-bedehi-moshtari"),
    path('update/good_consign', UpdateGoodConsign, name="update-good-consign"),



    path('kalagroup', Kala_group, name="kala_group"),

    path('update/brand-rules', UpdateBrandGroupinfo, name='update_brand_rules'),
    path('update/brands-from-role', CreateBrandsFromRules, name='update_brands'),
    path('update/kala-brands', UpdateKalaBrands, name='update_kala_brands'),



]



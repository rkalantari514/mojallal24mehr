from django.urls import path

from mahakupdate.views import Update_from_mahak, Kala_group, category_create_view, kala_create_view, Updatedb, \
    UpdateFactor, UpdateKala, UpdateFactorDetail,Updateall,UpdateKardex

urlpatterns = [
    path('1', Update_from_mahak,name="update"),
    path('updatedb', Updatedb, name="updatedb"),
    path('updateall', Updateall, name="updateall"),

    path('update/factor', UpdateFactor, name="updatefactor"),
    path('update/factor-detail', UpdateFactorDetail, name="updatefactordetail"),
    path('update/kala', UpdateKala, name="updatekala"),
    path('update/kardex', UpdateKardex, name="updatekardex"),

    path('kalagroup', Kala_group,name="kala_group"),
    path('category/create/', category_create_view, name='category_create'),
    path('kala/create/', kala_create_view, name='kala_create'),


]


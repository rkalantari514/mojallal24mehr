from django.urls import path
from . import views, jobs
from mahakupdate.views import Update_from_mahak, Kala_group, category_create_view, kala_create_view, Updatedb, \
    UpdateFactor, UpdateKala, UpdateFactorDetail, Updateall, UpdateKardex, UpdatePerson, UpdateKalaGroupinfo, \
    CreateKalaGroup, UpdateKalaGroup, UpdateStorage, UpdateMojodi

urlpatterns = [
    path('1', Update_from_mahak, name="update"),
    # path('', Updatedb, name="updatedb"),
    path('updatedb', Updatedb, name="updatedb"),
    path('updateall', Updateall, name="updateall"),
    path('update/factor', UpdateFactor, name="updatefactor"),
    path('update/factor-detail', UpdateFactorDetail, name="updatefactordetail"),
    path('update/kala', UpdateKala, name="updatekala"),
    path('update/storage', UpdateStorage, name="updatestorage"),
    path('update/person', UpdatePerson, name="updateperson"),
    path('update/kardex', UpdateKardex, name="updatekardex"),
    path('update/mojodi', UpdateMojodi, name="updatemojodi"),
    path('update/updatekalagroupinfo', UpdateKalaGroupinfo, name="updatekalagroupinfo"),
    path('update/createkalagroup', CreateKalaGroup, name="createkalagroup"),
    path('update/updatekalagroup', UpdateKalaGroup, name="updatekalagroup"),

    path('kalagroup', Kala_group, name="kala_group"),
    path('category/create/', category_create_view, name='category_create'),
    path('kala/create/', kala_create_view, name='kala_create'),

]



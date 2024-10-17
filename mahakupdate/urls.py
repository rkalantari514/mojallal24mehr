from django.urls import path

from mahakupdate.views import Update_from_mahak, Kala_group, category_create_view, kala_create_view, Updatedb

urlpatterns = [
    path('1', Update_from_mahak,name="update"),
    path('updatedb', Updatedb, name="updatedb"),

    path('kalagroup', Kala_group,name="kala_group"),
    path('category/create/', category_create_view, name='category_create'),
    path('kala/create/', kala_create_view, name='kala_create'),


]


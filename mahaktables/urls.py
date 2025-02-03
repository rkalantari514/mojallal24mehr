from django.urls import path

from mahaktables.views import MTable, search_in_tables, list_tables, table_detail

urlpatterns = [
    path('mahaktables', MTable, name="mtables"),
    path('search/<str:search_text>/', search_in_tables, name='search_in_tables'),
    path('tables/', list_tables, name='list_tables'),
    path('tables/<str:table_name>/', table_detail, name='table_detail'),

]

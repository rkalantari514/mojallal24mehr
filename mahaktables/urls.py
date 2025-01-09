from django.urls import path

from mahaktables.views import MTables, search_in_tables

urlpatterns = [
    path('mahaktables', MTables,name="mtables"),
    path('search/<str:search_text>/', search_in_tables, name='search_in_tables'),

]


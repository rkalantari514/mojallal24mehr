from django.urls import path
from .views import DsshKala, TotalKala, load_categories_level2, load_categories_level3,DetailKala
from mahaktables.views import MTables
from django.shortcuts import redirect
urlpatterns = [
    path('dash/kala', DsshKala, name='dssh_kala'),

    path('', lambda request: redirect('/dash/kala/total/all/all/all/all/total', permanent=True)),
    path('dash/kala/total/<st>/<cat1>/<cat2>/<cat3>/<total>', TotalKala, name='total_kala'),



    path('dash/kala/detail/<code>', DetailKala, name='detailkala'),







    # Ajax
    path('ajax/load-categories-level2/', load_categories_level2, name='ajax_load_categories_level2'),  # AJAX برای سطح 2
    path('ajax/load-categories-level3/', load_categories_level3, name='ajax_load_categories_level3'),  # AJAX برای سطح 3
]

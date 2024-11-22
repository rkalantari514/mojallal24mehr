from django.urls import path
from .views import DsshKala, TotalKala, load_categories_level2, load_categories_level3
from mahaktables.views import MTables
from django.shortcuts import redirect
urlpatterns = [
    path('dash/kala', DsshKala, name='dssh_kala'),

    path('', lambda request: redirect('/dash/kala/total/12/all/all/all/', permanent=True)),
    path('dash/kala/total/<st>/<cat1>/<cat2>/<cat3>/', TotalKala, name='total_kala'),

    # Ajax
    path('ajax/load-categories-level2/', load_categories_level2, name='ajax_load_categories_level2'),  # AJAX برای سطح 2
    path('ajax/load-categories-level3/', load_categories_level3, name='ajax_load_categories_level3'),  # AJAX برای سطح 3
]

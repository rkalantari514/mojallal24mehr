from django.urls import path
from .views import DsshKala, TotalKala, load_categories_level2, load_categories_level3
from mahaktables.views import MTables

urlpatterns = [
    path('dash/kala', DsshKala, name='dssh_kala'),
    path('dash/kala/total', TotalKala, name='totalkala'),

    # Ajax
    path('ajax/load-categories-level2/', load_categories_level2, name='ajax_load_categories_level2'),  # AJAX برای سطح 2
    path('ajax/load-categories-level3/', load_categories_level3, name='ajax_load_categories_level3'),  # AJAX برای سطح 3
]


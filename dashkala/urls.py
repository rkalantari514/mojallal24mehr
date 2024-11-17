from django.urls import path
from .views import DsshKala, TotalKala, load_categories, filter_kardex
from mahaktables.views import MTables

urlpatterns = [
    path('dash/kala', DsshKala, name='dssh_kala'),
    path('dash/kala/total', TotalKala, name='totalkala'),
    path('load_categories/', load_categories, name='load_categories'),
    path('filter_kardex/', filter_kardex, name='filter_kardex'),  # مسیر برای فیلتر کردن کاردکس
]

from django.urls import path

from custom_login.views import log_out, login_view, forgot_password_view, dashboard_view

urlpatterns = [

    path('logout/', log_out, name='logout'),
    path('login/', login_view, name='login'),
    path('forgot-password/', forgot_password_view, name='forgot_password'),
    path('v1', dashboard_view, name='dashboard'),
    # path('', views.register_view, name='register_view'),
    # path('verify/', views.verify, name='verify'),
    # path('dashboard/', views.dashboard, name='dashboard'),
]

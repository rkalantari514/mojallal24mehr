"""
URL configuration for mojal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from mahakupdate.views import Updateall
from mojallal24mehr import settings
from mojallal24mehr.views import header, sidebar, footer, update_dark_mode

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('', include('mahaktables.urls')),
    path('', include('mahakupdate.urls')),
    path('', include('dashkala.urls')),
    path('', include('custom_login.urls')),
    path('', include('accounting.urls')),
    path('', include('payment.urls')),
    path('', include('festival.urls')),
    path('', include('budget.urls')),

    path('update-dark-mode/', update_dark_mode, name='update_dark_mode'),

    path('header', header, name="header"),
    path('sidebar', sidebar, name="sidebar"),
    path('footer', footer, name="footer"),

    path('fake-path/', Updateall, name='update_all'),  # مسیر را به درستی تنظیم کنید

]







# برای فایل های استاتیک
if settings.DEBUG:
    # add root static files
    urlpatterns = urlpatterns + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # add media static files
    urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

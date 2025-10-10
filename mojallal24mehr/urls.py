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
from mojallal24mehr.views import header, sidebar, footer, update_dark_mode, dev_static

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.views.static import serve
import django
import os
# Static and media must come first to avoid being shadowed by greedy app URL patterns
_admin_static_root = os.path.join(os.path.dirname(django.__file__), 'contrib', 'admin', 'static')
static_urlpatterns = [
    # Django admin static (serve even without collectstatic)
    re_path(r'^%s(?P<path>admin/.*)$' % settings.STATIC_URL.lstrip('/'), dev_static, {
        'root': _admin_static_root,
    }),
    # assets first (project assets)
    re_path(r'^%s(?P<path>.*)$' % settings.STATIC_URL.lstrip('/'), dev_static, {
        'root': os.path.join(str(settings.BASE_DIR), 'assets'),
    }),
    # then STATIC_ROOT (if collected)
    re_path(r'^%s(?P<path>.*)$' % settings.STATIC_URL.lstrip('/'), dev_static, {
        'root': settings.STATIC_ROOT,
    }),
    # media
    re_path(r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'), dev_static, {
        'root': settings.MEDIA_ROOT,
    }),
]

urlpatterns = static_urlpatterns + [
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
    path('events/', include('events.urls')),
    path('jariashkhas/', include('jariashkhas.urls')),

    path('update-dark-mode/', update_dark_mode, name='update_dark_mode'),

    path('header', header, name="header"),
    path('sidebar', sidebar, name="sidebar"),
    path('footer', footer, name="footer"),

    path('fake-path/', Updateall, name='update_all'),  # مسیر را به درستی تنظیم کنید
]

# Custom error handlers
handler404 = 'mojallal24mehr.views.handle_404_error'
handler500 = 'mojallal24mehr.views.handle_500_error'



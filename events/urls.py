# events/urls.py

from django.urls import path
from . import views

app_name = 'events' # نام اپلیکیشن برای استفاده در تگ url

urlpatterns = [
    # EventCategory URLs
    path('categories/', views.EventCategoryListView.as_view(), name='category_list'),
    path('categories/add/', views.EventCategoryCreateView.as_view(), name='category_add'),
    path('categories/<int:pk>/edit/', views.EventCategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.EventCategoryDeleteView.as_view(), name='category_delete'),

    # Event URLs
    path('', views.EventListView.as_view(), name='event_list'), # لیست اصلی رویدادها
    path('add/', views.EventCreateView.as_view(), name='event_add'),
    path('<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('<int:pk>/edit/', views.EventUpdateView.as_view(), name='event_edit'),
    path('<int:pk>/delete/', views.EventDeleteView.as_view(), name='event_delete'),

    # EventDetail URLs (جزئیات برگزاری یک رویداد خاص)
    # اینها معمولا از طریق صفحه EventDetail یا EventEdit مدیریت می شوند
    # اما برای دسترسی مستقیم هم می توانیم تعریف کنیم

    path('details/<int:pk>/', views.EventDetailDetailView.as_view(), name='event_detail_detail'),
    path('details/<int:pk>/delete/', views.EventDetailDeleteView.as_view(), name='event_detail_delete'),


    path('<int:event_pk>/details/add/', views.EventDetailCreateView.as_view(), name='event_detail_add'),
    path('details/<int:pk>/edit/', views.EventDetailUpdateView.as_view(), name='event_detail_edit'),

# اضافه کردن این خط در لیست urlpatterns
    path('upcoming/', views.UpcomingEventDetailsListView.as_view(), name='upcoming_event_details'),
# events/urls.py
    path('resolutions/', views.ResolutionListView.as_view(), name='resolutions'),

    # Resolution URLs (مصوبات) - معمولا به صورت Inline مدیریت می شوند
    # اما اگر نیاز به مدیریت جداگانه دارید، می توانید اضافه کنید.
    # فعلاً به صورت جداگانه تعریف نمی کنیم چون Inline Formset ها را داریم.

    # EventImage URLs (تصاویر) - معمولا به صورت Inline مدیریت می شوند
    # فعلاً به صورت جداگانه تعریف نمی کنیم چون Inline Formset ها را داریم.
]
from django.urls import path
from .views import DsshKala
from mahaktables.views import MTables

urlpatterns = [
    # path('dash/kala', DsshKala,name="dashkala"),
    path('dash/kala', DsshKala, name='dssh_kala'),  # اطمینان از درست بودن نام

]


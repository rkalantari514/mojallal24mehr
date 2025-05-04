from django.urls import path
from .views import request_payment, payment_callback

urlpatterns = [
    path("payment/request/", request_payment, name="request_payment"),
    path("payment/callback/", payment_callback, name="payment_callback"),
]


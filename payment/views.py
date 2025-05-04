from django.contrib.sites import requests
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect

from mojallal24mehr import settings
from mojallal24mehr.settings import BEHPARDAKHT_TERMINAL_ID, BEHPARDAKHT_USERNAME, BEHPARDAKHT_PASSWORD, \
    BEHPARDAKHT_MERCHANT_ID
from .payment import BehpardakhtMellat

response_codes = {
    "0": "تراکنش تأیید شد",
    "11": "شماره کارت نامعتبر است",
    "12": "موجودی کافی نیست",
    "13": "رمز نادرست است",
    "14": "حداکثر تعداد تلاش برای وارد کردن رمز عبور انجام شده",
    "17": "لغو توسط مشتری",
    "18": "کارت منقضی شده است",
    "421": "آی‌پی نامعتبر است، با پشتیبانی بانک تماس بگیرید",
    # و سایر کدهای خطا...
}

def request_payment(request):
    """ ارسال درخواست پرداخت """
    if request.method == "POST":
        order_id = 12345  # باید مقدار یونیک باشد
        amount = 100000  # مبلغ به ریال
        callback_url = "http://yourdomain.com/payment/callback/"

        payment_gateway = BehpardakhtMellat(
            settings.BEHPARDAKHT_TERMINAL_ID,
            settings.BEHPARDAKHT_USERNAME,
            settings.BEHPARDAKHT_PASSWORD,
            settings.BEHPARDAKHT_MERCHANT_ID
        )
        response = payment_gateway.send_payment_request(order_id, amount, callback_url)

        if response.get("status") == "Success":
            return redirect(response.get("payment_url"))

    return render(request, "payment_form.html")


def payment_callback(request):
    """ بررسی وضعیت تراکنش پس از بازگشت کاربر """
    res_code = request.GET.get("ResCode")  # کد وضعیت تراکنش
    sale_ref_id = request.GET.get("SaleReferenceId")  # شناسه تراکنش

    if res_code == "0":
        message = "پرداخت با موفقیت انجام شد."
    else:
        error_message = response_codes.get(res_code, "خطای نامشخص")
        message = f"پرداخت ناموفق: {error_message}"

    return render(request, "payment_status.html", {"message": message})


def verify_payment(order_id, sale_order_id, sale_ref_id):
    """ بررسی وضعیت پرداخت """
    data = {
        "terminalId": settings.BEHPARDAKHT_TERMINAL_ID,
        "userName": settings.BEHPARDAKHT_USERNAME,
        "userPassword": settings.BEHPARDAKHT_PASSWORD,
        "orderId": order_id,
        "saleOrderId": sale_order_id,
        "saleReferenceId": sale_ref_id
    }

    response = requests.post(f"{settings.BEHPARDAKHT_URL}/VerifyTransaction", json=data)

    if response.status_code == 200 and response.text == "0":
        return "تراکنش تأیید شد."
    else:
        return f"خطای تأیید تراکنش: {response.text}"

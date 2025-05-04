import requests


from django.conf import settings

class BehpardakhtMellat:
    def __init__(self, terminal_id, username, password, merchant_id):
        self.terminal_id = terminal_id
        self.username = username
        self.password = password
        self.merchant_id = merchant_id
        self.base_url = "https://bpm.shaparak.ir/pgwchannel/services"


    def send_payment_request(self, order_id, amount, callback_url):
        """ ارسال درخواست پرداخت به درگاه ملت """
        data = {
            "terminalId": self.terminal_id,
            "userName": self.username,
            "userPassword": self.password,
            "orderId": order_id,
            "amount": amount,
            "callBackUrl": callback_url
        }
        response = requests.post(f"{self.base_url}/PaymentRequest", json=data)
        return response.json()

    def verify_payment(self, order_id, ref_id):
        """ بررسی وضعیت پرداخت پس از بازگشت کاربر """
        data = {
            "terminalId": self.terminal_id,
            "userName": self.username,
            "userPassword": self.password,
            "orderId": order_id,
            "refId": ref_id
        }
        response = requests.post(f"{self.base_url}/VerifyTransaction", json=data)
        return response.json()

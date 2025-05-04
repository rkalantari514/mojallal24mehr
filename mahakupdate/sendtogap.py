import requests
import time

from django.utils.translation.trans_null import activate

from dashboard.models import MasterInfo


def send_to_admin(data):
    try:
        myparams = {
            'chat_id': '+989151006447',
            'type': 'text',
            'data': data,
            'reply_keyboard': None,
            'inline_keyboard': None,
            'form': None,
        }
        myheader = {
            'token': 'e55bcc5a1e961e9cba1d131de91d2b4aa2a7fa7ea68ad8f44dfe687986dba690'
        }
        print(data)
        response = requests.post('https://api.gap.im/sendMessage/', data=myparams, headers=myheader)
        print(response)


    except:
        print('can not send to gap')

def send_to_admin1(data):
    try:
        myparams = {
            'chat_id': '+989151006447',
            'type': 'text',
            'data': data,
            'reply_keyboard': None,
            'inline_keyboard': None,
            'form': None,
        }
        myheader = {
            'token': 'e55bcc5a1e961e9cba1d131de91d2b4aa2a7fa7ea68ad8f44dfe687986dba690'
        }
        print(data)
        response = requests.post('https://api.gap.im/sendMessage/', data=myparams, headers=myheader)
        print(response)
        return response  # برگرداندن پاسخ
    except Exception as e:
        print('can not send to gap:', e)
        return None  # برگرداندن مقدار None در صورت بروز خطا


def send_to_managers(mobiles,data):
    print(mobiles)
    for m in mobiles:
        m = m[1:]
        m=f'+98{m}'
        print(m)
        try:
            myparams = {
                'chat_id': m,
                'type': 'text',
                'data': data,
                'reply_keyboard': None,
                'inline_keyboard': None,
                'form': None,
            }
            myheader = {
                'token': 'a9827aaae459d060d8ca68f0be07f58f1b39eebe29f457da25f2ceed731ddbf1'
            }
            print(data)
            response = requests.post('https://api.gap.im/sendMessage/', data=myparams, headers=myheader)
            print(response)

        except:
            print(f'can not send to gap to:{m}')

        time.sleep(3)  # برنامه به مدت 5 ثانیه متوقف می‌شود


import requests



# def send_sms(phone_number, message):
#     url = "https://api2.ippanel.com/api/v1/sms/send"
#     headers = {
#         "Authorization": f"Bearer {ip_panel_token}",
#         "Content-Type": "application/json"
#     }
#     data = {
#         "recipient": phone_number,
#         "message": message,
#         "sender": "3000505"
#     }
#
#     response = requests.post(url, json=data, headers=headers)
#
#     # بررسی وضعیت درخواست
#     if response.status_code != 200:
#         print(f"Error: {response.status_code}, Response: {response.text}")
#         return None
#
#     try:
#         return response.json()
#     except requests.exceptions.JSONDecodeError:
#         print("Error: Invalid JSON response received from API")
#         return None



ip_panel_token=MasterInfo.objects.filter(is_active=True).last().ip_panel_token

import requests

import requests

# def send_sms(phone_number, message):
#     url = "https://api2.ippanel.com/api/v1/sms/send/webservice/single"
#     headers = {
#         "accept": "application/json",
#         "apikey": ip_panel_token,  # فقط مقدار API Key، بدون "Bearer"
#         "Content-Type": "application/json"
#     }
#     data = {
#         "recipient": [phone_number],
#         "sender": "+983000505",
#         "message": message
#     }
#
#     response = requests.post(url, json=data, headers=headers)
#     print('response')
#     print(response.json())
#
#     if response.status_code == 200:
#         return response.json()
#     else:
#         print(f"Error: {response.status_code}, Response: {response.text}")
#         return None

import requests

import requests

def send_sms(phone_number, message):
    url = "https://api2.ippanel.com/api/v1/sms/send/webservice/single"
    headers = {
        "accept": "application/json",
        "apikey": ip_panel_token,
        "Content-Type": "application/json"
    }
    data = {
        "recipient": [phone_number],
        # "sender": "+983000505",
        "sender": "+9890002741",
        "message": message
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        return response_data.get("data", {}).get("message_id", None)  # بازگرداندن `message_id`
    else:
        print(f"Error: {response.status_code}, Response: {response.text}")
        return None



import requests


import requests

def check_sms_status(message_id):
    print('message_id',message_id)
    url = f"https://api2.ippanel.com/api/v1/sms/message/show-recipient/message-id/{message_id}?page=1&per_page=10"
    headers = {
        "accept": "application/json",
        "apikey": ip_panel_token  # فقط مقدار API Key
    }

    response = requests.get(url, headers=headers)
    print('response.json()')
    print(response.json())
    print('++++++++++++++++')
    if response.status_code == 200:
        data = response.json()

        if "data" in data and "deliveries" in data["data"]:
            status_code = data["data"]["deliveries"][0]["status"]
            print('status_code')
            print(status_code)

            if isinstance(status_code, int):  # بررسی اینکه مقدار عددی است
                return status_code

        return None  # مقدار `None` برمی‌گرداند تا ذخیره نشود
    else:
        print(f"Error: {response.status_code}, Response: {response.text}")
        return None  # مقدار `None` به جای متن خطا برمی‌گردد




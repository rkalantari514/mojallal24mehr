import requests
import time

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

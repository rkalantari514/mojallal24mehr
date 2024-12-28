import requests


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
        response = requests.post('https://api.gap.im/sendMessage/', data=myparams, headers=myheader)

    except:
        print('can not send to gap')


def send_to_managers(data):
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
            'token': 'a9827aaae459d060d8ca68f0be07f58f1b39eebe29f457da25f2ceed731ddbf1'
        }
        response = requests.post('https://api.gap.im/sendMessage/', data=myparams, headers=myheader)

    except:
        print('can not send to gap')

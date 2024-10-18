import requests
import json

api_key = 'waka_caff199c-a0d5-4792-81b1-d51995b29e3d'
url = 'https://api.waketime.com/v1/data'

headers = {
    'Authorization': f'Bearer {api_key}'
}

response = requests.get(url, headers=headers,timeout=20)

if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2))
else:
    print('Failed to retrieve data:', response.status_code)

import time
from django.http import HttpResponse
from django.views import View


class CombinedView(View):
    def get(self, request, *args, **kwargs):
        response_one = ViewOne.as_view()(request, *args, **kwargs)
        time.sleep(5)  # Pause for 5 seconds
        response_two = ViewTwo.as_view()(request, *args, **kwargs)
        time.sleep(5)  # Pause for 5 seconds
        response_three = ViewThree.as_view()(request, *args, **kwargs)

        # Combine the responses
        combined_content = response_one.content + b'\n' + response_two.content + b'\n' + response_three.content
        return HttpResponse(combined_content)


import requests
import json

api_key = 'waka_caff199c-a0d5-4792-81b1-d51995b29e3d'
url = 'https://api.waketime.com/v1/data'

headers = {
    'Authorization': f'Bearer {api_key}'
}

response = requests.get(url, headers=headers, timeout=20)

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

< div


class ="fixed-table-body" >

< div


class ="fixed-table-loading table table-bordered table-hover" style="top: 84.625px;" >

< span


class ="loading-wrap" >

< span


class ="loading-text" > در حال بارگذاری, لطفا صبر کنید < / span >

< span


class ="animation-wrap" > < span class ="animation-dot" > < / span > < / span >

< / span >

< / div >
< table
id = "table"


class ="table-striped table table-bordered table-hover" data-toggle="table" data-locale="fa-IR" data-search="true" data-show-columns="true" data-show-export="true" data-show-refresh="true" data-show-columns-toggle-all="true" data-show-pagination-switch="true" data-show-toggle="true" data-show-fullscreen="true" data-buttons="buttons" data-search-align="left" data-buttons- class ="primary" data-pagination="true" data-show-columns-search="true" data-show-footer="true" data-page-size="50" data-remember-order="true" data-sortable="true" data-show-search-clear-button="true" data-sort-name="kambod" data-sort-order="desc" data-filter-control="true" data-show-print="true" data-export-footer="true" data-export-data-type="all" data-export-types="['excel']" >

< thead > < tr


class ="tr-class-1" > < th class ="card-text text-center" style="vertical-align: middle; " data-field="sal" > < div class ="th-inner sortable both" >


سال
مالی
< / div > < div


class ="fht-cell" > < div class ="filter-control" > < select class ="form-control bootstrap-table-filter-control-sal " style="width: 100%;" dir="ltr" > < option value="" > < / option > < option value="1402" > 1402 < / option > < option value="1400" > 1400 < / option > < option value="1401" > 1401 < / option > < option value="1403" > 1403 < / option > < / select > < / div > < / div > < / th > < th class ="card-text text-center" style="vertical-align: middle; " data-field="sharh" > < div class ="th-inner sortable both" > شرح ردیف

< / div > < div


class ="fht-cell" > < div class ="filter-control" > < input type="search" class ="form-control bootstrap-table-filter-control-sharh search-input" style="width: 100%;" placeholder="" value="" > < / div > < / div > < / th > < th class ="card-text text-center" style="vertical-align: middle; " data-field="product" > < div class ="th-inner sortable both" > بودجه در پارتی

< / div > < div


class ="fht-cell" > < div class ="filter-control" > < input type="search" class ="form-control bootstrap-table-filter-control-product search-input" style="width: 100%;" placeholder="" value="" > < / div > < / div > < / th > < th class ="card-text text-center" style="vertical-align: middle; " data-field="star" > < div class ="th-inner sortable both" > *

< / div > < div


class ="fht-cell" > < div class ="filter-control" > < select class ="form-control bootstrap-table-filter-control-star " style="width: 100%;" dir="ltr" > < option value="" > < / option > < option value="1" > 1 < / option > < / select > < / div > < / div > < / th > < th class ="card-text text-center" style="" data-field="4" > < div class ="th-inner sortable both" >


آخرین
بودجه
مصوب
< / div > < div


class ="fht-cell" > < div class ="no-filter-control" > < / div > < / div > < / th > < th class ="card-text text-center" style="" data-field="5" > < div class ="th-inner sortable both" >


مانده
اعتبار
مصوب
< / div > < div


class ="fht-cell" > < div class ="no-filter-control" > < / div > < / div > < / th > < th class ="card-text text-center" style="" data-field="6" > < div class ="th-inner sortable both" >



تامین
اعتبار
شده
< / div > < div


class ="fht-cell" > < div class ="no-filter-control" > < / div > < / div > < / th > < th class ="card-text text-center" style="" data-field="7" > < div class ="th-inner sortable both" >
تخصیص
صادر
شده
< / div > < div



class ="fht-cell" > < div class ="no-filter-control" > < / div > < / div > < / th > < th class ="card-text text-center" style="" data-field="8" > < div class ="th-inner sortable both" >


تخصیص
فنی
و
عمرانی
< / div > < div


class ="fht-cell" > < div class ="no-filter-control" > < / div > < / div > < / th > < th class ="card-text text-center" style="" data-field="9" > < div class ="th-inner sortable both" >


علی
الحساب
تائید
شده
< / div > < div


class ="fht-cell" > < div class ="no-filter-control" > < / div > < / div > < / th > < th class ="card-text text-center" style="" data-field="10" > < div class ="th-inner sortable both" >


در
حال
ممیزی
< / div > < div


class ="fht-cell" > < div class ="no-filter-control" > < / div > < / div > < / th > < th class ="card-text text-center" style="" data-field="11" > < div class ="th-inner sortable both" >


ممیزی
شده
بدون
تخصیص
< / div > < div


class ="fht-cell" > < div class ="no-filter-control" > < / div > < / div > < / th > < th class ="card-text text-center" style="" data-field="12" > < div class ="th-inner sortable both" >


مانده
سقف
< / div > < div


class ="fht-cell" > < div class ="no-filter-control" > < / div > < / div > < / th > < / tr > < / thead >

< tbody > < tr
data - index = "0" > < td


class ="card-text text-center" style="vertical-align: middle; " > < h6 > 1402 < / h6 > < / td > < td class ="card-text text-center" style="vertical-align: middle; " > < h6 > پروژه احداث آشپزخانه مرکزی < / h6 > < / td > < td class ="card-text text-center" style="vertical-align: middle; " > < h6 > پروژه احداث آشپزخانه مرکزي < / h6 > < / td > < td class ="card-text text-center" style="vertical-align: middle; " > < h6 > 1 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 1, 040, 217, 326, 607 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 75, 267, 003, 509 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 964, 950, 323, 098 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 905, 510, 126, 147 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 774, 529, 810, 406 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 301, 006, 002, 793 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 3, 925, 425, 641 < / h6 > < / td > < td class ="card-text text-center" > < h6 > None < / h6 > < / td > < td class ="card-text text-center" > < h6 > 14, 201, 053, 058 < / h6 > < / td > < / tr > < tr data-index="1" > < td class ="card-text text-center" style="vertical-align: middle; " > < h6 > 1400 < / h6 > < / td > < td class ="card-text text-center" style="vertical-align: middle; " > < h6 > پروژه احداث آشپزخانه مرکزی < / h6 > < / td > < td class ="card-text text-center" style="vertical-align: middle; " > < h6 > پروژه احداث آشپزخانه مرکزي < / h6 > < / td > < td class ="card-text text-center" style="vertical-align: middle; " > < h6 > 1 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 450, 000, 000, 000 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 271, 396, 436, 347 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 178, 603, 563, 653 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 51, 854, 910, 997 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 52, 543, 027, 497 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 50, 000, 000, 000 < / h6 > < / td > < td class ="card-text text-center" > < h6 > None < / h6 > < / td > < td class ="card-text text-center" > < h6 > None < / h6 > < / td > < td class ="card-text text-center" > < h6 > 52, 956, 203, 188 < / h6 > < / td > < / tr > < tr data-index="2" > < td class ="card-text text-center" style="vertical-align: middle; " > < h6 > 1401 < / h6 > < / td > < td class ="card-text text-center" style="vertical-align: middle; " > < h6 > پروژه احداث آشپزخانه مرکزی < / h6 > < / td > < td class ="card-text text-center" style="vertical-align: middle; " > < h6 > پروژه احداث آشپزخانه مرکزي < / h6 > < / td > < td class ="card-text text-center" style="vertical-align: middle; " > < h6 > 1 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 1, 550, 000, 000, 000 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 704, 924, 619, 724 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 845, 075, 380, 276 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 686, 214, 423, 190 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 686, 214, 423, 190 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 819, 623, 463, 583 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 41, 526, 451, 583 < / h6 > < / td > < td class ="card-text text-center" > < h6 > None < / h6 > < / td > < td class ="card-text text-center" > < h6 > 49, 884, 177, 069 < / h6 > < / td > < / tr > < tr data-index="3" > < td class ="card-text text-center" style="vertical-align: middle; " > < h6 > 1403 < / h6 > < / td > < td class ="card-text text-center" style="vertical-align: middle; " > < h6 > پروژه احداث آشپزخانه مرکزی < / h6 > < / td > < td class ="card-text text-center" style="vertical-align: middle; " > < h6 > پروژه احداث آشپزخانه مرکزي < / h6 > < / td > < td class ="card-text text-center" style="vertical-align: middle; " > < h6 > 1 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 490, 000, 000, 000 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 100, 612, 146, 329 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 389, 387, 853, 671 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 323, 789, 772, 578 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 24, 225, 899, 954 < / h6 > < / td > < td class ="card-text text-center" > < h6 > None < / h6 > < / td > < td class ="card-text text-center" > < h6 > 9, 822, 142, 154 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 80, 159, 887, 565 < / h6 > < / td > < td class ="card-text text-center" > < h6 > 10, 612, 146, 329 < / h6 > < / td > < / tr > < / tbody >

< tfoot
style = "margin-right: 0px;" > < tr > < th


class ="card-text text-center" style="vertical-align: middle; " > < div class ="th-inner" > < / div > < div class ="fht-cell" style="width: 65.7656px;" > < / div > < / th > < th class ="card-text text-center" style="vertical-align: middle; " > < div class ="th-inner" > < / div > < div class ="fht-cell" style="width: 74.5938px;" > < / div > < / th > < th class ="card-text text-center" style="vertical-align: middle; " > < div class ="th-inner" > < / div > < div class ="fht-cell" style="width: 95.2344px;" > < / div > < / th > < th class ="card-text text-center" style="vertical-align: middle; " > < div class ="th-inner" > < / div > < div class ="fht-cell" style="width: 25.6406px;" > < / div > < / th > < th class ="card-text text-center" style="" > < div class ="th-inner" > $NaN < / div > < div class ="fht-cell" style="width: 121.703px;" > < / div > < / th > < th class ="card-text text-center" style="" > < div class ="th-inner" > < / div > < div class ="fht-cell" style="width: 114.578px;" > < / div > < / th > < th class ="card-text text-center" style="" > < div class ="th-inner" > < / div > < div class ="fht-cell" style="width: 119.438px;" > < / div > < / th > < th class ="card-text text-center" style="" > < div class ="th-inner" > < / div > < div class ="fht-cell" style="width: 122.25px;" > < / div > < / th > < th class ="card-text text-center" style="" > < div class ="th-inner" > < / div > < div class ="fht-cell" style="width: 129.469px;" > < / div > < / th > < th class ="card-text text-center" style="" > < div class ="th-inner" > < / div > < div class ="fht-cell" style="width: 133.766px;" > < / div > < / th > < th class ="card-text text-center" style="" > < div class ="th-inner" > < / div > < div class ="fht-cell" style="width: 106.438px;" > < / div > < / th > < th class ="card-text text-center" style="" > < div class ="th-inner" > < / div > < div class ="fht-cell" style="width: 152.922px;" > < / div > < / th > < th class ="card-text text-center" style="" > < div class ="th-inner" > < / div > < div class ="fht-cell" style="width: 101.594px;" > < / div > < / th > < / tr > < / tfoot > < / table > < / div >

import time

from django.shortcuts import render

from custom_login.models import UserLog
from custom_login.views import page_permision
from dashboard.models import MasterInfo
from mahakupdate.models import SanadDetail, AccCoding

# Create your views here.








import time
from django.shortcuts import render, redirect
from django.db.models import Sum, Max, Min, Count, F, Case, When, DecimalField, Q
from django.db.models.functions import Coalesce
from custom_login.views import page_permision


def JariAshkasList(request, *args, **kwargs):
    name = 'لیست مطالبات و بدهی ها'
    result = page_permision(request, name)
    if result:
        return result

    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='لیست مطالبات و بدهی ها', code=0)

    start_time = time.time()

    context = {
        'title': 'لیست مطالبات و بدهی ها',
        'user': user,
        'table1': [],
    }

    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year

    sanads = SanadDetail.objects.filter(kol=103, acc_year=acc_year)

    # --------------------------------------------------------------------------
    # بخش بهینه شده:
    # `total_bed` و `total_bes` از اینجا حذف شدند، زیرا ملاک نهایی `total_curramount` است.
    # --------------------------------------------------------------------------
    tafzili_aggregates = sanads.values('moin', 'tafzili').annotate(
        total_curramount=Coalesce(Sum('curramount'), 0, output_field=DecimalField()),
        num_transactions=Count('id'),
        max_curramount=Coalesce(Max('curramount'), 0, output_field=DecimalField()),
        min_curramount=Coalesce(Min('curramount'), 0, output_field=DecimalField()),
    ).order_by('moin', 'tafzili')

    # --------------------------------------------------------------------------
    # گام 2: ساختاردهی خروجی برای تمپلیت (جدول نهایی)
    # --------------------------------------------------------------------------
    table1 = []
    current_moein_code = None
    moein_data = None

    for entry in tafzili_aggregates:
        moein_code = entry['moin']
        tafzili_code = entry['tafzili']
        total_curramount = entry['total_curramount']
        num_transactions = entry['num_transactions']
        max_curramount = entry['max_curramount']
        min_curramount = entry['min_curramount']

        if moein_code != current_moein_code:
            if moein_data:
                table1.append(moein_data)

            moein_name_obj = AccCoding.objects.filter(parent__code=103,code=moein_code, level=2).first()
            moein_name = moein_name_obj.name if moein_name_obj else f"نامعلوم ({moein_code})"
            current_moein_code = moein_code

            moein_data = {
                'moein_code': moein_code,
                'moein_name': moein_name,
                'total_positive_balance': 0,
                'total_negative_balance': 0,
                'num_debtors': 0,
                'num_creditors': 0,
                'max_overall_debt': None,
                'min_overall_credit': None,
                'tafzilis': []
            }

        tafzili_name_obj = AccCoding.objects.filter(parent__parent__code=103,parent__code=moein_code,code=tafzili_code, level=3).first()
        tafzili_name = tafzili_name_obj.name if tafzili_name_obj else f"نامعلوم ({tafzili_code})"

        if total_curramount > 0:
            moein_data['total_positive_balance'] += total_curramount
            moein_data['num_debtors'] += 1
            if moein_data['max_overall_debt'] is None or total_curramount > moein_data['max_overall_debt']:
                moein_data['max_overall_debt'] = total_curramount
        elif total_curramount < 0:
            moein_data['total_negative_balance'] += total_curramount
            moein_data['num_creditors'] += 1
            if moein_data['min_overall_credit'] is None or total_curramount < moein_data['min_overall_credit']:
                moein_data['min_overall_credit'] = total_curramount

        moein_data['tafzilis'].append({
            'tafzili_code': tafzili_code,
            'tafzili_name': tafzili_name,
            'total_curramount': total_curramount,
            'num_transactions': num_transactions,
            'max_curramount': max_curramount,
            'min_curramount': min_curramount,
            'is_debtor': total_curramount > 0,
            'is_creditor': total_curramount < 0,
        })

    if moein_data:
        table1.append(moein_data)

    context['table1'] = table1

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'ashkas-total.html', context)
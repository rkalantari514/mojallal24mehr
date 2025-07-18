import time
from decimal import Decimal

from django.shortcuts import render
from openpyxl.styles.builtins import title

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


def JariAshkasList(request,km,moin, *args, **kwargs):
    start_time = time.time()
    name = 'لیست مطالبات و بدهی ها'
    result = page_permision(request, name)
    if result:
        return result

    user = request.user
    if user.mobile_number != '09151006447':
        if km=='k':
            UserLog.objects.create(user=user, page='لیست مطالبات و بدهی ها', code=0)
        elif km=='m':
            UserLog.objects.create(user=user, page='لیست مطالبات و بدهی ها', code=moin)
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year

    context = {
        'title': 'لیست مطالبات و بدهی ها',
        'user': user,
        'acc_year': acc_year,
        'table1': [],
        'master_data': [],
        'is_kol': True,
        'm_code': None,
    }

    if km=='k':
        sanads = SanadDetail.objects.filter(kol=103, acc_year=acc_year)

        tafzili_aggregates = sanads.values('moin', 'tafzili').annotate(
            total_curramount=Coalesce(Sum('curramount'), 0, output_field=DecimalField()),
            num_transactions=Count('id'),
            max_curramount=Coalesce(Max('curramount'), 0, output_field=DecimalField()),
            min_curramount=Coalesce(Min('curramount'), 0, output_field=DecimalField()),
        ).order_by('moin', 'tafzili')


        table1 = []
        current_moein_code = None
        moein_data = None

        for entry in tafzili_aggregates:
            moein_code = entry['moin']
            total_curramount = entry['total_curramount']

            if moein_code != current_moein_code:
                if moein_data:
                    table1.append(moein_data)

                moein_name_obj = AccCoding.objects.filter(parent__code=103, code=moein_code, level=2).first()
                moein_name = moein_name_obj.name if moein_name_obj else f"نامعلوم ({moein_code})"
                current_moein_code = moein_code

                moein_data = {
                    'code': moein_code,
                    'name': moein_name,
                    'total_positive_balance': 0,
                    'total_negative_balance': 0,
                    'num_debtors': 0,
                    'num_creditors': 0,
                    'max_overall_debt': None,
                    'min_overall_credit': None,
                }

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


        if moein_data:
            table1.append(moein_data)
        context['table1'] = table1


    if km=='m':

        moein_code=moin
        moein_name_obj = AccCoding.objects.filter(parent__code=103, code=moein_code, level=2).first()
        moein_name = moein_name_obj.name if moein_name_obj else f"نامعلوم ({moein_code})"
        context['title']= f'مطالبات و بدهی معین {moein_name}'
        context['is_kol']= False
        context['m_code']= moein_code
        sanads = SanadDetail.objects.filter(kol=103,moin=moein_code, acc_year=acc_year)

        sanad_aggregates = sanads.values('tafzili').annotate(
            total_curramount=Coalesce(Sum('curramount'), 0, output_field=DecimalField()),
            num_transactions=Count('id'),
            max_curramount=Coalesce(Max('curramount'), 0, output_field=DecimalField()),
            min_curramount=Coalesce(Min('curramount'), 0, output_field=DecimalField()),
        ).order_by('tafzili')


        table1 = []
        current_tafzili_code = None
        tafzili_data = None

        for entry in sanad_aggregates:
            tafzili_code = entry['tafzili']
            total_curramount = entry['total_curramount']

            if tafzili_code != current_tafzili_code:
                if tafzili_data:
                    table1.append(tafzili_data)

                tafzili_name_obj = AccCoding.objects.filter(parent__parent__code=103,parent__code=103, code=moein_code, level=3).first()
                tafzili_name = tafzili_name_obj.name if tafzili_name_obj else f"نامعلوم ({tafzili_code})"
                current_tafzili_code = tafzili_code

                tafzili_data = {
                    'code': tafzili_code,
                    'name': tafzili_name,
                    'total_positive_balance': 0,
                    'total_negative_balance': 0,
                    'num_debtors': 0,
                    'num_creditors': 0,
                    'max_overall_debt': None,
                    'min_overall_credit': None,
                }

            if total_curramount > 0:
                tafzili_data['total_positive_balance'] += total_curramount
                tafzili_data['num_debtors'] += 1
                if tafzili_data['max_overall_debt'] is None or total_curramount > moein_data['max_overall_debt']:
                    tafzili_data['max_overall_debt'] = total_curramount
            elif total_curramount < 0:
                tafzili_data['total_negative_balance'] += total_curramount
                tafzili_data['num_creditors'] += 1
                if tafzili_data['min_overall_credit'] is None or total_curramount < moein_data['min_overall_credit']:
                    tafzili_data['min_overall_credit'] = total_curramount


        if tafzili_data:
            table1.append(tafzili_data)
        context['table1'] = table1











    total_positive_balance = Decimal('0')
    total_negative_balance = Decimal('0')
    num_debtors = 0
    num_creditors = 0
    max_overall_debt = None
    min_overall_credit = None

    for moin in table1:
        total_positive_balance += moin['total_positive_balance']
        total_negative_balance += moin['total_negative_balance']
        num_debtors += moin['num_debtors']
        num_creditors += moin['num_creditors']

        if moin['max_overall_debt'] is not None:
            if max_overall_debt is None or moin['max_overall_debt'] > max_overall_debt:
                max_overall_debt = moin['max_overall_debt']

        if moin['min_overall_credit'] is not None:
            if min_overall_credit is None or moin['min_overall_credit'] < min_overall_credit:
                min_overall_credit = moin['min_overall_credit']

    master_data = {
        'total_positive_balance': total_positive_balance/10,
        'total_negative_balance': total_negative_balance /10*-1,
        'total_balance': (total_positive_balance + total_negative_balance)/10,
        'num_debtors': num_debtors,
        'num_creditors': num_creditors,
        'max_overall_debt': max_overall_debt/10,
        'min_overall_credit': min_overall_credit/10*-1,
    }
    context['master_data'] = master_data




    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'ashkas-total.html', context)

import time
from decimal import Decimal

from django.shortcuts import render
from openpyxl.styles.builtins import title

from accounting.models import BedehiMoshtari
from custom_login.models import UserLog
from custom_login.views import page_permision
from dashboard.models import MasterInfo
from mahakupdate.models import SanadDetail, AccCoding, Person

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
    master_info = MasterInfo.objects.filter(is_active=True).last()
    monthly_rate = master_info.monthly_rate

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
            tafzili_code = entry['tafzili']
            total_curramount = entry['total_curramount']


            bedehi_moshtari=BedehiMoshtari.objects.filter(moin=moein_code,tafzili=tafzili_code)
            if bedehi_moshtari:
                sleep_investment=bedehi_moshtari.aggregate(total=Sum('sleep_investment'))['total']
                if sleep_investment:
                    bar_mali = sleep_investment / Decimal(30) * monthly_rate / Decimal(100)
                else:
                    bar_mali=0


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
                    'total_positive_bar_mali': 0,
                    'total_negative_bar_mali': 0,
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

            if bar_mali >0:
                moein_data['total_positive_bar_mali'] += bar_mali

            elif bar_mali <0:
                moein_data['total_negative_bar_mali'] += bar_mali

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
            bedehi_moshtari=BedehiMoshtari.objects.filter(tafzili=tafzili_code).last()
            if bedehi_moshtari:
                sleep_investment=bedehi_moshtari.sleep_investment
                if sleep_investment:
                    bar_mali = sleep_investment / Decimal(30) * monthly_rate / Decimal(100)
                else:
                    bar_mali=0
            if tafzili_code != current_tafzili_code:
                if tafzili_data:
                    table1.append(tafzili_data)

                tafzili_name_obj = Person.objects.filter(per_taf=tafzili_code).last()
                tafzili_name = f'{tafzili_name_obj.name} {tafzili_name_obj.lname}'  if tafzili_name_obj else f"کد فرد ({tafzili_code})"
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
                    'total_positive_bar_mali': 0,
                    'total_negative_bar_mali': 0,
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

            if bar_mali >0:
                tafzili_data['total_positive_bar_mali'] += bar_mali

            elif bar_mali <0:
                tafzili_data['total_negative_bar_mali'] += bar_mali


        if tafzili_data:
            table1.append(tafzili_data)
        context['table1'] = table1











    total_positive_balance = Decimal('0')
    total_negative_balance = Decimal('0')
    total_positive_barmali = Decimal('0')
    total_nagative_barmali = Decimal('0')
    num_debtors = 0
    num_creditors = 0
    max_overall_debt = None
    min_overall_credit = None

    for moin in table1:
        total_positive_balance += moin['total_positive_balance']
        total_negative_balance += moin['total_negative_balance']
        num_debtors += moin['num_debtors']
        num_creditors += moin['num_creditors']

        total_positive_barmali += moin['total_positive_bar_mali']
        total_nagative_barmali += moin['total_negative_bar_mali']

        if moin['max_overall_debt'] is not None:
            if max_overall_debt is None or moin['max_overall_debt'] > max_overall_debt:
                max_overall_debt = moin['max_overall_debt']

        if moin['min_overall_credit'] is not None:
            if min_overall_credit is None or moin['min_overall_credit'] < min_overall_credit:
                min_overall_credit = moin['min_overall_credit']

    master_data = {
        'total_positive_balance': total_positive_balance/10 if total_positive_balance else 0,
        'total_negative_balance': total_negative_balance /10*-1 if total_negative_balance else 0,
        'total_balance': (total_positive_balance + total_negative_balance)/10 if (total_positive_balance + total_negative_balance) else 0,
        'num_debtors': num_debtors,
        'num_creditors': num_creditors,
        'max_overall_debt': max_overall_debt/10 if max_overall_debt else 0 ,
        'min_overall_credit': min_overall_credit/10*-1 if min_overall_credit else 0,
        'total_positive_barmali': total_positive_barmali/10 if total_positive_barmali else 0,
        'total_negative_barmali': total_negative_barmali/10 if total_negative_barmali else 0,
    }
    context['master_data'] = master_data
    balance = master_data['total_balance']
    context['abs_balance'] = abs(balance)
    context['is_negative'] = balance < 0

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'ashkas-total.html', context)

from lib2to3.fixes.fix_input import context

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import time
from django.db.models import Sum
from openpyxl.styles.builtins import total
from pandas.plotting import table

from custom_login.models import UserLog
from mahakupdate.models import SanadDetail, AccCoding, ChequesRecieve
from django.db.models import Sum
from datetime import date, timedelta
from jdatetime import date as jdate
from datetime import timedelta, date



@login_required(login_url='/login')
def TarazKol(request, *args, **kwargs):
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='تراز آزمایشی', code=0)

    start_time = time.time()  # زمان شروع تابع

    # بارگذاری اطلاعات کل با جمع بدهکاری و بستانکاری
    kol_totals = SanadDetail.objects.values('kol').annotate(
        total_bed=Sum('bed'),
        total_bes=Sum('bes'),
        total_curramount=Sum('curramount')
    ).order_by('kol')

    # بارگذاری AccCoding برای سطوح کل و معین
    acc_codings = AccCoding.objects.filter(level__in=[1, 2]).values('code', 'name', 'level')
    acc_coding_dict = {coding['code']: (coding['name'], coding['level']) for coding in acc_codings}

    # ایجاد جدول کلی
    table_kol = []
    for kol in kol_totals:
        total_bed = kol['total_bed'] or 0
        total_bes = kol['total_bes'] or 0
        total_curramount = kol['total_curramount'] or 0
        name, level = acc_coding_dict.get(kol['kol'], ('نام نامشخص', 0))

        table_kol.append({
            'kol': kol['kol'],
            'name': name,
            'level': level,
            'total_bed': total_bed,
            'total_bes': total_bes,
            'total_curramount': total_curramount,
        })

    # ایجاد جدول معین با ارتباط به کل
    moin_totals = SanadDetail.objects.values('moin', 'kol').annotate(
        total_bed=Sum('bed'),
        total_bes=Sum('bes'),
        total_curramount=Sum('curramount')
    ).order_by('moin')

    table_moin = []
    for moin in moin_totals:
        total_bed = moin['total_bed'] or 0
        total_bes = moin['total_bes'] or 0
        total_curramount = moin['total_curramount'] or 0
        name, level = acc_coding_dict.get(moin['moin'], ('نام نامشخص', 0))
        kol_info = acc_coding_dict.get(moin['kol'], ('نام کل نامشخص', 0))
        kol_name = kol_info[0]  # نام کل
        kol_level = kol_info[1]  # سطح کل

        table_moin.append({
            'kol_num': moin['kol'],     # شماره کل
            'kol_name': kol_name,       # نام کل
            'moin': moin['moin'],       # شماره معین
            'name': name,               # نام معین
            'level': level,             # سطح معین
            'total_bed': total_bed,     # مجموع بدهکار
            'total_bes': total_bes,     # مجموع بستانکار
            'total_curramount': total_curramount,  # مجموع مانده
        })

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    # ایجاد کانتکست برای ارسال به تمپلیت
    context = {
        'title': 'تراز آزمایشی',
        'user': user,
        'table_kol': table_kol,
        'table_moin': table_moin,
    }

    return render(request, 'taraz_kol.html', context)


from django.shortcuts import render
from django.db.models import Prefetch
import time

from django.shortcuts import render



import time

from django.db.models import Prefetch

from django.shortcuts import render
from django.db.models import Sum
import time

from django.shortcuts import render
from django.db.models import Sum
import time

from django.shortcuts import render
import time


from django.db.models import Sum, F, OuterRef, Subquery

from django.db.models import Sum, OuterRef, Subquery

from django.shortcuts import render
import time

from django.shortcuts import render
from django.db.models import Prefetch
import time

from django.shortcuts import render
import time
from django.shortcuts import render
import time
import re

def extract_first_words(text):
    # الگوی جستجو برای پیدا کردن اولین کلمات قبل از اولین پرانتز
    match = re.match(r'([^()]+)', text)
    if match:
        return match.group(1).strip()
    return None



def ChequesRecieveTotal(request, *args, **kwargs):
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='چک های دریافتی', code=0)

    start_time = time.time()  # زمان شروع تابع
    today = date.today()

    # بارگذاری چک‌ها با بهینه‌سازی
    chequesrecieve = ChequesRecieve.objects.filter(total_mandeh__lt=0).select_related('last_sanad_detaile').all()

    chequesr = ChequesRecieve.objects.aggregate(total_mandeh_sum=Sum('total_mandeh'))
    postchequesr = ChequesRecieve.objects.filter(cheque_date__gt=today).aggregate(total_mandeh_sum=Sum('total_mandeh'))
    pastchequesr = ChequesRecieve.objects.filter(cheque_date__lte=today).aggregate(
        total_mandeh_sum=Sum('total_mandeh'))

    tmandeh = (chequesr['total_mandeh_sum'] / 10000000) * -1
    pastmandeh = (pastchequesr['total_mandeh_sum'] / 10000000) * -1
    postmandeh = (postchequesr['total_mandeh_sum'] / 10000000) * -1


    a=SanadDetail.objects.filter(kol=400).aggregate(curramount_sum=Sum('curramount'))['curramount_sum']
    print(a)
    ceque_ratio=tmandeh/a*10000000*100
    print(ceque_ratio)
    total_data = {
        'tmandeh': tmandeh,
        'pastmandeh': pastmandeh,
        'postmandeh': postmandeh,
        'ceque_ratio': ceque_ratio,

    }

    # chartmahanedata=[
    #     {
    #         'month_name':'سال های قبل',
    #         'total_count':25656,
    #     }
    #     ,
    #     {
    #         'month_name':'فروردین',
    #         'total_count':16546,
    #     }
    #     ,
    #     {
    #         'month_name':'اردیبهشت',
    #         'total_count':6520,
    #     }
    #     ,
    #     {
    #         'month_name':'سالهای بعد',
    #         'total_count':2154666,
    #     }
    #
    # ]

    # تبدیل تاریخ امروز به شمسی
    today_jalali = jdate.fromgregorian(date=today)

    # سال شمسی جاری
    current_jalali_year = today_jalali.year

    # اولین روز سال جاری شمسی
    first_day_of_current_year_jalali = jdate(current_jalali_year, 1, 1).togregorian()

    # آخرین روز سال جاری شمسی
    last_day_of_current_year_jalali = jdate(current_jalali_year, 12, 29).togregorian()  # اسفند ۲۹ روز دارد

    # محاسبه مجموع مانده چک‌های سال‌های قبل
    cheques_before_current_year = ChequesRecieve.objects.filter(
        cheque_date__lt=first_day_of_current_year_jalali
    ).aggregate(total_mandeh=Sum('total_mandeh'))['total_mandeh'] or 0

    # محاسبه مجموع مانده چک‌های سال‌های بعد
    cheques_after_current_year = ChequesRecieve.objects.filter(
        cheque_date__gt=last_day_of_current_year_jalali
    ).aggregate(total_mandeh=Sum('total_mandeh'))['total_mandeh'] or 0

    # محاسبه مجموع مانده چک‌ها برای هر ماه سال جاری
    month_names = {
        1: 'فروردین',
        2: 'اردیبهشت',
        3: 'خرداد',
        4: 'تیر',
        5: 'مرداد',
        6: 'شهریور',
        7: 'مهر',
        8: 'آبان',
        9: 'آذر',
        10: 'دی',
        11: 'بهمن',
        12: 'اسفند',
    }





    monthly_data = []
    for month in range(1, 13):  # از فروردین (ماه ۱) تا اسفند (ماه ۱۲)
        first_day_of_month_jalali = jdate(current_jalali_year, month, 1).togregorian()
        last_day_of_month_jalali = (jdate(current_jalali_year, month + 1, 1) if month < 12 else jdate(
            current_jalali_year + 1, 1, 1)).togregorian() - timedelta(days=1)

        total_mandeh_month = ChequesRecieve.objects.filter(
            cheque_date__gte=first_day_of_month_jalali,
            cheque_date__lte=last_day_of_month_jalali
        ).aggregate(total_mandeh=Sum('total_mandeh'))['total_mandeh'] or 0

        # monthly_data.append({
        #     'month_name': jdate(current_jalali_year, month, 1).strftime('%B'),  # نام ماه به فارسی
        #     'total_count': float(total_mandeh_month) * -1/10000000  # ضرب در منفی ۱
        # })
        # در حلقه ماه‌ها
        monthly_data.append({
            'month_name': month_names[month],  # استفاده از دیکشنری
            'total_count': float(total_mandeh_month) * -1 / 10000000
        })

    # آماده‌سازی داده‌ها برای نمودار
    chartmahanedata = [
        {
            'month_name': 'سال های قبل',
            'total_count': float(cheques_before_current_year) * -1/10000000  # ضرب در منفی ۱
        }
    ]

    # اضافه کردن داده‌های ماه‌های سال جاری
    chartmahanedata.extend(monthly_data)

    # اضافه کردن داده‌های سال‌های بعد
    chartmahanedata.append({
        'month_name': 'سالهای بعد',
        'total_count': float(cheques_after_current_year) * -1 /10000000 # ضرب در منفی ۱
    })

    for c in chartmahanedata:
        print(c)

















    table1 = []
    # تغییر به cheque_id به جای id
    last_sanad_comments = {chequ.cheque_id: chequ.last_sanad_detaile.syscomment for chequ in chequesrecieve if chequ.last_sanad_detaile}

    for chequ in chequesrecieve:
        com = last_sanad_comments.get(chequ.cheque_id, '')

        table1.append(
            {
                'id': chequ.cheque_id,
                'status': chequ.status,
                'com': extract_first_words(com),
                'mandeh': -1*chequ.total_mandeh,
                'date':chequ.cheque_date,
            }
        )

    context = {
        'title': 'چکهای دریافتی',
        'user': user,
        'total_data': total_data,
        'chartmahanedata': chartmahanedata,
        'table1': table1,
    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'cheques-recieve-total.html', context)


def ChequesRecieveTotal1(request, *args, **kwargs):
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='چک های دریافتی', code=0)

    start_time = time.time()  # زمان شروع تابع

    # بارگذاری همزمان اوبجکت‌های ChequesRecieve
    chequesrecieve = ChequesRecieve.objects.filter(status=1)

    table1 = []

    for chequ in chequesrecieve:
        last_sanad = chequ.sanad_detail()  # متد برای دستیابی به سند
        com = last_sanad.syscomment if last_sanad else "بدون توضیحات"
        man = chequ.mandeh()  # متد برای محاسبه مانده

        table1.append(
            {
                'id': chequ.cheque_id,
                'status': chequ.status,
                'com': com,
                'mandeh': man,
            }
        )

    context = {
        'title': 'چکهای دریافتی',
        'user': user,
        'table1': table1,
    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'cheques-recieve-total.html', context)


# views.py
from django.shortcuts import render

# views.py
from django.shortcuts import render


# views.py
from django.shortcuts import render
from django.db.models import Sum

def balance_sheet_kol(request):
    kol_codes = SanadDetail.objects.values('kol').distinct()
    balance_data = []

    for kol in kol_codes:
        kol_code = kol['kol']
        kol_name = AccCoding.objects.filter(code=kol_code, level=1).first().name
        bed_sum = SanadDetail.objects.filter(kol=kol_code).aggregate(Sum('bed'))['bed__sum']
        bes_sum = SanadDetail.objects.filter(kol=kol_code).aggregate(Sum('bes'))['bes__sum']
        curramount_sum = SanadDetail.objects.filter(kol=kol_code).aggregate(Sum('curramount'))['curramount__sum']

        balance_data.append({
            'kol_code': kol_code,
            'kol_name': kol_name,
            'bed_sum': bed_sum,
            'bes_sum': bes_sum,
            'curramount_sum': curramount_sum,
        })

    context = {
        'balance_data': balance_data,
        'level': 1,
        'level_name': 'کل',
        'myheader':'جدول تراز در سطح کل',
        'myheaderlink':'/#',
    }
    return render(request, 'balance_sheet.html', context)


# views.py
from django.shortcuts import render


# views.py

# views.py
def balance_sheet_moin(request, kol_code):
    moin_codes = SanadDetail.objects.filter(kol=kol_code).values('moin').distinct()
    balance_data = []

    for moin in moin_codes:
        moin_code = moin['moin']
        moin_name = AccCoding.objects.filter(code=moin_code, level=2, parent__code=kol_code).first().name
        bed_sum = SanadDetail.objects.filter(kol=kol_code, moin=moin_code).aggregate(Sum('bed'))['bed__sum']
        bes_sum = SanadDetail.objects.filter(kol=kol_code, moin=moin_code).aggregate(Sum('bes'))['bes__sum']
        curramount_sum = SanadDetail.objects.filter(kol=kol_code, moin=moin_code).aggregate(Sum('curramount'))['curramount__sum']

        balance_data.append({
            'moin_code': moin_code,
            'moin_name': moin_name,
            'bed_sum': bed_sum,
            'bes_sum': bes_sum,
            'curramount_sum': curramount_sum,
        })
    kol_name=AccCoding.objects.filter(level=1,code=kol_code).last().name
    context = {
        'balance_data': balance_data,
        'level': 2,
        'level_name': 'معین',
        'parent_code': kol_code,
        'parent_name': AccCoding.objects.filter(code=kol_code, level=1).first().name,
        'myheader': f'جدول تراز در سطح معین از کل {kol_code}-{kol_name}',
        'myheaderlink': '/balance-sheet-kol',
    }
    return render(request, 'balance_sheet.html', context)
# views.py


def balance_sheet_tafsili(request, kol_code, moin_code):
    tafsili_codes = SanadDetail.objects.filter(kol=kol_code, moin=moin_code).values('tafzili').distinct()
    balance_data = []

    for tafsili in tafsili_codes:
        tafsili_code = tafsili['tafzili']
        bed_sum = SanadDetail.objects.filter(kol=kol_code, moin=moin_code, tafzili=tafsili_code).aggregate(Sum('bed'))['bed__sum']
        bes_sum = SanadDetail.objects.filter(kol=kol_code, moin=moin_code, tafzili=tafsili_code).aggregate(Sum('bes'))['bes__sum']
        curramount_sum = SanadDetail.objects.filter(kol=kol_code, moin=moin_code, tafzili=tafsili_code).aggregate(Sum('curramount'))['curramount__sum']

        balance_data.append({
            'tafzili_code': tafsili_code,
            'bed_sum': bed_sum,
            'bes_sum': bes_sum,
            'curramount_sum': curramount_sum,
        })

    for t in balance_data:
        print('t.tafzili_code')
        print(t)


    context = {
        'balance_data': balance_data,
        'level': 3,
        'moin_code':moin_code,
        'kol_code':kol_code,
        'level_name': 'تفضیلی',
        'parent_code': moin_code,
        'parent_name': AccCoding.objects.filter(code=moin_code, level=2, parent__code=kol_code).first().name,
    }
    return render(request, 'balance_sheet.html', context)


def SanadTotal(request, *args, **kwargs):
    kol_code = kwargs['kol_code']
    moin_code = kwargs['moin_code']
    tafzili_code = kwargs['tafzili_code']

    sanads=SanadDetail.objects.filter(kol=kol_code,moin=moin_code,tafzili=tafzili_code)


    context={
        'sanads':sanads,
        'kol_code':kol_code,
        'kol_name':AccCoding.objects.filter(level=1,code=kol_code).last().name,
        'moin_code':moin_code,
        'moin_name':AccCoding.objects.filter(level=2,code=moin_code).last().name,
        'tafzili_code':tafzili_code,

    }



    return render(request, 'sanad_total.html', context)


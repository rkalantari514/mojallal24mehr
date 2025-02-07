#جدید
# جدیدتر
import re
from django.contrib.auth.decorators import login_required
import time

from openpyxl.styles.builtins import total

from custom_login.models import UserLog
from mahakupdate.models import SanadDetail, AccCoding, ChequesRecieve
from jdatetime import date as jdate
from datetime import timedelta, date
from django.shortcuts import render
from django.db.models import Sum





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

def extract_first_words(text):
    # الگوی جستجو برای پیدا کردن اولین کلمات قبل از اولین پرانتز
    match = re.match(r'([^()]+)', text)
    if match:
        return match.group(1).strip()
    return None


@login_required(login_url='/login')
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

    from django.db.models import Sum

    # جمع مقادیر curramount برای kol های 400 و 404
    total_a = SanadDetail.objects.filter(kol=400).aggregate(total=Sum('curramount'))['total'] or 0
    total_b = SanadDetail.objects.filter(kol=404).aggregate(total=Sum('curramount'))['total'] or 0

    # محاسبه مجموع
    total_sum = total_a + total_b

    # محاسبه نسبت ceque_ratio
    if total_sum != 0:
        ceque_ratio = (tmandeh / total_sum) * 10000000 * 100
    else:
        ceque_ratio = 0

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



def balance_sheet_kol(request):
    kol_codes = SanadDetail.objects.values('kol').distinct()
    balance_data = []
    total_bed = 0
    total_bes = 0
    total_curramount = 0

    for kol in kol_codes:
        kol_code = kol['kol']
        kol_name = AccCoding.objects.filter(code=kol_code, level=1).first().name
        bed_sum = SanadDetail.objects.filter(is_active=True,kol=kol_code).aggregate(Sum('bed'))['bed__sum'] or 0
        bes_sum = SanadDetail.objects.filter(is_active=True,kol=kol_code).aggregate(Sum('bes'))['bes__sum'] or 0
        curramount_sum = SanadDetail.objects.filter(is_active=True,kol=kol_code).aggregate(Sum('curramount'))['curramount__sum'] or 0
        total_bed += bed_sum
        total_bes += bes_sum
        total_curramount += curramount_sum
        balance_data.append({
            'kol_code': kol_code,
            'kol_name': kol_name,
            'bed_sum': bed_sum,
            'bes_sum': bes_sum,
            'curramount_sum': curramount_sum,

        })

    level1=[]
    level2=[]
    level3=[]
    for l in AccCoding.objects.filter(level=1).order_by('code'):
        # filtercount=SanadDetail.objects.filter(is_active=False,kol=l.code).count()
        print(l.code,l.name)
        level1.append(
            {
               'code':l.code,
               'name':l.name,
               # 'filtercount':filtercount,

            }
        )



    context = {
        'balance_data': balance_data,
        'level': 1,
        'level1':level1,
        'level2':level2,
        'level3':level3,
        'total_bed': total_bed,
        'total_bes': total_bes,
        'total_curramount': total_curramount,
    }
    return render(request, 'balance_sheet.html', context)

def balance_sheet_moin(request, kol_code):
    moin_codes = SanadDetail.objects.filter(kol=kol_code).values('moin').distinct()
    balance_data = []
    total_bed=0
    total_bes=0
    total_curramount=0

    for moin in moin_codes:
        moin_code = moin['moin']
        moin_name=None
        if AccCoding.objects.filter(code=moin_code, level=2, parent__code=kol_code):
            moin_name = AccCoding.objects.filter(code=moin_code, level=2, parent__code=kol_code).first().name
        if not moin_name:
            par=AccCoding.objects.filter(code=kol_code, level=1).last()
            AccCoding.objects.create(code=moin_code, level=2, parent=par,name='تعیین نشده')
        moin_name = AccCoding.objects.filter(code=moin_code, level=2, parent__code=kol_code).first().name
        bed_sum = SanadDetail.objects.filter(is_active=True, kol=kol_code, moin=moin_code).aggregate(Sum('bed'))[
                      'bed__sum'] or 0
        bes_sum = SanadDetail.objects.filter(is_active=True, kol=kol_code, moin=moin_code).aggregate(Sum('bes'))[
                      'bes__sum'] or 0
        curramount_sum = \
        SanadDetail.objects.filter(is_active=True, kol=kol_code, moin=moin_code).aggregate(Sum('curramount'))[
            'curramount__sum'] or 0
        total_bed += bed_sum
        total_bes += bes_sum
        total_curramount += curramount_sum

        balance_data.append({
            'moin_code': moin_code,
            'moin_name': moin_name,
            'bed_sum': bed_sum,
            'bes_sum': bes_sum,
            'curramount_sum': curramount_sum,
        })
    kol_name=AccCoding.objects.filter(level=1,code=kol_code).last().name
    # kol_code=AccCoding.objects.filter(level=1,code=kol_code).last().code
    level1 = []
    level2 = []
    level3 = []
    for l in AccCoding.objects.filter(level=1).order_by('code'):
        print(l.code, l.name)
        level1.append(
            {
                'code': l.code,
                'name': l.name,

            }
        )

    for l in AccCoding.objects.filter(level=2,parent__code=kol_code).order_by('code'):
        print(l.code, l.name)
        level2.append(
            {
                'code': l.code,
                'name': l.name,

            }
        )




    context = {
        'balance_data': balance_data,
        'level': 2,
        'level_name': 'معین',
        'parent_code': kol_code,
        'parent_name': AccCoding.objects.filter(code=kol_code, level=1).first().name,
        'myheader': f'جدول تراز در سطح معین از کل {kol_code}-{kol_name}',
        'myheaderlink': '/balance-sheet-kol',
        'kol_code': kol_code,
        # 'moin_code': kol_code,

        'level1': level1,
        'level2': level2,
        'level3': level3,
        'total_bed':total_bed,
        'total_bes':total_bes,
        'total_curramount':total_curramount,


    }
    return render(request, 'balance_sheet.html', context)

def balance_sheet_tafsili(request, kol_code, moin_code):
    tafsili_codes = SanadDetail.objects.filter(kol=kol_code, moin=moin_code).values('tafzili').distinct()
    balance_data = []
    total_bed = 0
    total_bes = 0
    total_curramount = 0
    for tafsili in tafsili_codes:
        tafsili_code = tafsili['tafzili']

        bed_sum = \
        SanadDetail.objects.filter(is_active=True, kol=kol_code, moin=moin_code, tafzili=tafsili_code).aggregate(
            Sum('bed'))['bed__sum'] or 0
        bes_sum = \
        SanadDetail.objects.filter(is_active=True, kol=kol_code, moin=moin_code, tafzili=tafsili_code).aggregate(
            Sum('bes'))['bes__sum'] or 0
        curramount_sum = \
        SanadDetail.objects.filter(is_active=True, kol=kol_code, moin=moin_code, tafzili=tafsili_code).aggregate(
            Sum('curramount'))['curramount__sum'] or 0



        total_bed += bed_sum
        total_bes += bes_sum
        total_curramount += curramount_sum
        balance_data.append({
            'tafzili_code': tafsili_code,
            'bed_sum': bed_sum,
            'bes_sum': bes_sum,
            'curramount_sum': curramount_sum,
        })


    kol_name = AccCoding.objects.filter(level=1, code=kol_code).last().name
    # kol_code=AccCoding.objects.filter(level=1,code=kol_code).last().code
    level1 = []
    level2 = []
    level3 = []
    for l in AccCoding.objects.filter(level=1).order_by('code'):
        level1.append(
            {
                'code': l.code,
                'name': l.name,

            }
        )

    for l in AccCoding.objects.filter(level=2, parent__code=kol_code).order_by('code'):
        level2.append(
            {
                'code': l.code,
                'name': l.name,

            }
        )


    # فعلا خالی است
    for l in AccCoding.objects.filter(level=3, parent__code=moin_code, parent__parent__code=kol_code).order_by('code'):
        print(l.code, l.name)
        level3.append(
            {
                'code': l.code,
                'name': l.name,

            }
        )
    level3 = []

    # فیلتر کردن داده‌ها
    sanads = SanadDetail.objects.filter(kol=kol_code, moin=moin_code)

    # استفاده از مجموعه برای حذف تکراری‌ها و سپس تبدیل به لیست مرتب‌شده
    tafzili_set = sorted({s.tafzili for s in sanads})

    # ایجاد لیست level3
    for tafzili_code in tafzili_set:
        print(tafzili_code)
        level3.append(
            {
                'code': tafzili_code,
                'name': '',
            }
        )

    context = {
        'balance_data': balance_data,
        'level': 3,
        'moin_code':moin_code,
        'kol_code':kol_code,
        'level_name': 'تفضیلی',
        'parent_code': moin_code,
        'parent_name': AccCoding.objects.filter(code=moin_code, level=2, parent__code=kol_code).first().name,
        'kol_code': kol_code,
        'moin_code': moin_code,

        'level1': level1,
        'level2': level2,
        'level3': level3,
        'total_bed': total_bed,
        'total_bes': total_bes,
        'total_curramount': total_curramount,
    }
    return render(request, 'balance_sheet.html', context)

def SanadTotal(request, *args, **kwargs):
    kol_code = kwargs['kol_code']
    moin_code = kwargs['moin_code']
    tafzili_code = kwargs['tafzili_code']

    sanads=SanadDetail.objects.filter(kol=kol_code,moin=moin_code,tafzili=tafzili_code)

    level1 = []
    level2 = []
    level3 = []
    for l in AccCoding.objects.filter(level=1).order_by('code'):
        level1.append(
            {
                'code': l.code,
                'name': l.name,

            }
        )

    for l in AccCoding.objects.filter(level=2, parent__code=kol_code).order_by('code'):
        level2.append(
            {
                'code': l.code,
                'name': l.name,

            }
        )

    # فعلا خالی است
    for l in AccCoding.objects.filter(level=3, parent__code=moin_code, parent__parent__code=kol_code).order_by('code'):
        print(l.code, l.name)
        level3.append(
            {
                'code': l.code,
                'name': l.name,

            }
        )
    level3 = []

    # فیلتر کردن داده‌ها
    sanads2 = SanadDetail.objects.filter(kol=kol_code, moin=moin_code)

    # استفاده از مجموعه برای حذف تکراری‌ها و سپس تبدیل به لیست مرتب‌شده
    tafzili_set = sorted({s.tafzili for s in sanads2})

    # ایجاد لیست level3
    for tafzili_code1 in tafzili_set:
        level3.append(
            {
                'code': tafzili_code1,
                'name': '',
            }
        )

    level=4

    print(level,kol_code,moin_code,tafzili_code)
    bed_sum = SanadDetail.objects.filter(is_active=True,kol=kol_code, moin=moin_code, tafzili=tafzili_code).aggregate(Sum('bed'))[
        'bed__sum']
    bes_sum = SanadDetail.objects.filter(is_active=True,kol=kol_code, moin=moin_code, tafzili=tafzili_code).aggregate(Sum('bes'))[
        'bes__sum']
    curramount_sum = \
    SanadDetail.objects.filter(is_active=True,kol=kol_code, moin=moin_code, tafzili=tafzili_code).aggregate(Sum('curramount'))[
        'curramount__sum']



    context={
        'level':level,
        'sanads':sanads,
        'kol_code':int(kol_code),
        'moin_code':int(moin_code),
        'tafzili_code':int(tafzili_code),
        'level1': level1,
        'level2': level2,
        'level3': level3,
        'total_bed': bed_sum,
        'total_bes': bes_sum,
        'total_curramount': curramount_sum,

    }



    return render(request, 'sanad_total.html', context)

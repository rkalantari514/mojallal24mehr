# جدید
# جدیدتر
import re

import time
import datetime
from django.db.models import Sum, Min, Max
from django.db.models import Q
from django.shortcuts import render
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import jdatetime
from django.db.models import Sum, Subquery # مطمئن شوید Subquery را ایمپورت کرده‌اید
from django.contrib.auth.decorators import login_required
import time
from django.utils import timezone
from django.db.models import Sum, F, FloatField
from django.db.models.functions import Cast
from openpyxl.styles.builtins import total
from persianutils import standardize
from django.db.models import Sum, F, DecimalField

from accounting.models import BedehiMoshtari
from custom_login.models import UserLog
from custom_login.views import page_permision
from dashboard.models import MasterInfo, MasterReport, MonthlyReport
from dashboard.views import generate_calendar_data_cheque
from loantracker.forms import SMSTrackingForm, CallTrackingForm
from loantracker.models import TrackKinde, Tracking
from mahakupdate.models import SanadDetail, AccCoding, ChequesRecieve, ChequesPay, Person, Loan, LoanDetil, Kala, \
    GoodConsign
from jdatetime import date as jdate
from khayyam import JalaliDate, JalaliDatetime
from django.db.models import F

from mahakupdate.sendtogap import send_to_admin1, send_sms, check_sms_status
from django.http import JsonResponse

def fix_persian_characters(value):
    return standardize(value)


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
            'kol_num': moin['kol'],  # شماره کل
            'kol_name': kol_name,  # نام کل
            'moin': moin['moin'],  # شماره معین
            'name': name,  # نام معین
            'level': level,  # سطح معین
            'total_bed': total_bed,  # مجموع بدهکار
            'total_bes': total_bes,  # مجموع بستانکار
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
    name = 'چک های دریافتی'
    result = page_permision(request, name)  # بررسی دسترسی
    if result:  # اگر هدایت انجام شده است
        return result
    from django.db.models import Sum  # این خط را به ابتدای تابع منتقل کنید
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='چک های دریافتی', code=0)

    start_time = time.time()  # زمان شروع تابع

    # گام اول: استخراج تاریخ و ماه
    today = timezone.now().date()
    month = request.GET.get('month', None)
    year = request.GET.get('year', None)

    if month is not None and year is not None:
        current_month = int(month)
        current_year = int(year)
    else:
        today_jalali = JalaliDate.today()
        current_year = today_jalali.year
        current_month = today_jalali.month

    months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    month_name = months[current_month - 1]
    print(f"1: {time.time() - start_time:.2f} ثانیه")
    # گام دوم: بارگذاری چک‌ها به صورت بهینه
    chequesrecieve = ChequesRecieve.objects.filter(total_mandeh__lt=0).select_related('last_sanad_detaile').order_by(
        'cheque_date')
    print(f"2: {time.time() - start_time:.2f} ثانیه")
    # گام سوم: محاسبه جمع چک‌ها
    cheques_data = ChequesRecieve.objects.aggregate(
        total_mandeh_sum=Sum('total_mandeh')
    )

    past_cheques_sum = \
        ChequesRecieve.objects.filter(cheque_date__lte=today).aggregate(total_mandeh=Sum('total_mandeh'))[
            'total_mandeh'] or 0
    post_cheques_sum = ChequesRecieve.objects.filter(cheque_date__gt=today).aggregate(total_mandeh=Sum('total_mandeh'))[
                           'total_mandeh'] or 0
    tmandeh = -cheques_data['total_mandeh_sum'] / 10000000  # تبدیل به میلیون
    pastmandeh = -past_cheques_sum / 10000000
    postmandeh = -post_cheques_sum / 10000000

    # محاسبه مجموع curramount برای kol های 400 و 404
    total_a = SanadDetail.objects.filter(kol=400).aggregate(total=Sum('curramount'))['total'] or 0
    total_b = SanadDetail.objects.filter(kol=404).aggregate(total=Sum('curramount'))['total'] or 0
    total_sum = total_a + total_b

    # محاسبه نسبت ceque_ratio
    ceque_ratio = (tmandeh / total_sum * 10000000 * 100) if total_sum != 0 else 0

    total_data = {
        'tmandeh': tmandeh,
        'pastmandeh': pastmandeh,
        'postmandeh': postmandeh,
        'ceque_ratio': ceque_ratio,
    }
    print(f"3: {time.time() - start_time:.2f} ثانیه")

    # تبدیل تاریخ امروز به شمسی
    today_jalali = jdate.fromgregorian(date=today)
    current_jalali_year = today_jalali.year

    # محاسبه مجموع مانده چک‌های سال‌های قبل و بعد
    first_day_of_current_year_jalali = jdate(current_jalali_year, 1, 1).togregorian()
    last_day_of_current_year_jalali = jdate(current_jalali_year, 12, 29).togregorian()

    cheques_before_current_year = \
        ChequesRecieve.objects.filter(cheque_date__lt=first_day_of_current_year_jalali).aggregate(
            total_mandeh=Sum('total_mandeh'))['total_mandeh'] or 0
    cheques_after_current_year = \
        ChequesRecieve.objects.filter(cheque_date__gt=last_day_of_current_year_jalali).aggregate(
            total_mandeh=Sum('total_mandeh'))['total_mandeh'] or 0
    print(f"4: {time.time() - start_time:.2f} ثانیه")

    monthly_data = []
    for month in range(1, 13):
        first_day_of_month_jalali = jdate(current_jalali_year, month, 1).togregorian()
        last_day_of_month_jalali = (
            jdate(current_jalali_year, month + 1, 1).togregorian() - timedelta(days=1) if month < 12 else jdate(
                current_jalali_year + 1, 1, 1).togregorian() - timedelta(days=1))

        total_mandeh_month = ChequesRecieve.objects.filter(
            cheque_date__gte=first_day_of_month_jalali,
            cheque_date__lte=last_day_of_month_jalali
        ).aggregate(total_mandeh=Sum('total_mandeh'))['total_mandeh'] or 0

        monthly_data.append({
            'month_name': months[month - 1],
            'total_count': -float(total_mandeh_month) / 10000000
        })
    print(f"5: {time.time() - start_time:.2f} ثانیه")

    chart_data = [
        {'month_name': 'سال های قبل', 'total_count': -float(cheques_before_current_year) / 10000000},
        *monthly_data,
        {'month_name': 'سالهای بعد', 'total_count': -float(cheques_after_current_year) / 10000000},
    ]
    print(f"6: {time.time() - start_time:.2f} ثانیه")

    # مرحله اول: دریافت کدهای منحصر به فرد per_code
    per_codes = chequesrecieve.values_list('per_code', flat=True).distinct()
    print("Unique per_codes from ChequesRecieve:", per_codes)

    # بارگذاری اطلاعات شخص بر اساس per_code
    persons = Person.objects.filter(code__in=per_codes)

    # بارگذاری دیکشنری با کلیدهای به عنوان رشته
    persons_map = {str(person.code): f"{person.name} {person.lname}" for person in persons}
    print("Loaded Persons Map:", persons_map)

    # آماده‌سازی داده‌ها برای جدول
    table1 = []
    for chequ in chequesrecieve:
        com = chequ.last_sanad_detaile.syscomment if chequ.last_sanad_detaile else ''

        # دسترسی به نام و نام خانوادگی شخص از دیکشنری
        person = persons_map.get(str(chequ.per_code), '')  # ساختار به صورت رشته

        # Split تاریخ به سال، ماه و روز
        year, month, day = chequ.cheque_tarik.split('/')

        # اضافه کردن داده‌ها به جدول
        table1.append({
            'id': chequ.cheque_id,
            'status': chequ.status,
            'com': extract_first_words(com),
            'mandeh': -1 * chequ.total_mandeh,
            'date': chequ.cheque_date,
            'bank_logo': chequ.bank_logo,
            'bank_name': chequ.bank_name,
            'bank_branch': chequ.bank_branch,
            'person': fix_persian_characters(person),  # Person نام و نام خانوادگی
            'year': year,
            'month': month,
        })

    print(f"7: {time.time() - start_time:.2f} ثانیه")

    print(f"8: {time.time() - start_time:.2f} ثانیه")

    # آماده‌سازی context برای رندر
    context = {
        'title': 'چکهای دریافتی',
        'user': user,
        'total_data': total_data,
        'chartmahanedata': chart_data,
        'table1': table1,

    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'cheques-recieve-total.html', context)


@login_required(login_url='/login')
def ChequesPayTotal(request, *args, **kwargs):
    name = 'چکهای پرداختی'
    result = page_permision(request, name)  # بررسی دسترسی
    if result:  # اگر هدایت انجام شده است
        return result
    from django.db.models import Sum  # این خط را به ابتدای تابع منتقل کنید
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='چک های پرداختی', code=0)

    start_time = time.time()  # زمان شروع تابع

    # گام اول: استخراج تاریخ و ماه
    today = timezone.now().date()
    month = request.GET.get('month', None)
    year = request.GET.get('year', None)

    if month is not None and year is not None:
        current_month = int(month)
        current_year = int(year)
    else:
        today_jalali = JalaliDate.today()
        current_year = today_jalali.year
        current_month = today_jalali.month

    months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    month_name = months[current_month - 1]
    print(f"1: {time.time() - start_time:.2f} ثانیه")
    # گام دوم: بارگذاری چک‌ها به صورت بهینه
    chequespay = ChequesPay.objects.filter(total_mandeh__gt=0).select_related('last_sanad_detaile').order_by(
        'cheque_date')
    print(f"2: {time.time() - start_time:.2f} ثانیه")
    # گام سوم: محاسبه جمع چک‌ها
    cheques_data = ChequesPay.objects.aggregate(
        total_mandeh_sum=Sum('total_mandeh')
    )

    past_cheques_sum = \
        ChequesPay.objects.filter(cheque_date__lte=today).aggregate(total_mandeh=Sum('total_mandeh'))[
            'total_mandeh'] or 0
    post_cheques_sum = ChequesPay.objects.filter(cheque_date__gt=today).aggregate(total_mandeh=Sum('total_mandeh'))[
                           'total_mandeh'] or 0
    tmandeh = cheques_data['total_mandeh_sum'] / 10000000  # تبدیل به میلیون
    pastmandeh = past_cheques_sum / 10000000
    postmandeh = post_cheques_sum / 10000000

    # محاسبه مجموع curramount برای kol های 400 و 404
    total_a = SanadDetail.objects.filter(kol=400).aggregate(total=Sum('curramount'))['total'] or 0
    total_b = SanadDetail.objects.filter(kol=404).aggregate(total=Sum('curramount'))['total'] or 0
    total_sum = total_a + total_b

    # محاسبه نسبت ceque_ratio
    ceque_ratio = (tmandeh / total_sum * 10000000 * 100) if total_sum != 0 else 0

    total_data = {
        'tmandeh': tmandeh,
        'pastmandeh': pastmandeh,
        'postmandeh': postmandeh,
        'ceque_ratio': ceque_ratio,
    }
    print(f"3: {time.time() - start_time:.2f} ثانیه")

    # تبدیل تاریخ امروز به شمسی
    today_jalali = jdate.fromgregorian(date=today)
    current_jalali_year = today_jalali.year

    # محاسبه مجموع مانده چک‌های سال‌های قبل و بعد
    first_day_of_current_year_jalali = jdate(current_jalali_year, 1, 1).togregorian()
    last_day_of_current_year_jalali = jdate(current_jalali_year, 12, 29).togregorian()

    cheques_before_current_year = \
        ChequesPay.objects.filter(cheque_date__lt=first_day_of_current_year_jalali).aggregate(
            total_mandeh=Sum('total_mandeh'))['total_mandeh'] or 0
    cheques_after_current_year = \
        ChequesPay.objects.filter(cheque_date__gt=last_day_of_current_year_jalali).aggregate(
            total_mandeh=Sum('total_mandeh'))['total_mandeh'] or 0
    print(f"4: {time.time() - start_time:.2f} ثانیه")

    monthly_data = []
    for month in range(1, 13):
        first_day_of_month_jalali = jdate(current_jalali_year, month, 1).togregorian()
        last_day_of_month_jalali = (
            jdate(current_jalali_year, month + 1, 1).togregorian() - timedelta(days=1) if month < 12 else jdate(
                current_jalali_year + 1, 1, 1).togregorian() - timedelta(days=1))

        total_mandeh_month = ChequesPay.objects.filter(
            cheque_date__gte=first_day_of_month_jalali,
            cheque_date__lte=last_day_of_month_jalali
        ).aggregate(total_mandeh=Sum('total_mandeh'))['total_mandeh'] or 0

        monthly_data.append({
            'month_name': months[month - 1],
            'total_count': float(total_mandeh_month) / 10000000
        })
    print(f"5: {time.time() - start_time:.2f} ثانیه")

    chart_data = [
        {'month_name': 'سال های قبل', 'total_count': float(cheques_before_current_year) / 10000000},
        *monthly_data,
        {'month_name': 'سالهای بعد', 'total_count': float(cheques_after_current_year) / 10000000},
    ]

    # آماده‌سازی داده‌ها برای جدول
    table1 = []
    for chequ in chequespay:
        com = chequ.last_sanad_detaile.syscomment if chequ.last_sanad_detaile else ''

        # Split تاریخ به سال، ماه و روز
        year, month, day = chequ.cheque_tarik.split('/')

        # اضافه کردن داده‌ها به جدول
        table1.append({
            'id': chequ.cheque_id,
            'status': chequ.status,
            'person': (f'{chequ.person.name} {chequ.person.lname}') if chequ.person else "",
            'com': extract_first_words(com),
            'mandeh': chequ.total_mandeh,
            'date': chequ.cheque_date,
            'bank_logo': chequ.bank.bank_logo,
            'bank_name': chequ.bank.bank_name,
            'bank_branch': chequ.bank.name,
            'year': year,
            'month': month,
        })

    print(f"7: {time.time() - start_time:.2f} ثانیه")

    # تکمیل تقویم

    month = request.GET.get('month', None)
    year = request.GET.get('year', None)
    print("Query params - Year:", year, "Month:", month)

    print(f"8: {time.time() - start_time:.2f} ثانیه")

    # آماده‌سازی context برای رندر
    context = {
        'title': 'چکهای پرداختنی',
        'user': user,
        'total_data': total_data,
        'chartmahanedata': chart_data,
        'table1': table1,

    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'cheques-pay-total.html', context)


@login_required(login_url='/login')
def balance_sheet_kol(request, year):
    name = 'تراز آزمایشی | کل'
    result = page_permision(request, name)  # بررسی دسترسی
    if result:  # اگر هدایت انجام شده است
        return result
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
    acc_year = int(year)
    kol_codes = SanadDetail.objects.values('kol').distinct()
    balance_data = []
    total_bed = 0
    total_bes = 0
    total_curramount = 0

    for kol in kol_codes:
        kol_code = kol['kol']
        kol_name = AccCoding.objects.filter(code=kol_code, level=1).first().name
        bed_sum = SanadDetail.objects.filter(is_active=True, kol=kol_code, acc_year=acc_year).aggregate(Sum('bed'))[
                      'bed__sum'] or 0
        bes_sum = SanadDetail.objects.filter(is_active=True, kol=kol_code, acc_year=acc_year).aggregate(Sum('bes'))[
                      'bes__sum'] or 0
        curramount_sum = \
            SanadDetail.objects.filter(is_active=True, kol=kol_code, acc_year=acc_year).aggregate(Sum('curramount'))[
                'curramount__sum'] or 0
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

    level1 = []
    level2 = []
    level3 = []
    for l in AccCoding.objects.filter(level=1).order_by('code'):
        # filtercount=SanadDetail.objects.filter(is_active=False,kol=l.code).count()
        print(l.code, l.name)
        level1.append(
            {
                'code': l.code,
                'name': l.name,
                # 'filtercount':filtercount,

            }
        )

    context = {
        'year': year,
        'balance_data': balance_data,
        'level': 1,
        'level1': level1,
        'level2': level2,
        'level3': level3,
        'total_bed': total_bed,
        'total_bes': total_bes,
        'total_curramount': total_curramount,
    }
    return render(request, 'balance_sheet.html', context)


def balance_sheet_moin(request,year, kol_code):
    name = 'تراز آزمایشی | معین'
    result = page_permision(request, name)  # بررسی دسترسی
    if result:  # اگر هدایت انجام شده است
        return result
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
    acc_year = year
    moin_codes = SanadDetail.objects.filter(kol=kol_code).values('moin').distinct()
    balance_data = []
    total_bed = 0
    total_bes = 0
    total_curramount = 0

    for moin in moin_codes:
        moin_code = moin['moin']
        moin_name = None
        if AccCoding.objects.filter(code=moin_code, level=2, parent__code=kol_code):
            moin_name = AccCoding.objects.filter(code=moin_code, level=2, parent__code=kol_code).first().name
        if not moin_name:
            par = AccCoding.objects.filter(code=kol_code, level=1).last()
            AccCoding.objects.create(code=moin_code, level=2, parent=par, name='تعیین نشده')
        moin_name = AccCoding.objects.filter(code=moin_code, level=2, parent__code=kol_code).first().name
        bed_sum = SanadDetail.objects.filter(is_active=True, kol=kol_code, moin=moin_code, acc_year=acc_year).aggregate(
            Sum('bed'))[
                      'bed__sum'] or 0
        bes_sum = SanadDetail.objects.filter(is_active=True, kol=kol_code, moin=moin_code, acc_year=acc_year).aggregate(
            Sum('bes'))[
                      'bes__sum'] or 0
        curramount_sum = \
            SanadDetail.objects.filter(is_active=True, kol=kol_code, moin=moin_code, acc_year=acc_year).aggregate(
                Sum('curramount'))[
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
    kol_name = AccCoding.objects.filter(level=1, code=kol_code).last().name
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

    for l in AccCoding.objects.filter(level=2, parent__code=kol_code).order_by('code'):
        print(l.code, l.name)
        level2.append(
            {
                'code': l.code,
                'name': l.name,

            }
        )

    context = {
        'year': year,
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
        'total_bed': total_bed,
        'total_bes': total_bes,
        'total_curramount': total_curramount,

    }
    return render(request, 'balance_sheet.html', context)



def balance_sheet_tafsili(request, year, kol_code, moin_code):
    # بررسی مجوز
    name = 'تراز آزمایشی | تفصیلی'
    result = page_permision(request, name)
    if result:
        return result

    # تعیین سال حساب
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
    if year:
        acc_year = year

    # جمع‌آوری کدهای tafsili بدون تکرار
    tafsili_codes = SanadDetail.objects.filter(kol=kol_code, moin=moin_code).values_list('tafzili', flat=True).distinct()

    total_bed = total_bes = total_curramount = 0
    balance_data = []
    level3 = []

    # برای هر کد tafsili، نام و مقدارهای مربوطه را جمع‌آوری می‌کنیم
    for tafsili_code in tafsili_codes:
        # تعیین نام بر اساس نوع کد
        try:
            if int(kol_code) == 103:
                person = Person.objects.filter(per_taf=int(tafsili_code)).last()
                tafsili_name = f'{person.name} {person.lname}' if person else ''
            elif int(kol_code) == 102 or int(kol_code) == 500:
                kala = Kala.objects.filter(kala_taf=int(tafsili_code)).last()
                tafsili_name = kala.name if kala else ''
            else:
                acc = AccCoding.objects.filter(
                    level=3,
                    parent__code=int(moin_code),
                    parent__parent__code=int(kol_code),
                    code=int(tafsili_code)
                ).last()
                tafsili_name = acc.name if acc else ''
        except:
            tafsili_name = ''

        # افزودن به لیست سطح ۳
        level3.append({'code': tafsili_code, 'name': tafsili_name})

        # جمع مقادیر با یک Query برای هر tafsili
        aggregates = SanadDetail.objects.filter(
            is_active=True,
            kol=kol_code,
            moin=moin_code,
            tafzili=tafsili_code,
            acc_year=acc_year
        ).aggregate(
            bed_sum=Sum('bed'),
            bes_sum=Sum('bes'),
            curramount_sum=Sum('curramount')
        )

        bed_sum = aggregates['bed_sum'] or 0
        bes_sum = aggregates['bes_sum'] or 0
        curramount_sum = aggregates['curramount_sum'] or 0

        # جمع کل
        total_bed += bed_sum
        total_bes += bes_sum
        total_curramount += curramount_sum

        # افزودن به لیست نهایی
        balance_data.append({
            'tafzili_code': tafsili_code,
            'tafsili_name': tafsili_name,
            'bed_sum': bed_sum,
            'bes_sum': bes_sum,
            'curramount_sum': curramount_sum,
        })

    # نام کل کلید
    kol_item = AccCoding.objects.filter(level=1, code=kol_code).last()
    kol_name = kol_item.name if kol_item else ''

    # ساخت لیست‌های سطح ۱ و ۲
    level1 = [
        {'code': item.code, 'name': item.name}
        for item in AccCoding.objects.filter(level=1).order_by('code')
    ]
    level2 = [
        {'code': item.code, 'name': item.name}
        for item in AccCoding.objects.filter(level=2, parent__code=kol_code).order_by('code')
    ]

    # جمع‌آوری tafziliها برای ساخت لیست کامل
    sanads = SanadDetail.objects.filter(kol=kol_code, moin=moin_code, acc_year=acc_year)
    tafzili_set = sorted(set(sanads.values_list('tafzili', flat=True)))

    # ساخت context نهایی
    context = {
        'year': year,
        'balance_data': balance_data,
        'level': 3,
        'moin_code': moin_code,
        'kol_code': kol_code,
        'level_name': 'تفضیلی',
        'parent_code': moin_code,
        'parent_name': AccCoding.objects.filter(code=moin_code, level=2, parent__code=kol_code).first().name,

        'level1': level1,
        'level2': level2,
        'level3': level3,
        'total_bed': total_bed,
        'total_bes': total_bes,
        'total_curramount': total_curramount,
    }
    return render(request, 'balance_sheet.html', context)





def balance_sheet_tafsili2(request,year, kol_code, moin_code):
    name = 'تراز آزمایشی | تفصیلی'
    result = page_permision(request, name)  # بررسی دسترسی
    if result:  # اگر هدایت انجام شده است
        return result
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
    acc_year = year
    tafsili_codes = SanadDetail.objects.filter(kol=kol_code, moin=moin_code).values('tafzili').distinct()
    balance_data = []
    total_bed = 0
    total_bes = 0
    total_curramount = 0
    level3=[]
    for tafsili in tafsili_codes:
        tafsili_code = tafsili['tafzili']
        tafsili_name = ''

        if int(kol_code) == 103:
            try:
                tafsili_name=f'{Person.objects.filter(code=int(tafsili_code)).last().name} {Person.objects.filter(code=int(tafsili_code)).last().lname}'
                print('tafsili_name b', tafsili_name)
            except:
                pass
        elif int(kol_code) == 102:
            try:
                tafsili_name=Kala.objects.filter(kala_taf=int(tafsili_code)).last().name
                print('tafsili_name c', tafsili_name)
            except:
                pass

        else:
            try:
                tafsili_name =AccCoding.objects.filter(level=3,parent__code=int(moin_code),parent__parent__code=int(kol_code),code=int(tafsili_code)).last().name
                print('tafsili_name a',tafsili_name)
            except:
                pass


        level3.append(
            {
                'code': tafsili_code,
                'name': tafsili_name,

            }
        )




        bed_sum = \
            SanadDetail.objects.filter(is_active=True, kol=kol_code, moin=moin_code, tafzili=tafsili_code,
                                       acc_year=acc_year).aggregate(
                Sum('bed'))['bed__sum'] or 0
        bes_sum = \
            SanadDetail.objects.filter(is_active=True, kol=kol_code, moin=moin_code, tafzili=tafsili_code,
                                       acc_year=acc_year).aggregate(
                Sum('bes'))['bes__sum'] or 0
        curramount_sum = \
            SanadDetail.objects.filter(is_active=True, kol=kol_code, moin=moin_code, tafzili=tafsili_code,
                                       acc_year=acc_year).aggregate(
                Sum('curramount'))['curramount__sum'] or 0

        total_bed += bed_sum
        total_bes += bes_sum
        total_curramount += curramount_sum
        balance_data.append({
            'tafzili_code': tafsili_code,
            'tafsili_name': tafsili_name,
            'bed_sum': bed_sum,
            'bes_sum': bes_sum,
            'curramount_sum': curramount_sum,
        })

    kol_name = AccCoding.objects.filter(level=1, code=kol_code).last().name
    level1 = []
    level2 = []
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



    # فیلتر کردن داده‌ها
    sanads = SanadDetail.objects.filter(kol=kol_code, moin=moin_code, acc_year=acc_year)

    # استفاده از مجموعه برای حذف تکراری‌ها و سپس تبدیل به لیست مرتب‌شده
    tafzili_set = sorted({s.tafzili for s in sanads})

    # # ایجاد لیست level3
    # for tafzili_code in tafzili_set:
    #     print(tafzili_code)
    #     try:
    #         taf_name=AccCoding.objects.filter(level=3, parent__code=moin_code, parent__parent__code=kol_code,code=tafzili_code).last().name
    #     except:
    #         taf_name=' '
    #
    #
    #
    #
    #
    #     level3.append(
    #         {
    #             'code': tafzili_code,
    #             'name': taf_name,
    #
    #         }
    #     )


    context = {
        'year': year,
        'balance_data': balance_data,
        'level': 3,
        'moin_code': moin_code,
        'kol_code': kol_code,
        'level_name': 'تفضیلی',
        'parent_code': moin_code,
        'parent_name': AccCoding.objects.filter(code=moin_code, level=2, parent__code=kol_code).first().name,


        'level1': level1,
        'level2': level2,
        'level3': level3,
        'total_bed': total_bed,
        'total_bes': total_bes,
        'total_curramount': total_curramount,
    }
    return render(request, 'balance_sheet.html', context)

from django.db.models import OuterRef, Subquery

def SanadTotal(request,year, *args, **kwargs):
    name = 'کل اسناد'
    result = page_permision(request, name)  # بررسی دسترسی
    if result:  # اگر هدایت انجام شده است
        return result
    kol_code = kwargs['kol_code']
    moin_code = kwargs['moin_code']
    tafzili_code = kwargs['tafzili_code']
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
    acc_year = year
    sanads = SanadDetail.objects.filter(kol=kol_code, moin=moin_code, tafzili=tafzili_code, acc_year=acc_year)

    # # فرض می‌کنیم، مدل Kala و SanadDetail دارید و می‌خواهید نام کالا را
    # kala_subquery = Kala.objects.filter(kala_taf=OuterRef('tafzili')).values('name')[:1]
    #
    # # حالا در query خوانده شده، آن را با annotate() اضافه می‌کنید
    # sanads = SanadDetail.objects.filter(kol=kol_code, moin=moin_code, tafzili=tafzili_code, acc_year=acc_year).annotate(
    #     kala_name=Subquery(kala_subquery)
    # )
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


    # جمع‌آوری کدهای tafsili بدون تکرار
    tafsili_codes = SanadDetail.objects.filter(kol=kol_code, moin=moin_code).values_list('tafzili', flat=True).distinct()

    level3 = []

    # برای هر کد tafsili، نام و مقدارهای مربوطه را جمع‌آوری می‌کنیم
    for tafsili_code in tafsili_codes:
        # تعیین نام بر اساس نوع کد
        try:
            if int(kol_code) == 103:
                person = Person.objects.filter(per_taf=int(tafsili_code)).last()
                tafsili_name = f'{person.name} {person.lname}' if person else ''
                print('person:',tafsili_name)
            elif int(kol_code) == 102 or int(kol_code) == 500:
                kala = Kala.objects.filter(kala_taf=int(tafsili_code)).last()
                tafsili_name = kala.name if kala else ''
                print('kala:',tafsili_name)
            else:
                acc = AccCoding.objects.filter(
                    level=3,
                    parent__code=int(moin_code),
                    parent__parent__code=int(kol_code),
                    code=int(tafsili_code)
                ).last()
                tafsili_name = acc.name if acc else ''
        except:
            tafsili_name = ''

        # افزودن به لیست سطح ۳
        level3.append({'code': tafsili_code, 'name': tafsili_name})


    level = 4

    print(level, kol_code, moin_code, tafzili_code)
    bed_sum = SanadDetail.objects.filter(is_active=True, kol=kol_code, moin=moin_code, tafzili=tafzili_code,
                                         acc_year=acc_year).aggregate(Sum('bed'))[
        'bed__sum']
    bes_sum = SanadDetail.objects.filter(is_active=True, kol=kol_code, moin=moin_code, tafzili=tafzili_code,
                                         acc_year=acc_year).aggregate(Sum('bes'))[
        'bes__sum']
    curramount_sum = \
        SanadDetail.objects.filter(is_active=True, kol=kol_code, moin=moin_code, tafzili=tafzili_code,
                                   acc_year=acc_year).aggregate(Sum('curramount'))[
            'curramount__sum']

    context = {
        'year': year,
        'level': level,
        'sanads': sanads,
        'kol_code': int(kol_code),
        'moin_code': int(moin_code),
        'tafzili_code': int(tafzili_code),
        'level1': level1,
        'level2': level2,
        'level3': level3,
        'total_bed': bed_sum,
        'total_bes': bes_sum,
        'total_curramount': curramount_sum,

    }

    return render(request, 'sanad_total.html', context)


import locale

# تنظیم محلی برای جداسازی اعداد با کاما
locale.setlocale(locale.LC_ALL, 'fa_IR.UTF-8')

import locale

# تنظیم محلی برای جداسازی اعداد با کاما
locale.setlocale(locale.LC_ALL, 'fa_IR.UTF-8')

from django.shortcuts import render
from django.db.models import Sum
import locale

# تنظیم محلی برای جداسازی اعداد با کاما
locale.setlocale(locale.LC_ALL, 'fa_IR.UTF-8')

from django.shortcuts import render
from django.db.models import Sum
import locale

# تنظیم محلی برای جداسازی اعداد با کاما
locale.setlocale(locale.LC_ALL, 'fa_IR.UTF-8')


def BedehkaranMoshtarian(request, state):
    # محاسبه مجموع curramount بر اساس tafzili
    tafzili_sums = SanadDetail.objects.filter(moin=1, kol=103).values('tafzili').annotate(
        total_curramount=Sum('curramount'))

    # جمع‌آوری داده‌ها برای نمایش در قالب جدول
    report_data = []
    total_amount = 0

    for tafzili_sum in tafzili_sums:
        tafzili_code = tafzili_sum['tafzili']
        total_curramount = tafzili_sum['total_curramount']

        # پیدا کردن فرد مربوط به tafzili_code
        person = Person.objects.filter(per_taf=tafzili_code).first()
        person_data = {
            'tafzili': tafzili_code,
            'total_curramount': total_curramount,
            'name': '',
            'lname': '',
            'loans': [],
            'sum_amount': 0,
            'total_with_loans': 0,
            'person_not_found': False,
            'no_loans': False
        }

        if person:
            person_data['name'] = person.name
            person_data['lname'] = person.lname

            # پیدا کردن وام‌های شخص
            loans = Loan.objects.filter(person=person)
            if loans.exists():
                person_data['loans'] = [
                    {
                        'code': loan.code,
                        'tarikh': loan.tarikh,
                        'cost': loan.cost
                    }
                    for loan in loans
                ]
                person_data['sum_amount'] = sum(loan['cost'] for loan in person_data['loans'])
            else:
                person_data['no_loans'] = True
        else:
            person_data['person_not_found'] = True

        person_data['total_with_loans'] = person_data['sum_amount'] + total_curramount

        # اعمال شرایط بر اساس state
        if (state == '1' and total_curramount > 0) or \
                (state == '2' and total_curramount == 0 and person_data['sum_amount'] == 0) or \
                (state == '3' and total_curramount == 0 and person_data['sum_amount'] > 0) or \
                (state == '4' and total_curramount < 0 and person_data['sum_amount'] == 0) or \
                (state == '5' and total_curramount < 0 and person_data['sum_amount'] > 0 and person_data[
                    'total_with_loans'] > 0) or \
                (state == '6' and total_curramount < 0 and person_data['sum_amount'] > 0 and person_data[
                    'total_with_loans'] < 0):
            total_amount += person_data['total_with_loans']
            report_data.append(person_data)

    context = {
        'report_data': report_data,
        'total_amount': locale.format_string("%d", total_amount, grouping=True)
    }
    return render(request, 'bedehkaran_moshtarian.html', context)


def JariAshkhasMoshtarian(request):
    name = 'حساب مشتریان'
    result = page_permision(request, name)  # بررسی دسترسی
    if result:  # اگر هدایت انجام شده است
        return result
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='حساب مشتریان', code=0)

    start_time = time.time()  # زمان شروع تابع

    filters = [
        {'filter': {'total_mandeh__gt': 0 ,'moin':1}, 'negate': False},
        {'filter': {'total_mandeh__gt': 0,'moin':1, 'loans_total__gt': 0}, 'negate': False},
        {'filter': {'total_mandeh__gt': 0,'moin':1, 'loans_total': 0}, 'negate': False},
        {'filter': {'total_mandeh__lt': 0,'moin':1}, 'negate': True},
        {'filter': {'total_mandeh__lt': 0,'moin':1, 'loans_total__gt': 0}, 'negate': True},
        {'filter': {'total_mandeh__lt': 0,'moin':1, 'loans_total': 0}, 'negate': True},
    ]

    table1 = []
    for f in filters:
        total_mandeh = BedehiMoshtari.objects.filter(**f['filter']).aggregate(total_mandeh=Sum('total_mandeh'))[
                           'total_mandeh'] or 0
        if f['negate']:
            total_mandeh = -total_mandeh
        table1.append(total_mandeh / 10000000)
    # 6 مانده کل
    table1.append((BedehiMoshtari.objects.aggregate(total_mandeh=Sum('total_mandeh'))['total_mandeh'] or 0) / 10000000)
    # 7 وام دار بی حساب
    table1.append((BedehiMoshtari.objects.filter(total_mandeh=0, loans_total__gt=0).aggregate(
        loans_total=Sum('loans_total'))['loans_total'] or 0) / 10000000)

    # 8 وام دار - کمبود وام
    table1.append(-(
            BedehiMoshtari.objects.filter(total_mandeh__lt=0, loans_total__gt=0, total_with_loans__lt=0).aggregate(
                total_with_loans=Sum('total_with_loans'))['total_with_loans'] or 0) / 10000000)
    today = timezone.now().date()
    # 9 قسط عقب افتاده
    total_cost = LoanDetil.objects.filter(
        complete_percent__lt=1,  # فرض کنیم درصد کامل باید کمتر از 100 باشد
        date__lt=today
    ).annotate(
        adjusted_cost=F('cost') * (1 - Cast(F('complete_percent'), DecimalField(max_digits=5, decimal_places=2)))
        # تبدیل complete_percent به Decimal
    ).aggregate(
        total_adjusted_cost=Sum('adjusted_cost')
    )['total_adjusted_cost'] or 0

    # تقسیم بر 10,000,000
    final_result = total_cost / 10000000
    # 9 قسط عقب افتاده
    table1.append(final_result)

    # 10 اقساط امروز به بعد
    total_cost = LoanDetil.objects.filter(
        complete_percent__lt=1,  # فرض کنیم درصد کامل باید کمتر از 100 باشد
        date__gte=today
    ).annotate(
        adjusted_cost=F('cost') * (1 - Cast(F('complete_percent'), DecimalField(max_digits=5, decimal_places=2)))
        # تبدیل complete_percent به Decimal
    ).aggregate(
        total_adjusted_cost=Sum('adjusted_cost')
    )['total_adjusted_cost'] or 0

    # تقسیم بر 10,000,000
    final_result = total_cost / 10000000
    # 10 اقساط امروز به بعد
    table1.append(final_result)

    # تقویم اقساط و بدهی ها
    # تبدیل تاریخ امروز به شمسی
    today_jalali = jdate.fromgregorian(date=today)
    current_jalali_year = today_jalali.year
    months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    # تبدیل تاریخ امروز به شمسی
    today_jalali = jdate.fromgregorian(date=today)
    current_jalali_year = today_jalali.year

    # محاسبه مجموع مانده چک‌های سال‌های قبل و بعد
    first_day_of_current_year_jalali = jdate(current_jalali_year, 1, 1).togregorian()
    last_day_of_current_year_jalali = jdate(current_jalali_year, 12, 29).togregorian()

    monthly_data = []
    for month in range(1, 13):
        first_day_of_month_jalali = jdate(current_jalali_year, month, 1).togregorian()
        last_day_of_month_jalali = (
            jdate(current_jalali_year, month + 1, 1).togregorian() - timedelta(days=1) if month < 12 else jdate(
                current_jalali_year + 1, 1, 1).togregorian() - timedelta(days=1))

        # total_mandeh_month = ChequesPay.objects.filter(
        total_loans_month = LoanDetil.objects.filter(
            date__gte=first_day_of_month_jalali,
            date__lte=last_day_of_month_jalali,
            complete_percent__lt=1
        ).aggregate(cost=Sum('cost'))['cost'] or 0

        monthly_data.append({
            'month_name': months[month - 1],
            'total_count': float(total_loans_month) / 10000000
        })
    print(f"5: {time.time() - start_time:.2f} ثانیه")
    no_loan = \
        BedehiMoshtari.objects.filter(total_mandeh__lt=0, loans_total=0).aggregate(total_mandeh=Sum('total_mandeh'))[
            'total_mandeh'] or 0
    loan_gap = BedehiMoshtari.objects.filter(total_mandeh__lt=0, loans_total__gt=0, total_with_loans__lt=0).aggregate(
        total_with_loans=Sum('total_with_loans'))['total_with_loans'] or 0

    loan_before_current_year = LoanDetil.objects.filter(
        date__lt=first_day_of_current_year_jalali,
        complete_percent__lt=1
    ).aggregate(
        cost=Sum('cost'))['cost'] or 0

    loan_after_current_year = LoanDetil.objects.filter(
        date__gt=last_day_of_current_year_jalali,
        complete_percent__lt=1
    ).aggregate(
        cost=Sum('cost'))['cost'] or 0

    chart_data = [
        {'month_name': 'بدون وام', 'total_count': float(no_loan) * -1 / 10000000},
        {'month_name': 'کمبود وام', 'total_count': float(loan_gap) * -1 / 10000000},
        {'month_name': 'معوق سال های قبل', 'total_count': float(loan_after_current_year) / 10000000},
        *monthly_data,
        {'month_name': 'سال های بعد', 'total_count': float(loan_after_current_year) / 10000000},
    ]
    print(f"6: {time.time() - start_time:.2f} ثانیه")

    # loans = Loan.objects.all()
    loans = Loan.objects.annotate(
        from_last_daryaft=Subquery(
            BedehiMoshtari.objects.filter(person=OuterRef("person")).values('from_last_daryaft')[:1]
        )
    )

    context = {
        'title': 'حساب مشتریان',
        'user': user,
        'table1': table1,
        'chartmahanedata': chart_data,
        'loans': loans,
    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'jari_ashkhas_moshtarian.html', context)


from django.db.models import F, Func

from django.db.models import F, Func


def JariAshkhasMoshtarianDetail(request, filter_id):
    filters = {
        '1': {'total_mandeh__gt': 0,'moin':1},
        '2': {'total_mandeh__gt': 0,'moin':1, 'loans_total__gt': 0},
        '3': {'total_mandeh__gt': 0, 'loans_total': 0,'moin':1},
        '4': {'total_mandeh__lt': 0,'moin':1},
        '5': {'total_mandeh__lt': 0 ,'moin':1, 'loans_total__gt': 0},
        '6': {'total_mandeh__lt': 0, 'loans_total': 0,'moin':1},
        '7': {'total_mandeh__lt': 0, 'loans_total__gt': 0, 'total_with_loans__lt': 0,'moin':1},
        '8': {'total_mandeh': 0, 'loans_total__gt': 0,'moin':1},
    }

    filter_labels = {
        '1': 'مشتری‌های بستانکار',
        '2': 'مشتری‌های بستانکار | دارای وام',
        '3': 'مشتری‌های بستانکار | بدون وام',
        '4': 'مشتریان بدهکار',
        '5': 'مشتریان بدهکار | دارای وام',
        '6': 'مشتریان بدهکار | بدون وام',
        '7': 'مشتریان بدهکار | کمبود وام',
        '8': 'مشتریان بی حساب | دارای وام'

    }

    filter_criteria = filters.get(str(filter_id), {})
    items = BedehiMoshtari.objects.filter(**filter_criteria).annotate(
        abs_total_mandeh=Func(F('total_mandeh'), function='ABS')).order_by('-abs_total_mandeh')

    context = {
        'title': f'جزئیات حساب مشتریان - {filter_labels.get(str(filter_id), "فیلتر نامشخص")}',
        'items': items,
    }




    return render(request, 'jari_ashkhas_moshtarian_detail.html', context)


from django.utils import timezone
from collections import defaultdict
from django.utils import timezone
from django.utils import timezone
from collections import defaultdict


@login_required(login_url='/login')
def HesabMoshtariDetail1(request, tafsili):
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='حساب مشتری', code=0)

    hesabmoshtari = BedehiMoshtari.objects.filter(tafzili=tafsili).last()
    today = timezone.now().date()
    asnad = SanadDetail.objects.filter(kol=103, moin=1, tafzili=tafsili).order_by('acc_year', 'date', 'code', 'radif')

    chart_data = defaultdict(lambda: {'value': 0})

    for item in asnad:
        g_date = item.date.strftime('%Y-%m-%d')  # فرمت تاریخ به ISO

        # محاسبه مقدار تجمعی
        chart_data[g_date]['value'] += item.curramount if item.curramount else 0

    # اکنون با داده‌های جمع‌آوری شده به فرمت مناسب برای Chart.js
    labels = list(chart_data.keys())  # تاریخ‌ها به عنوان لیبل
    data_values = [data['value'] for data in chart_data.values()]  # مقادیر تجمعی

    context = {
        'title': 'حساب مشتری',
        'hesabmoshtari': hesabmoshtari,
        'today': today,
        'asnad': asnad,
        'final_chart_data': [{'date': date, 'value': data['value']} for date, data in chart_data.items()],

        'labels': labels,
        'data_values': data_values,
    }

    return render(request, 'moshrari_detail.html', context)


import re


from django.shortcuts import render, redirect
from django.db.models import Sum, Min, Max
import jdatetime
from decimal import Decimal


@login_required(login_url='/login')
def HesabMoshtariDetail0524(request, tafsili):
    start_time = time.time()  # زمان شروع تابع

    name = 'جزئیات حساب مشتری'
    result = page_permision(request, name)  # بررسی دسترسی
    if result:  # اگر هدایت انجام شده است
        return result
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='حساب مشتری', code=tafsili)

    today = timezone.now().date()
    # asnad = SanadDetail.objects.filter(kol=103, moin=1, tafzili=tafsili).order_by('date')
    asnad = SanadDetail.objects.filter(kol=103, tafzili=tafsili,is_active=True).order_by('date')
    mandeh=0
    for s in asnad:
        s.mandeh=mandeh+s.curramount
        mandeh+=s.curramount


    # =========================================ایجاد نمودار گردش حساب مشتری
    master_info = MasterInfo.objects.filter(is_active=True).last()
    year_list=[]
    for m in MasterInfo.objects.order_by('acc_year').all():
        year_list.append(m.acc_year)

    acc_year = master_info.acc_year
    base_year = acc_year - 1

    start_date = SanadDetail.objects.filter(acc_year=base_year).aggregate(min_date=Min('date'))['min_date']
    end_date = SanadDetail.objects.filter(acc_year=base_year).aggregate(max_date=Max('date'))['max_date']

    # ایجاد لیست روزها
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date.strftime('%Y-%m-%d'))  # قالب تاریخ به YYYY-MM-DD
        current_date += timedelta(days=1)
    acc_date_list = [datetime.strptime(date, '%Y-%m-%d') + relativedelta(years=1) for date in date_list]
    acc_date_list = [date.strftime('%Y-%m-%d') for date in acc_date_list]


    chart_labels_shamsi = []
    for date in acc_date_list:
        try:
            miladi_date = datetime.strptime(date, '%Y-%m-%d')  # تبدیل میلادی به datetime
            shamsi_date = jdatetime.date.fromgregorian(day=miladi_date.day, month=miladi_date.month,
                                                       year=miladi_date.year)

            chart_labels_shamsi.append(shamsi_date.strftime('%Y-%m-%d'))

        except ValueError as e:
            print(f"خطای تبدیل تاریخ: {date}, {e}")  # نمایش خطا در صورت وجود مشکل

    chart_labels = chart_labels_shamsi  # برچسب‌های نمودار همان لیست تاریخ‌ها

    today = datetime.today().strftime('%Y-%m-%d')

    chart_date=[]
    l_start=False
    l_finish=False
    acc_days=0
    for y in year_list:
        print(y)
        delta_yar=y-acc_year
        print('delta_yar',delta_yar)
        daily_totals_year = {}
        sanad_year_qs = asnad.filter(acc_year=y).exclude(sharh__contains='بستن حساب هاي دارائي')

        print('sanad_year_qs.count()',sanad_year_qs.count())
        for k in sanad_year_qs:
            print('______________')
            print(k.sharh)
            print(k.syscomment)
        results = asnad.filter(acc_year=y).values('date').annotate(total=Sum('curramount')).order_by('date')
        print('نتایج برای سال:', y)
        print('تعداد نتایج:', len(results))
        for r in results:
            print(r)
        for s in sanad_year_qs:
            print('==>',s.date, s.curramount)
        if sanad_year_qs.exists():
            for item in sanad_year_qs.values('date').annotate(total=Sum('curramount')).order_by('date'):
                print("item[total]",item['total'])
                daily_totals_year[str(item['date'])] = float(item['total'] or 0)

        chart_y=[]
        cumulative_year = 0
        for day in acc_date_list:
            by_date = datetime.strptime(day, '%Y-%m-%d') + relativedelta(years=delta_yar)  # تاریخ مربوط به سال پایه
            if (not l_finish) and (day > today) and (y == acc_year):
                l_finish = True


            # مقدار روز جاری از سال پایه را دریافت و تجمعی محاسبه کن
            if str(by_date.date()) in daily_totals_year:
                a = daily_totals_year[str(by_date.date())]
                print('a', a)
                if (not l_start) and (int(daily_totals_year[str(by_date.date())]) != 0):
                    print('l_start = True',int(daily_totals_year[str(by_date.date())]))
                    l_start = True




                cumulative_year += daily_totals_year[str(by_date.date())]  # علامت منفی برای تصحیح

            if l_start and not l_finish:
                chart_y.append(cumulative_year)
                acc_days+=1
            else:
                chart_y.append('-')

        chart_date.append(chart_y)

    sum_line=0
    count_line=0
    for chart_y in chart_date:
        numeric_values = [value for value in chart_y if value != '-']
        sum_line += sum(numeric_values)
        count_line += len(numeric_values)

    if count_line>0:
        ave=sum_line/count_line
    else:
        ave=0

    average_line = [ave for _ in range(len(acc_date_list))]
    chart_date.insert(0, average_line)
    year_list.insert(0, 'میانگین')


    hesabmoshtari = BedehiMoshtari.objects.filter(tafzili=tafsili).last()

    m_name = None

    if request.method == 'POST':
        action = request.POST.get('action')  # دریافت نام دکمه کلیک شده
        print('action', action)

        if action == 'send_sms':
            form = SMSTrackingForm(request.POST, customer=hesabmoshtari)
            print('پیامک/////////////////////////1')

            if form.is_valid():
                phone_number = form.cleaned_data.get('phone_number')
                sample_sms = form.cleaned_data.get('sample_sms')
                message = form.cleaned_data.get('message')

                if not sample_sms and not message:
                    form.add_error('message', "حداقل یکی از فیلدهای متن پیامک یا پیامک نمونه باید مقدار داشته باشد.")
                else:
                    message_to_send = 'مشتری گرامی'
                    message_to_send += f"\n{hesabmoshtari.person.clname}\n"
                    message_to_send += sample_sms.text if sample_sms else ""
                    if message:
                        message_to_send += f"\n{message}"

                    # ارسال پیامک و دریافت `message_id`
                    message_id = send_sms(user.mobile_number, message_to_send)
                    # message_id = send_sms(phone_number, message_to_send)

                    if message_id:
                        # پیدا کردن نوع پیگیری "پیامک"
                        try:
                            track_kind = TrackKinde.objects.get(kind_name="پیامک")
                            print('تماس پیامک/////////////////////////2')

                        except TrackKinde.DoesNotExist:
                            track_kind = None
                            form.add_error(None, "نوع پیگیری 'پیامک' در سیستم وجود ندارد.")

                        if track_kind:
                            tracking = form.save(commit=False)
                            tracking.customer = hesabmoshtari
                            tracking.message_to_send = message_to_send
                            tracking.created_by = user if user.is_authenticated else None
                            tracking.track_kind = track_kind
                            tracking.message_id = message_id  # ⬅️ ذخیره `message_id`
                            tracking.save()

                        return redirect(f'/acc/jariashkhas/moshtari/{tafsili}')  # هدایت به صفحه مناسب

                    else:
                        form.add_error('phone_number', "ارسال پیامک موفقیت‌آمیز نبود. لطفاً دوباره تلاش کنید.")


        elif action == 'track_call':
            print('تماس تلفنی/////////////////////////0')
            form = CallTrackingForm(request.POST, customer=hesabmoshtari)
            if form.is_valid():
                print('تماس تلفنی/////////////////////////1')
                try:
                    track_kind = TrackKinde.objects.get(kind_name="تماس تلفنی")
                    print('تماس تلفنی/////////////////////////2')
                except TrackKinde.DoesNotExist:
                    print('تماس تلفنی/////////////////////////3')
                    track_kind = None
                    form.add_error(None, "نوع پیگیری 'تماس تلفنی' در سیستم وجود ندارد.")

                if track_kind:
                    print('تماس تلفنی/////////////////////////4')
                    tracking = form.save(commit=False)
                    tracking.customer = hesabmoshtari
                    tracking.track_kind = track_kind
                    tracking.created_by = request.user
                    tracking.call_duration = int(request.POST.get('call_duration', 0))  # ذخیره مدت تماس
                    tracking.phone_number = form.cleaned_data.get('phone_number')
                    # 🔹 محاسبه زمان یادآوری بعدی

                    tracking.next_reminder_date = form.cleaned_data['next_reminder_date']

                    tracking.save()

                return redirect(f'/acc/jariashkhas/moshtari/{tafsili}')
            else:
                print('form call not valiid')
                print(form.errors)  # 🔎 مشاهده خطاهای فرم


    else:
        sms_form = SMSTrackingForm(customer=hesabmoshtari)
        call_form = CallTrackingForm(customer=hesabmoshtari)

    sms_form = SMSTrackingForm(customer=hesabmoshtari)
    call_form = CallTrackingForm(customer=hesabmoshtari)
    tracking = Tracking.objects.filter(customer=hesabmoshtari).order_by('-id')
    for t in tracking:
        try:
            if t.message_id and t.status_code != 2 and t.status_code != 3 and t.status_code != 4:
                status_code = check_sms_status(t.message_id)
                if status_code is not None:  # فقط اگر مقدار معتبر باشد، ذخیره شود
                    t.status_code = status_code
                    t.save()
        except:
            pass

    monthly_rate=master_info.monthly_rate
    khab=True
    if hesabmoshtari.sleep_investment and hesabmoshtari.sleep_investment >= 0:
        khab=False
    try:
        bar_mali=hesabmoshtari.sleep_investment/Decimal(30) * monthly_rate / Decimal(100)
    except:
        bar_mali=0
    person=Person.objects.filter(per_taf=tafsili).last()
    amani=None
    if person:
        per_code=person.code
        amani=GoodConsign.objects.filter(per_code=per_code)


    context = {
        'title': 'حساب مشتری',
        'hesabmoshtari': hesabmoshtari,
        'user': user,
        'today': today,
        'asnad': asnad,
        'm_name': m_name,
        'sms_form': sms_form,  # ارسال فرم به قالب
        'call_form': call_form,  # ارسال فرم به قالب
        'tracking': tracking,
        'khab': khab,
        'acc_days': acc_days,
        'ave': ave,
        'khab2': acc_days*ave/10,
        'bar_mali': bar_mali,


        'chart_labels': chart_labels,
        'chart_date': chart_date,
        'year_list': year_list,

        'amani': amani,


    }
    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")
    # return render(request, 'moshrari_detail.html', context)
    return render(request, 'master_moshrari_detail.html', context)

from django.core.cache import cache
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from jdatetime import date as jdate
from django.db.models import Sum, Min, Max
from django.core.cache import cache
import time
import re


# byqwen 1404.05.14
@login_required(login_url='/login')
def HesabMoshtariDetail(request, tafsili):
    start_time = time.time()

    # بررسی دسترسی
    name = 'جزئیات حساب مشتری'
    result = page_permision(request, name)
    if result:
        return result

    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='حساب مشتری', code=tafsili)

    # کش MasterInfo
    master_info = cache.get('active_master_info')
    if not master_info:
        master_info = MasterInfo.objects.filter(is_active=True).last()
        if master_info:
            cache.set('active_master_info', master_info, 3600)  # 1 ساعت
    acc_year = master_info.acc_year
    base_year = acc_year - 1

    # گرفتن اسناد مشتری
    asnad_table = (SanadDetail.objects
             .filter(kol=103, tafzili=tafsili)
             .order_by('date'))

    asnad = (SanadDetail.objects
             .filter(kol=103, tafzili=tafsili, is_active=True)
             .exclude(sharh__contains='بستن حساب هاي دارائي')
             .order_by('date'))

    # محاسبه مانده تجمعی
    mandeh = 0
    for s in asnad:
        mandeh += s.curramount
        s.mandeh = mandeh



    mandeh = 0
    for s in asnad_table:
        mandeh += s.curramount
        s.mandeh = mandeh

    # جمع‌بندی داده‌ها بر اساس سال و تاریخ (برای نمودار)
    from collections import defaultdict
    yearly_data = defaultdict(lambda: defaultdict(float))
    for s in asnad:
        yearly_data[s.acc_year][str(s.date)] += float(s.curramount or 0)

    # محاسبه تاریخ‌های پایه (سال قبل)
    base_year_dates = SanadDetail.objects.filter(acc_year=base_year).aggregate(
        min_date=Min('date'),
        max_date=Max('date')
    )
    start_date = base_year_dates['min_date']
    end_date = base_year_dates['max_date']

    chart_labels = []
    chart_date = []
    year_list = []

    if start_date and end_date:
        # ساخت لیست تاریخ‌های سال پایه
        current = start_date
        date_list_miladi = []
        while current <= end_date:
            date_list_miladi.append(current)
            current += timedelta(days=1)

        # شیفت به سال جاری (acc_year): +1 سال
        acc_date_list_miladi = [d + relativedelta(years=1) for d in date_list_miladi]

        # تبدیل به شمسی برای نمایش
        chart_labels = [
            jdate.fromgregorian(date=d).strftime('%Y-%m-%d')
            for d in acc_date_list_miladi
        ]

        # ساخت خطوط نمودار برای هر سال
        year_list = sorted(yearly_data.keys())
        acc_days = 0

        for year in year_list:
            delta = year - acc_year
            daily_totals = yearly_data[year]
            cumulative = 0
            chart_y = []
            l_start = False
            l_finish = False

            for acc_date in acc_date_list_miladi:
                # تاریخ متناظر در سال `year`
                by_date = acc_date + relativedelta(years=delta)
                str_by_date = str(by_date)

                # متوقف در امروز (فقط برای سال جاری)
                if year == acc_year and not l_finish and acc_date > timezone.now().date():
                    l_finish = True

                # اگر داده‌ای در این تاریخ وجود داشت
                if str_by_date in daily_totals:
                    amount = daily_totals[str_by_date]
                    if not l_start and amount != 0:
                        l_start = True
                    if l_start and not l_finish:
                        cumulative += amount

                # اضافه کردن مقدار یا خط تیره
                if l_start and not l_finish:
                    chart_y.append(cumulative)
                    if year == acc_year:
                        acc_days += 1
                else:
                    chart_y.append('-')

            chart_date.append(chart_y)

        # محاسبه میانگین
        all_vals = [v for line in chart_date for v in line if v != '-']
        ave = sum(all_vals) / len(all_vals) if all_vals else 0
        average_line = [ave] * len(chart_labels)
        chart_date.insert(0, average_line)
        year_list.insert(0, 'میانگین')
    else:
        acc_days = 0
        ave = 0

    # گرفتن اطلاعات مشتری
    hesabmoshtari = (BedehiMoshtari.objects
                     .filter(tafzili=tafsili)
                     .select_related('person')
                     .last())

    person = hesabmoshtari.person if hesabmoshtari else None
    amani = GoodConsign.objects.filter(per_code=person.code) if person else None

    # فرم‌ها
    sms_form = SMSTrackingForm(customer=hesabmoshtari)
    call_form = CallTrackingForm(customer=hesabmoshtari)

    # پردازش POST
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'send_sms':
            sms_form = SMSTrackingForm(request.POST, customer=hesabmoshtari)
            if sms_form.is_valid():
                phone_number = sms_form.cleaned_data.get('phone_number')
                sample_sms = sms_form.cleaned_data.get('sample_sms')
                message = sms_form.cleaned_data.get('message')

                if not sample_sms and not message:
                    sms_form.add_error('message', "حداقل یکی از فیلدهای متن پیامک یا پیامک نمونه باید مقدار داشته باشد.")
                else:
                    message_to_send = f'مشتری گرامی\n{hesabmoshtari.person.clname}\n'
                    if sample_sms:
                        message_to_send += sample_sms.text
                    if message:
                        message_to_send += f'\n{message}'

                    # ارسال پیامک
                    if phone_number:
                        # message_id = send_sms(phone_number, message_to_send)
                        message_id = send_sms(user.mobile_number, message_to_send)

                    if message_id:
                        try:
                            track_kind = TrackKinde.objects.get(kind_name="پیامک")
                        except TrackKinde.DoesNotExist:
                            track_kind = None
                            sms_form.add_error(None, "نوع پیگیری 'پیامک' در سیستم وجود ندارد.")

                        if track_kind:
                            tracking = sms_form.save(commit=False)
                            tracking.customer = hesabmoshtari
                            tracking.message_to_send = message_to_send
                            tracking.created_by = user
                            tracking.track_kind = track_kind
                            tracking.message_id = message_id
                            tracking.save()
                            return redirect(f'/acc/jariashkhas/moshtari/{tafsili}')
                    else:
                        sms_form.add_error('phone_number', "ارسال پیامک موفقیت‌آمیز نبود.")

        elif action == 'track_call':
            call_form = CallTrackingForm(request.POST, customer=hesabmoshtari)
            if call_form.is_valid():
                try:
                    track_kind = TrackKinde.objects.get(kind_name="تماس تلفنی")
                except TrackKinde.DoesNotExist:
                    track_kind = None
                    call_form.add_error(None, "نوع پیگیری 'تماس تلفنی' در سیستم وجود ندارد.")

                if track_kind:
                    tracking = call_form.save(commit=False)
                    tracking.customer = hesabmoshtari
                    tracking.track_kind = track_kind
                    tracking.created_by = user
                    tracking.call_duration = int(request.POST.get('call_duration', 0))
                    tracking.phone_number = call_form.cleaned_data.get('phone_number')
                    tracking.next_reminder_date = call_form.cleaned_data['next_reminder_date']
                    tracking.save()
                    return redirect(f'/acc/jariashkhas/moshtari/{tafsili}')

    # دریافت رکوردهای پیگیری
    tracking = (Tracking.objects
                .filter(customer=hesabmoshtari)
                .select_related('track_kind', 'created_by')
                .order_by('-id'))

    # به‌روزرسانی وضعیت پیامک‌ها
    for t in tracking:
        if t.message_id and t.status_code not in [2, 3, 4]:
            try:
                status = check_sms_status(t.message_id)
                if status in [2, 3, 4]:
                    t.status_code = status
                    t.save()
            except:
                pass

    # محاسبات مالی
    monthly_rate = master_info.monthly_rate
    khab = True
    if hesabmoshtari.sleep_investment and hesabmoshtari.sleep_investment > 0:
        khab = False

    try:
        bar_mali = (hesabmoshtari.sleep_investment or 0) / 30 * monthly_rate / 100
    except:
        bar_mali = 0


    cheque_recive=ChequesRecieve.objects.filter(per_code=hesabmoshtari.person.code,total_mandeh__lt=0).order_by('cheque_date')
    cheque_pay=ChequesPay.objects.filter(per_code=hesabmoshtari.person.code,total_mandeh__gt=0).order_by('cheque_date')
    # محاسبه مجموع مانده چک‌های دریافتی
    result_receive = cheque_recive.aggregate(mandeh=Sum('total_mandeh'))
    cheque_receive_summary = abs(result_receive['mandeh']) if result_receive['mandeh'] is not None else None

    # محاسبه مجموع مانده چک‌های پرداختی
    result_pay = cheque_pay.aggregate(mandeh=Sum('total_mandeh'))
    cheque_pay_summary = abs(result_pay['mandeh']) if result_pay['mandeh'] is not None else None


    # context نهایی
    context = {
        'title': 'حساب مشتری',
        'hesabmoshtari': hesabmoshtari,
        'user': user,
        'today': timezone.now().date().isoformat(),
        'today2': timezone.now().date(),
        'asnad': asnad,
        'asnad_table': asnad_table,
        'm_name': None,
        'sms_form': sms_form,
        'call_form': call_form,
        'tracking': tracking,
        'khab': khab,
        'acc_days': acc_days,
        'ave': ave,
        'khab2': acc_days * ave / 10,
        'bar_mali': bar_mali,
        'chart_labels': chart_labels,
        'chart_date': chart_date,
        'year_list': year_list,
        'amani': amani,
        'cheque_recive': cheque_recive,
        'cheque_pay': cheque_pay,
        'cheque_receive_summary': cheque_receive_summary,
        'cheque_pay_summary': cheque_pay_summary,
    }

    print(f"زمان اجرا: {time.time() - start_time:.2f} ثانیه")
    return render(request, 'master_moshrari_detail.html', context)



from django.utils import timezone
from django.db.models import Value, CharField, IntegerField, F, ExpressionWrapper, DurationField
from django.db.models import Value, CharField, IntegerField, F, ExpressionWrapper, DecimalField, Sum, Count
from django.db.models import OuterRef, Subquery


@login_required(login_url='/login')
def LoanTotal1(request, status, *args, **kwargs):
    name = 'اقساط معوق'
    result = page_permision(request, name)  # بررسی دسترسی
    if result:  # اگر هدایت انجام شده است
        return result
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page=' اقساط معوق', code=0)

    start_time = time.time()  # زمان شروع تابع
    start_time2 = time.time()

    today = timezone.now().date()
    total_count = 0
    total_cost = 0
    total_mtday = 0

    print(f"stage 1 : {time.time() - start_time2:.2f} ثانیه")
    start_time2 = time.time()

    if status == 'overdue':
        title = 'گزارش اقساط معوق'
        loans = LoanDetil.objects.filter(complete_percent__lt=1, date__lt=today)
        person = Person.objects.filter(pk__in=loans.values('loan__person__pk')).distinct()
        total_count=person.count()
        total_cost=0
        total_mtday=0
        print(f"stage 2 : {time.time() - start_time2:.2f} ثانیه")
        start_time2 = time.time()
        min_mandeh=0
        max_mandeh=0
        min_cost=0
        max_cost=0
        min_from_last_daryaft=0
        max_from_last_daryaft=0
        for p in person:
            l_p = loans.filter(loan__person=p)
            try:
                p.f_date = l_p.first().tarikh
            except:
                p.f_date = "-"
            count = 0
            cost = 0
            from_last_daryaft=0
            mtday=0
            for l in l_p:
                count += (1 - l.complete_percent)
                if l.date < today:
                    cost += (1 - l.complete_percent) * float(l.cost)
                    mtday=((1 - l.complete_percent) * float(l.cost))*int((today-l.date).days)
            try:
                from_last_daryaft = BedehiMoshtari.objects.filter(person=p).last().from_last_daryaft
            except:
                pass
            last_tracks=Tracking.objects.filter(customer__person=p).last()
            try:
                p.mandeh=BedehiMoshtari.objects.filter(person=p).last().total_mandeh
            except:
                p.mandeh=0
            p.last_tracks=last_tracks
            p.loan_count = count
            p.cost = cost
            p.mtday = mtday/10000000
            p.from_last_daryaft = from_last_daryaft
            p.save()
            total_cost+=cost
            total_mtday+= mtday*1/10000000


            if p.mandeh > max_mandeh:
                max_mandeh = p.mandeh

            if p.mandeh < min_mandeh:
                min_mandeh = p.mandeh

            if cost > max_cost:
                max_cost = cost

            if cost < min_cost:
                min_cost = cost

            if from_last_daryaft > max_from_last_daryaft:
                max_from_last_daryaft = from_last_daryaft

            if from_last_daryaft < min_from_last_daryaft:
                min_from_last_daryaft = from_last_daryaft


    if status == 'soon':
        title = 'گزارش اقساط دارای تعجیل'
        loans = LoanDetil.objects.filter(complete_percent__gt=0, date__gte=today)
        person = Person.objects.filter(pk__in=loans.values('loan__person__pk')).distinct()
        total_cost=0
        total_mtday=0
        min_mandeh=0
        max_mandeh=0
        min_cost=0
        max_cost=0
        min_from_last_daryaft=0
        max_from_last_daryaft=0
        for p in person:
            l_p = loans.filter(loan__person=p)
            try:
                p.f_date = l_p.first().tarikh
            except:
                p.f_date = "-"
            count = 0
            cost = 0
            from_last_daryaft = 0
            mtday = 0
            for l in l_p:

                if l.date > today:
                    count += (l.complete_percent)
                    cost += (l.complete_percent) * float(l.cost)
                    mtday = ((l.complete_percent) * float(l.cost)) * int((today - l.date).days)
            try:
                from_last_daryaft = BedehiMoshtari.objects.filter(person=p).last().from_last_daryaft
            except:
                pass
            last_tracks = Tracking.objects.filter(customer__person=p).last()
            try:
                p.mandeh=BedehiMoshtari.objects.filter(person=p).last().total_mandeh
            except:
                p.mandeh=0
            p.last_tracks = last_tracks
            p.loan_count = count
            p.cost = cost
            p.mtday = -1 * mtday / 10000000
            p.from_last_daryaft = from_last_daryaft
            p.save()
            total_cost += cost
            total_mtday += mtday * 1 / 10000000

            if p.mandeh > max_mandeh:
                max_mandeh = p.mandeh

            if p.mandeh < min_mandeh:
                min_mandeh = p.mandeh

            if cost > max_cost:
                max_cost = cost

            if cost < min_cost:
                min_cost = cost

            if from_last_daryaft > max_from_last_daryaft:
                max_from_last_daryaft = from_last_daryaft

            if from_last_daryaft < min_from_last_daryaft:
                min_from_last_daryaft = from_last_daryaft

    print(f"stage 3 : {time.time() - start_time2:.2f} ثانیه")
    start_time2 = time.time()


    print('loan_stats["total_cost"]')

    # loan_stats = person.aggregate(
    #     total_count=Count("id"),
    #     total_cost=Sum("cost") / 10000000000,
    #     total_mtday=Sum("mtday") / 1000
    # )
    # print(loan_stats["total_cost"])
    # day_report = MasterReport.objects.filter(day=today).last()

    # if day_report and (
    #         day_report.total_delaycost != loan_stats["total_delaycost"] or day_report.total_mtday != loan_stats[
    #     "total_mtday"]):
    #     day_report.total_delaycost = loan_stats["total_delaycost"]
    #     day_report.total_mtday = loan_stats["total_mtday"]
    #     day_report.save()

    from django.db.models import Q

    # فیلتر کردن مواردی که نیاز به بررسی دارند
    tracking = Tracking.objects.filter(
        Q(message_id__isnull=False) &
        ~Q(status_code__in=[2, 3, 4])
    )
    print(f"stage 4 : {time.time() - start_time2:.2f} ثانیه")
    start_time2 = time.time()
    updated_objects = []

    for t in tracking:
        try:
            status_code = check_sms_status(t.message_id)
            if status_code is not None:  # فقط اگر مقدار معتبر باشد، ذخیره شود
                t.status_code = status_code
                updated_objects.append(t)  # جمع‌آوری موارد برای به‌روزرسانی دسته‌ای
        except Exception as e:
            print(f"خطا در پردازش {t.id}: {e}")  # مدیریت خطا برای اشکال‌زدایی

    print(f"stage 5 : {time.time() - start_time2:.2f} ثانیه")
    start_time2 = time.time()
    # به‌روزرسانی دسته‌ای برای بهبود عملکرد
    if updated_objects:
        Tracking.objects.bulk_update(updated_objects, ["status_code"])




    context = {
        'title': title,
        'user': user,
        'today': today,  # <--- این خط را اضافه کنید!

        'person': person,
        "total_count": total_count,
        "total_cost": total_cost/ 10000000000,
        "total_mtday": total_mtday/ 1000,
        'status': status,

        'min_mandeh': min_mandeh,
        'max_mandeh': max_mandeh,
        'min_cost': min_cost,
        'max_cost': max_cost,
        'min_from_last_daryaft': min_from_last_daryaft,
        'max_from_last_daryaft': max_from_last_daryaft,



    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'loan-total.html', context)


@login_required(login_url='/login')
def LoanTotal(request, status, *args, **kwargs):
    from django.utils import timezone
    import time

    # بررسی مجوز دسترسی
    name = 'اقساط معوق'
    result = page_permision(request, name)
    if result:
        return result

    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page=' اقساط معوق', code=0)

    start_time = time.time()
    today = timezone.now().date()

    # تعیین شرایط فیلتر بر اساس وضعیت
    if status == 'overdue':
        title = 'گزارش اقساط معوق'
        loans_qs = LoanDetil.objects.filter(complete_percent__lt=1, date__lt=today)
    elif status == 'soon':
        title = 'گزارش اقساط دارای تعجیل'
        loans_qs = LoanDetil.objects.filter(complete_percent__gt=0, date__gte=today)
    else:
        loans_qs = LoanDetil.objects.none()

    # گرفتن لیست افراد بدون تکرار
    persons = Person.objects.filter(pk__in=loans_qs.values('loan__person__pk')).distinct()

    total_cost = 0
    total_mtday = 0

    # گرفتن لیست افراد بدون تکرار
    persons = Person.objects.filter(pk__in=loans_qs.values('loan__person__pk')).distinct()

    total_cost = 0
    total_mtday = 0
    min_mandeh = float('inf')
    max_mandeh = float('-inf')
    min_cost = float('inf')
    max_cost = float('-inf')
    min_from_last_daryaft = float('inf')
    max_from_last_daryaft = float('-inf')

    # حلقه روی هر شخص برای محاسبات و بروزرسانی
    for p in persons:
        l_p = loans_qs.filter(loan__person=p)

        # تعیین تاریخ اولیه
        p.f_date = l_p.first().tarikh if l_p.exists() else "-"

        count = 0
        cost = 0
        from_last_daryaft = 0
        mtday = 0

        # گرفتن بدهی مشتری
        try:
            total_mandeh = BedehiMoshtari.objects.filter(person=p).last().total_mandeh
        except:
            total_mandeh = 0

        last_tracks = Tracking.objects.filter(customer__person=p).last()

        for l in l_p:
            if (status == 'overdue' and l.date < today) or (status == 'soon' and l.date > today):
                if status == 'overdue':
                    count += (1 - l.complete_percent)
                    cost += (1 - l.complete_percent) * float(l.cost)
                    mtday += ((1 - l.complete_percent) * float(l.cost)) * int((today - l.date).days)
                else:
                    count += l.complete_percent
                    cost += l.complete_percent * float(l.cost)
                    mtday += (l.complete_percent * float(l.cost)) * int((today - l.date).days)

        # گرفتن مقدار from_last_daryaft
        try:
            from_last_daryaft = BedehiMoshtari.objects.filter(person=p).last().from_last_daryaft
            if from_last_daryaft is None:
                from_last_daryaft = 0
        except:
            from_last_daryaft = 0

        acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
        master_info = MasterInfo.objects.filter(is_active=True).last()
        monthly_rate = master_info.monthly_rate if master_info and master_info.monthly_rate else Decimal('0')
        mtday=Decimal(mtday) / Decimal(30) * monthly_rate / Decimal(100) if mtday else Decimal('0')

            # بروزرسانی خصیصه‌های شخص
        p.mandeh = total_mandeh
        p.last_tracks = last_tracks
        p.loan_count = count
        p.cost = cost
        p.mtday = -mtday if status == 'soon' else mtday
        p.from_last_daryaft = from_last_daryaft
        p.save()

        # جمع‌بندی مقادیر کل
        total_cost += cost
        total_mtday += mtday

        # بروزرسانی کمینه و بیشینه‌ها
        min_mandeh = min(min_mandeh, p.mandeh)
        max_mandeh = max(max_mandeh, p.mandeh)
        min_cost = min(min_cost, cost)
        max_cost = max(max_cost, cost)
        min_from_last_daryaft = min(min_from_last_daryaft, from_last_daryaft)
        max_from_last_daryaft = max(max_from_last_daryaft, from_last_daryaft)

    # بروزرسانی وضعیت پیامک‌ها
    tracking_qs = Tracking.objects.filter(
        message_id__isnull=False
    ).exclude(status_code__in=[2, 3, 4])

    updated_objects = []
    for t in tracking_qs:
        try:
            status_code = check_sms_status(t.message_id)
            if status_code is not None:
                t.status_code = status_code
                updated_objects.append(t)
        except Exception as e:
            print(f"خطا در پردازش {t.id}: {e}")

    if updated_objects:
        Tracking.objects.bulk_update(updated_objects, ['status_code'])

    # total_mtday = Decimal(total_mtday) / Decimal(30) * monthly_rate / Decimal(100) if total_mtday else Decimal('0')

    # ساختن کانتکست نهایی برای قالب
    context = {
        'title': title,
        'user': user,
        'today': today,
        'person': persons,
        "total_count": persons.count(),
        "total_cost": abs(total_cost)/10,
        "total_mtday": (-abs(total_mtday) if status != 'soon' else abs(total_mtday))/10,
        'status': status,
        'min_mandeh': min_mandeh,
        'max_mandeh': max_mandeh,
        'min_cost': min_cost,
        'max_cost': max_cost,
        'min_from_last_daryaft': min_from_last_daryaft,
        'max_from_last_daryaft': max_from_last_daryaft,
    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")
    return render(request, 'loan-total.html', context)







from django.db.models import Sum, F, Q, Case, When, Value, IntegerField, FloatField, ExpressionWrapper, Min, Max
from django.utils import timezone
from datetime import timedelta
import time









def loan_summary_api(request):
    today = timezone.now().date()

    loans = LoanDetil.objects.filter(complete_percent__lt=1, date__lt=today).annotate(
        delay_days=(ExpressionWrapper(F("date") - today, output_field=IntegerField())) / -86400000000,
        mtday=(ExpressionWrapper((F("delay_days") * F("cost") * (1 - F("complete_percent"))),
                                 output_field=IntegerField())) / 10000000,
        delaycost=(ExpressionWrapper((F("cost") * (1 - F("complete_percent"))), output_field=IntegerField()))
    )

    loan_stats = loans.aggregate(
        total_delaycost=Sum("delaycost") / 10000000000,
        total_mtday=Sum("mtday") / 1000
    )

    return JsonResponse({
        "total_delaycost": loan_stats["total_delaycost"],
        "total_mtday": loan_stats["total_mtday"],
    })


from django.db.models import Q


@login_required(login_url='/login')
def SaleTotal(request, year=None, month=None, day=None):
    name = 'گزارش فروش'
    result = page_permision(request, name)
    if result:
        return result
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page=' گزارش فروش', code=0)

    start_time = time.time()

    if year and month and day:
        try:
            day_filter_gregorian = datetime.date(int(year), int(month), int(day))
        except (ValueError, TypeError):
            day_filter_gregorian = timezone.now().date()
    else:
        day_filter_gregorian = timezone.now().date()
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year

    kind1 = ['خريدار در برگشت از فروش', 'خريدار در فاکتور فروش','تخفيف فاکتور فروش']
    q_objects = Q()
    for item in kind1:
        q_objects |= Q(sharh__startswith=item)

    asnadp = SanadDetail.objects.filter(
        q_objects,
        kol=103,
        date=day_filter_gregorian
    ).select_related('person')

    for s in asnadp:
        try:
            # اطمینان از اینکه curramount قبل از ضرب عددی است
            s.negative_curramount = float(s.curramount) * -1
        except (ValueError, TypeError):
            # اگر s.curramount قابل تبدیل به عدد نبود، 0 در نظر بگیرید یا مقدار دیگری
            s.negative_curramount = 0  # یا s.curramount اگر می‌خواهید همان مقدار اصلی باشد

    # --- اضافه کردن روز هفته برای رندر اولیه ---
    jalali_weekday_names = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
    current_day_jalali = jdate.fromgregorian(date=day_filter_gregorian)
    day_of_week_jalali = jalali_weekday_names[current_day_jalali.weekday()]  # weekday() بر اساس شنبه (0) شروع می‌شود

    # -------------------------------------------------------------------------------------------------

    jalali_month_names = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن",
                          "اسفند"]

    all_report_years = MonthlyReport.objects.values_list('year', flat=True).distinct().order_by('year')

    yearly_monthly_khales_forosh_data = {year: [0] * 12 for year in all_report_years}

    all_monthly_reports = MonthlyReport.objects.filter(year__in=all_report_years).order_by('year', 'month')

    for report in all_monthly_reports:
        try:
            year_val = report.year
            month_index = report.month - 1  # ماه شمسی 1 تا 12، ایندکس 0 تا 11

            if 0 <= month_index < 12:
                yearly_monthly_khales_forosh_data[year_val][month_index] = float(report.khales_forosh / 1000)
        except (ValueError, TypeError, KeyError):
            print(f"Error processing monthly report: Year {report.year}, Month {report.month}")
            pass

    chart_datasets_khales_forosh_by_year = []

    colors_for_yearly_chart = [
        'rgba(30, 144, 255, 0.7)',  # Dodger Blue
        'rgba(255, 69, 0, 0.7)',  # Orange Red
        'rgba(50, 205, 50, 0.7)',  # Lime Green
        'rgba(147, 112, 219, 0.7)',  # MediumPurple
        'rgba(255, 165, 0, 0.7)',  # Orange
        'rgba(0, 191, 255, 0.7)',  # Deep Sky Blue
        'rgba(255, 0, 128, 0.7)',  # Pink
        'rgba(128, 128, 0, 0.7)',  # Olive
        'rgba(0, 200, 200, 0.7)',  # Teal
        'rgba(200, 0, 200, 0.7)',  # Fuchsia
    ]
    border_colors_for_yearly_chart = [c.replace('0.7', '1') for c in colors_for_yearly_chart]

    color_index = 0
    for year_val in sorted(yearly_monthly_khales_forosh_data.keys()):
        chart_datasets_khales_forosh_by_year.append({
            'label': f'خالص فروش  {year_val}',
            'data': yearly_monthly_khales_forosh_data[year_val],
            'backgroundColor': colors_for_yearly_chart[color_index % len(colors_for_yearly_chart)],
            'borderColor': border_colors_for_yearly_chart[color_index % len(border_colors_for_yearly_chart)],
            'borderWidth': 1,
            'barPercentage': 0.8,
            'categoryPercentage': 0.8,
            # 'stack': 'khales_forosh_stack' # اگر نمودار میله ای انباشته (Stacked) می خواهید، این خط را فعال کنید
        })
        color_index += 1
        # -------------------------------------------------------
        jalali_weekday_names = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]

        # بهینه‌سازی: فقط فیلدهای لازم را از دیتابیس دریافت کنید
        all_master_reports_data = MasterReport.objects.values('day', 'khales_forosh')

        # لیست برای نگهداری مجموع خالص فروش برای هر روز هفته
        weekly_khales_forosh_sum_temp = [0.0] * 7
        # لیست برای نگهداری تعداد رکوردهای هر روز هفته
        weekly_day_counts = [0] * 7

        for report_data in all_master_reports_data:
            try:
                gregorian_date = report_data['day']
                khales_forosh_value = float(report_data['khales_forosh'])

                jdate_obj = jdate.fromgregorian(date=gregorian_date)
                weekday_index = jdate_obj.weekday()  # 0=شنبه, 1=یکشنبه, ..., 6=جمعه

                weekly_khales_forosh_sum_temp[weekday_index] += khales_forosh_value
                weekly_day_counts[weekday_index] += 1

            except (ValueError, TypeError, KeyError):
                print(f"Error processing MasterReport for date {report_data.get('day')}")
                pass

        # محاسبه میانگین خالص فروش برای هر روز هفته
        weekly_khales_forosh_average = [0.0] * 7
        valid_weekly_averages_sum = 0.0  # مجموع میانگین‌های غیر صفر
        valid_weekly_averages_count = 0  # تعداد میانگین‌های غیر صفر

        for i in range(7):
            if weekly_day_counts[i] > 0:
                weekly_khales_forosh_average[i] = weekly_khales_forosh_sum_temp[i] / weekly_day_counts[i]
                valid_weekly_averages_sum += weekly_khales_forosh_average[i]
                valid_weekly_averages_count += 1
            else:
                weekly_khales_forosh_average[i] = 0.0

        # محاسبه میانگین کل از میانگین‌های روزهای هفته
        # این همان "متوسط فروش روزهای هفته" است
        average_of_weekly_averages = valid_weekly_averages_sum / valid_weekly_averages_count if valid_weekly_averages_count > 0 else 0

        chart_datasets_weekly_khales_forosh = [
            {
                'label': 'میانگین فروش روزانه',
                'data': weekly_khales_forosh_average,
                'backgroundColor': 'rgba(102, 51, 153, 0.7)',
                'borderColor': 'rgba(102, 51, 153, 1)',
                'borderWidth': 1,
                'barPercentage': 0.7,
                'categoryPercentage': 0.7,
            },
            {
                'type': 'line',
                'label': 'میانگین (متوسط روزانه)',  # لیبل برای خط افقی
                'data': [average_of_weekly_averages] * 7,  # خط افقی در ارتفاع میانگین کل
                'borderColor': 'rgba(255, 193, 7, 1)',
                'backgroundColor': 'transparent',
                'borderWidth': 2,
                'pointRadius': 0,
                'tension': 0,
            }
        ]

    title = 'گزارش فروش'
    context = {
        'title': title,
        'user': user,
        'day': day_filter_gregorian,
        'asnadp': asnadp,
        'day_of_week': day_of_week_jalali,  # اضافه کردن روز هفته به context
        'chart_labels_khales_forosh_by_year': jalali_month_names,
        'chart_datasets_khales_forosh_by_year': chart_datasets_khales_forosh_by_year,

        'chart_labels_weekly_khales_forosh': jalali_weekday_names,  # لیبل‌های روزهای هفته
        'chart_datasets_weekly_khales_forosh': chart_datasets_weekly_khales_forosh,  # Dataset‌ها (میله‌ای و خط میانگین)
    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'sale_total.html', context)


from django.http import JsonResponse  # اگر قبلاً ایمپورت نکرده‌اید، حتماً اضافه کنید


from datetime import datetime

def SaleTotalData(request, date_str):
    try:
        day_filter_gregorian = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    kind1 = ['خريدار در برگشت از فروش', 'خريدار در فاکتور فروش', 'تخفيف فاکتور فروش']
    q_objects = Q()
    for item in kind1:
        q_objects |= Q(sharh__startswith=item)

    asnadp = SanadDetail.objects.filter(
        q_objects,
        kol=103,
        date=day_filter_gregorian
    ).select_related('person')

    data = []
    total_mandah = 0
    for s in asnadp:
        sharh_display = s.syscomment if s.syscomment else s.sharh
        jalali_tarikh_str = s.tarikh
        try:
            jalali_year = s.tarikh.split('/')[0]
            jalali_month = s.tarikh.split('/')[1]
        except IndexError:
            jalali_year = ''
            jalali_month = ''
        try:
            current_amount_numeric = float(s.curramount)
            negative_curramount = current_amount_numeric * -1
        except (ValueError, TypeError):
            negative_curramount = 0

        data.append({
            'person_name': f"{s.person.name} {s.person.lname}",
            'person_id': s.person.per_taf,
            'sanad_code': s.sanad_code,
            'radif': s.radif,
            'tarikh': jalali_tarikh_str,
            'year': jalali_year,
            'month': jalali_month,
            'sharh': sharh_display,
            'mablagh': negative_curramount,
            'is_negative': negative_curramount < 0
        })
        total_mandah += negative_curramount

    display_date_jalali = jdate.fromgregorian(date=day_filter_gregorian)
    display_date_str = display_date_jalali.strftime('%Y/%m/%d')
    jalali_weekday_names = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
    day_of_week_jalali = jalali_weekday_names[display_date_jalali.weekday()]

    return JsonResponse({
        'data': data,
        'total_mandah': total_mandah,
        'display_date': display_date_str,
        'day_of_week': day_of_week_jalali,
    })
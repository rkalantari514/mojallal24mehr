# جدید
# جدیدتر
import re
from django.contrib.auth.decorators import login_required
import time
from datetime import date
from django.utils import timezone
from django.db.models import Sum, F, FloatField
from django.db.models.functions import Cast
from openpyxl.styles.builtins import total
from persianutils import standardize
from django.db.models import Sum, F, DecimalField

from accounting.models import BedehiMoshtari
from custom_login.models import UserLog
from dashboard.models import MasterInfo, MasterReport
from dashboard.views import generate_calendar_data_cheque
from loantracker.forms import SMSTrackingForm
from loantracker.models import TrackKinde, Tracking
from mahakupdate.models import SanadDetail, AccCoding, ChequesRecieve, ChequesPay, Person, Loan, LoanDetil
from jdatetime import date as jdate
from datetime import timedelta, date
from khayyam import JalaliDate, JalaliDatetime
from django.db.models import F

from mahakupdate.sendtogap import send_to_admin1


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
    from django.db.models import Sum  # این خط را به ابتدای تابع منتقل کنید
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='چک های دریافتی', code=0)

    start_time = time.time()  # زمان شروع تابع
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':

        # تکمیل تقویم

        month = request.GET.get('month', None)
        year = request.GET.get('year', None)
        print("Query params - Year:", year, "Month:", month)

        if month is not None and year is not None:
            current_month = int(month)
            current_year = int(year)
        else:
            today_jalali = JalaliDate.today()
            current_year = today_jalali.year
            current_month = today_jalali.month

        months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
        month_name = months[current_month - 1]
        print("Current Year:", current_year, "Current Month:", current_month)

        cheque_recive_data = ChequesRecieve.objects.exclude(total_mandeh=0)
        cheque_pay_data = ChequesPay.objects.exclude(total_mandeh=0)

        loan_detail_data = LoanDetil.objects.filter(complete_percent__lt=1)

        days_in_month, max_cheque, month_cheque_data, month_loan_data = generate_calendar_data_cheque(current_month,
                                                                                                      current_year,
                                                                                                      cheque_recive_data,
                                                                                                      cheque_pay_data,
                                                                                                      loan_detail_data)

        context = {
            # for calendar
            'month_name': month_name,
            'year': current_year,
            'month': current_month,
            'days_in_month': days_in_month,
            'max_cheque': max_cheque,
            'month_cheque_data': month_cheque_data,
            'month_loan_data': month_loan_data,

        }

        print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

        return render(request, 'partial_calendar_cheque_recive.html', context)

    # گام اول: استخراج تاریخ و ماه
    today = date.today()
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

    # تکمیل تقویم

    month = request.GET.get('month', None)
    year = request.GET.get('year', None)
    print("Query params - Year:", year, "Month:", month)

    if month is not None and year is not None:
        current_month = int(month)
        current_year = int(year)
    else:
        today_jalali = JalaliDate.today()
        current_year = today_jalali.year
        current_month = today_jalali.month

    months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    month_name = months[current_month - 1]
    print("Current Year:", current_year, "Current Month:", current_month)

    cheque_recive_data = ChequesRecieve.objects.exclude(total_mandeh=0)
    cheque_pay_data = ChequesPay.objects.exclude(total_mandeh=0)

    loan_detail_data = LoanDetil.objects.filter(complete_percent__lt=1)

    days_in_month, max_cheque, month_cheque_data, month_loan_data = generate_calendar_data_cheque(current_month,
                                                                                                  current_year,
                                                                                                  cheque_recive_data,
                                                                                                  cheque_pay_data,
                                                                                                  loan_detail_data)

    print(f"8: {time.time() - start_time:.2f} ثانیه")

    # آماده‌سازی context برای رندر
    context = {
        'title': 'چکهای دریافتی',
        'user': user,
        'total_data': total_data,
        'chartmahanedata': chart_data,
        'table1': table1,

        # for calendar
        'month_name': month_name,
        'year': current_year,
        'month': current_month,
        'days_in_month': days_in_month,
        'max_cheque': max_cheque,
        'month_cheque_data': month_cheque_data,
        'month_loan_data': month_loan_data,
    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'cheques-recieve-total.html', context)


@login_required(login_url='/login')
def ChequesPayTotal(request, *args, **kwargs):
    from django.db.models import Sum  # این خط را به ابتدای تابع منتقل کنید
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='چک های پرداختی', code=0)

    start_time = time.time()  # زمان شروع تابع
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':

        # تکمیل تقویم

        month = request.GET.get('month', None)
        year = request.GET.get('year', None)
        print("Query params - Year:", year, "Month:", month)

        if month is not None and year is not None:
            current_month = int(month)
            current_year = int(year)
        else:
            today_jalali = JalaliDate.today()
            current_year = today_jalali.year
            current_month = today_jalali.month

        months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
        month_name = months[current_month - 1]
        print("Current Year:", current_year, "Current Month:", current_month)

        cheque_recive_data = ChequesRecieve.objects.exclude(total_mandeh=0)
        cheque_pay_data = ChequesPay.objects.exclude(total_mandeh=0)

        loan_detail_data = LoanDetil.objects.filter(complete_percent__lt=1)

        days_in_month, max_cheque, month_cheque_data, month_loan_data = generate_calendar_data_cheque(current_month,
                                                                                                      current_year,
                                                                                                      cheque_recive_data,
                                                                                                      cheque_pay_data,
                                                                                                      loan_detail_data)

        context = {
            # for calendar
            'month_name': month_name,
            'year': current_year,
            'month': current_month,
            'days_in_month': days_in_month,
            'max_cheque': max_cheque,
            'month_cheque_data': month_cheque_data,
            'month_loan_data': month_loan_data,

        }

        print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

        return render(request, 'partial_calendar_cheque_pay.html', context)

    # گام اول: استخراج تاریخ و ماه
    today = date.today()
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
    print(f"6: {time.time() - start_time:.2f} ثانیه")

    # مرحله اول: دریافت کدهای منحصر به فرد per_code
    # per_codes = chequespay.values_list('per_code', flat=True).distinct()
    # print("Unique per_codes from ChequesRecieve:", per_codes)

    # بارگذاری اطلاعات شخص بر اساس per_code
    # persons = Person.objects.filter(code__in=per_codes)

    # بارگذاری دیکشنری با کلیدهای به عنوان رشته
    # persons_map = {str(person.code): f"{person.name} {person.lname}" for person in persons}
    # print("Loaded Persons Map:", persons_map)

    # آماده‌سازی داده‌ها برای جدول
    table1 = []
    for chequ in chequespay:
        com = chequ.last_sanad_detaile.syscomment if chequ.last_sanad_detaile else ''

        # دسترسی به نام و نام خانوادگی شخص از دیکشنری
        # person = persons_map.get(str(chequ.per_code), '')  # ساختار به صورت رشته

        # Split تاریخ به سال، ماه و روز
        year, month, day = chequ.cheque_tarik.split('/')

        # اضافه کردن داده‌ها به جدول
        table1.append({
            'id': chequ.cheque_id,
            'status': chequ.status,
            'com': extract_first_words(com),
            'mandeh': chequ.total_mandeh,
            'date': chequ.cheque_date,
            'bank_logo': chequ.bank.bank_logo,
            'bank_name': chequ.bank.bank_name,
            'bank_branch': chequ.bank.name,
            # 'person': fix_persian_characters(person),  # Person نام و نام خانوادگی
            'year': year,
            'month': month,
        })

    print(f"7: {time.time() - start_time:.2f} ثانیه")

    # تکمیل تقویم

    month = request.GET.get('month', None)
    year = request.GET.get('year', None)
    print("Query params - Year:", year, "Month:", month)

    if month is not None and year is not None:
        current_month = int(month)
        current_year = int(year)
    else:
        today_jalali = JalaliDate.today()
        current_year = today_jalali.year
        current_month = today_jalali.month

    months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    month_name = months[current_month - 1]
    print("Current Year:", current_year, "Current Month:", current_month)

    cheque_recive_data = ChequesRecieve.objects.exclude(total_mandeh=0)
    cheque_pay_data = ChequesPay.objects.exclude(total_mandeh=0)

    loan_detail_data = LoanDetil.objects.filter(complete_percent__lt=1)

    days_in_month, max_cheque, month_cheque_data, month_loan_data = generate_calendar_data_cheque(current_month,
                                                                                                  current_year,
                                                                                                  cheque_recive_data,
                                                                                                  cheque_pay_data,
                                                                                                  loan_detail_data)

    print(f"8: {time.time() - start_time:.2f} ثانیه")

    # آماده‌سازی context برای رندر
    context = {
        'title': 'چکهای پرداختنی',
        'user': user,
        'total_data': total_data,
        'chartmahanedata': chart_data,
        'table1': table1,

        # for calendar
        'month_name': month_name,
        'year': current_year,
        'month': current_month,
        'days_in_month': days_in_month,
        'max_cheque': max_cheque,
        'month_cheque_data': month_cheque_data,
        'month_loan_data': month_loan_data,
    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'cheques-pay-total.html', context)


@ login_required(login_url='/login')
def balance_sheet_kol(request):
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
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


def balance_sheet_moin(request, kol_code):
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
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


def balance_sheet_tafsili(request, kol_code, moin_code):
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
    tafsili_codes = SanadDetail.objects.filter(kol=kol_code, moin=moin_code).values('tafzili').distinct()
    balance_data = []
    total_bed = 0
    total_bes = 0
    total_curramount = 0
    for tafsili in tafsili_codes:
        tafsili_code = tafsili['tafzili']

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
    sanads = SanadDetail.objects.filter(kol=kol_code, moin=moin_code, acc_year=acc_year)

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
        'moin_code': moin_code,
        'kol_code': kol_code,
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
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
    sanads = SanadDetail.objects.filter(kol=kol_code, moin=moin_code, tafzili=tafzili_code, acc_year=acc_year)

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
    sanads2 = SanadDetail.objects.filter(kol=kol_code, moin=moin_code, acc_year=acc_year)

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
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='حساب مشتریان', code=0)

    start_time = time.time()  # زمان شروع تابع

    filters = [
        {'filter': {'total_mandeh__gt': 0}, 'negate': False},
        {'filter': {'total_mandeh__gt': 0, 'loans_total__gt': 0}, 'negate': False},
        {'filter': {'total_mandeh__gt': 0, 'loans_total': 0}, 'negate': False},
        {'filter': {'total_mandeh__lt': 0}, 'negate': True},
        {'filter': {'total_mandeh__lt': 0, 'loans_total__gt': 0}, 'negate': True},
        {'filter': {'total_mandeh__lt': 0, 'loans_total': 0}, 'negate': True},
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
    today = date.today()

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
        '1': {'total_mandeh__gt': 0},
        '2': {'total_mandeh__gt': 0, 'loans_total__gt': 0},
        '3': {'total_mandeh__gt': 0, 'loans_total': 0},
        '4': {'total_mandeh__lt': 0},
        '5': {'total_mandeh__lt': 0, 'loans_total__gt': 0},
        '6': {'total_mandeh__lt': 0, 'loans_total': 0},
        '7': {'total_mandeh__lt': 0, 'loans_total__gt': 0, 'total_with_loans__lt': 0},
        '8': {'total_mandeh': 0, 'loans_total__gt': 0},
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


import datetime
from django.utils import timezone
import datetime
from collections import defaultdict
from django.utils import timezone
from django.utils import timezone
from collections import defaultdict
import datetime


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

from datetime import timedelta

from datetime import timedelta
import re

from datetime import timedelta

from django.shortcuts import render, redirect


@login_required(login_url='/login')
def HesabMoshtariDetail(request, tafsili):
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='حساب مشتری', code=0)

    today = timezone.now().date()
    asnad = SanadDetail.objects.filter(kol=103, moin=1, tafzili=tafsili).order_by('date')

    hesabmoshtari = BedehiMoshtari.objects.filter(tafzili=tafsili).last()
    m_name = None

    if hesabmoshtari:
        full_name = f'{hesabmoshtari.person.name} {hesabmoshtari.person.lname}'
        cleaned_name = re.split(r"[a-zA-Z-$]|قسط", full_name, maxsplit=1)[0].strip()
        m_name = cleaned_name

    if request.method == 'POST':
        action = request.POST.get('action')  # دریافت نام دکمه کلیک شده

        if action == 'send_sms':  # عملیات ارسال پیامک
            form = SMSTrackingForm(request.POST, customer=hesabmoshtari)
            if form.is_valid():
                phone_number = form.cleaned_data.get('phone_number')  # دریافت شماره تلفن از فرم
                sample_sms = form.cleaned_data.get('sample_sms')  # دریافت پیامک نمونه از فرم
                message = form.cleaned_data.get('message')  # دریافت متن پیامک واردشده توسط کاربر

                if not sample_sms and not message:
                    form.add_error('message', "حداقل یکی از فیلدهای متن پیامک یا پیامک نمونه باید مقدار داشته باشد.")
                else:
                    # ترکیب پیامک
                    message_to_send = ""
                    if sample_sms:
                        message_to_send += sample_sms.text
                    if message:
                        message_to_send += f"\n{message}"

                    test_message = f"{phone_number}: {message_to_send}"

                    # ارسال پیامک
                    response = send_to_admin1(test_message)

                    if response and response.status_code == 200:
                        # پیدا کردن نوع پیگیری "پیامک"
                        try:
                            track_kind = TrackKinde.objects.get(kind_name="پیامک")
                        except TrackKinde.DoesNotExist:
                            track_kind = None
                            form.add_error(None, "نوع پیگیری 'پیامک' در سیستم وجود ندارد.")

                        if track_kind:
                            tracking = form.save(commit=False)
                            tracking.customer = hesabmoshtari
                            tracking.message_to_send = message_to_send
                            tracking.created_by = user if user.is_authenticated else None
                            tracking.track_kind = track_kind  # مقدار نوع پیگیری
                            tracking.save()

                        return redirect(f'/acc/jariashkhas/moshtari/{tafsili}')  # هدایت به صفحه مناسب

                    else:
                        form.add_error('phone_number', "ارسال پیامک موفقیت‌آمیز نبود. لطفاً دوباره تلاش کنید.")

        elif action == 'other_action':  # عملیات دیگر
            pass
    else:
        form = SMSTrackingForm(customer=hesabmoshtari)  # نمایش فرم خالی

    tracking=Tracking.objects.filter(customer=hesabmoshtari).order_by('-id')

    context = {
        'title': 'حساب مشتری',
        'hesabmoshtari': hesabmoshtari,
        'user': user,
        'today': today,
        'asnad': asnad,
        'm_name': m_name,
        'form': form,  # ارسال فرم به قالب
        'tracking': tracking,  # ارسال فرم به قالب
    }

    return render(request, 'moshrari_detail.html', context)

from django.utils import timezone
from django.db.models import Value, CharField, IntegerField, F, ExpressionWrapper, DurationField
from django.db.models import Value, CharField, IntegerField, F, ExpressionWrapper, DecimalField, Sum, Count
from django.db.models import OuterRef, Subquery


@login_required(login_url='/login')
def LoanTotal(request, *args, **kwargs):
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page=' اقساط معوق', code=0)

    start_time = time.time()  # زمان شروع تابع

    today = timezone.now().date()





    loans = LoanDetil.objects.filter(complete_percent__lt=1, date__lt=today).annotate(
        category_en=Value("Overdue", CharField()),
        category_fa=Value("معوق", CharField()),
        delay_days=(ExpressionWrapper(F("date") - today, output_field=IntegerField())) / -86400000000,
        mtday=(ExpressionWrapper(
            (F("delay_days") * F("cost") * (1 - F("complete_percent"))),
            output_field=DecimalField(max_digits=15, decimal_places=0)) / 10000000
               ),
        delaycost=(ExpressionWrapper(
            (F("cost") * (1 - F("complete_percent"))),
            output_field=DecimalField(max_digits=15, decimal_places=0))
        ),
        from_last_daryaft=Subquery(
            BedehiMoshtari.objects.filter(person=OuterRef("loan__person")).values('from_last_daryaft')[:1]
        )
    )

    # loans = LoanDetil.objects.filter(complete_percent__lt=1, date__lt=today).annotate(
    #     category_en=Value("Overdue", CharField()),
    #     category_fa=Value("معوق", CharField()),
    #     # delay_days=ExpressionWrapper(today - F("date"), output_field=DurationField()),
    #     delay_days=(ExpressionWrapper(F("date") - today, output_field=IntegerField())) / -86400000000,
    #     mtday=(ExpressionWrapper(
    #         (F("delay_days") * F("cost") * (1 - F("complete_percent"))),
    #         output_field=DecimalField(max_digits=15, decimal_places=0)) / 10000000
    #            ),
    #     delaycost=(ExpressionWrapper(
    #         (F("cost") * (1 - F("complete_percent"))),
    #         output_field=DecimalField(max_digits=15, decimal_places=0))
    #     )
    #
    # )

    # loans_today = LoanDetil.objects.filter(complete_percent__lt=1, date=today).annotate(
    #     category_en=Value("Today", CharField()),
    #     category_fa=Value("امروز", CharField()),
    #     delay_days=Value(0, IntegerField()),
    #     mtday=Value(0, FloatField())
    # )
    #
    # loans_future = LoanDetil.objects.filter(complete_percent__lt=1, date__gt=today).annotate(
    #     category_en=Value("Future", CharField()),
    #     category_fa=Value("آینده", CharField()),
    #     delay_days=Value(0, IntegerField()),
    #     mtday=Value(0, FloatField())
    # )

    # final_loans = loans.union(loans_today, loans_future)
    # final_loans = loans.union(loans_today)

    # محاسبه تعداد وام‌ها، مجموع delay_days و مجموع mtday
    loan_stats = loans.aggregate(
        total_count=Count("id"),
        total_delaycost=Sum("delaycost") / 10000000000,
        total_mtday=Sum("mtday")/1000
    )

    day_report=MasterReport.objects.filter(day=today).last()

    if day_report and (day_report.total_delaycost != loan_stats["total_delaycost"] or day_report.total_mtday != loan_stats["total_mtday"]):
        day_report.total_delaycost = loan_stats["total_delaycost"]
        day_report.total_mtday = loan_stats["total_mtday"]
        day_report.save()



    context = {
        'title': 'اقساط معوق',
        'user': user,
        'loans': loans,
        "total_count": loan_stats["total_count"],
        "total_delaycost": loan_stats["total_delaycost"],
        "total_mtday": loan_stats["total_mtday"],

    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'loan-total.html', context)

# برای api
from django.http import JsonResponse

from django.http import JsonResponse
from django.db.models import ExpressionWrapper, F, IntegerField, Sum
from django.utils import timezone

def loan_summary_api(request):
    today = timezone.now().date()

    loans = LoanDetil.objects.filter(complete_percent__lt=1, date__lt=today).annotate(
        delay_days=(ExpressionWrapper(F("date") - today, output_field=IntegerField())) / -86400000000,
        mtday=(ExpressionWrapper((F("delay_days") * F("cost") * (1 - F("complete_percent"))), output_field=IntegerField())) / 10000000,
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

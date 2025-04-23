import logging
import jdatetime
from datetime import datetime, timedelta, date
from collections import defaultdict
from django.utils import timezone
from django.db.models import  Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from accounting.models import BedehiMoshtari
from custom_login.models import UserLog
from .models import MasterInfo, MasterReport, MonthlyReport
from khayyam import JalaliDate
from django.db.models import OuterRef, Subquery
logger = logging.getLogger(__name__)
from django.http import JsonResponse

from mahakupdate.models import (
    Factor, FactorDetaile, SanadDetail, Mtables,
    ChequesRecieve, ChequesPay, LoanDetil, AccCoding
)




month_names_persian = {
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
    12: 'اسفند'
}

def TarazCalFromReport(day):
    repo = MasterReport.objects.filter(day=day).last()

    if repo is None:
        # اگر گزارشی پیدا نشد، یک مقدار پیش‌فرض برگردانید یا خطا هندل کنید
        return {
            'khales_forosh': 0,
            'baha_tamam_forosh': 0,
            'sayer_hazine': 0,
            'sayer_daramad': 0,
            'sood_navizhe': 0,
            'sood_vizhe': 0,
            'asnad_daryaftani': 0,
            'asnad_pardakhtani': 0,
        }

    to_return = {
        'khales_forosh': repo.khales_forosh,
        'baha_tamam_forosh': repo.baha_tamam_forosh,
        'sayer_hazine': repo.sayer_hazine,
        'sayer_daramad': repo.sayer_daramad,
        'sood_navizhe': repo.sood_navizhe,
        'sood_vizhe': repo.sood_vizhe,
        'asnad_daryaftani': repo.asnad_daryaftani,
        'asnad_pardakhtani': repo.asnad_pardakhtani,  # جمع مقادیر asnad_pardakhtani
    }
    return to_return

def TarazCal(fday, lday, data):
    # ایجاد لیستی از تمام روزهای بین fday و lday
    day_range = [fday + timedelta(days=x) for x in range((lday - fday).days + 1)]

    # فیلتر کردن داده‌ها برای تمام روزها در یک بار
    current_data = defaultdict(int)
    for item in data:
        current_data[(item['date'], item['kol'])] = item['total_amount']
    khales_forosh = 0
    baha_tamam_forosh = 0
    sood_navizhe = 0
    sood_vizhe = 0
    active_day = 0
    sayer_hazine = 0
    sayer_daramad = 0
    daily_sood_navizhe = []  # لیست برای ذخیره مقادیر روزانه
    daily_sood_vizhe = []  # لیست برای ذخیره مقادیر روزانه
    asnad_daryaftan = []  # لیست برای ذخیره مقادیر asnad_daryaftan
    asnad_pardakhtan = []  # لیست برای ذخیره مقادیر asnad_pardakhtan

    for current_date in day_range:
        baha_tamam_forosh_d = current_data.get((current_date, 500), 0)
        sayer_hazine_d = current_data.get((current_date, 501), 0)
        daramad_forosh = current_data.get((current_date, 400), 0)
        sayer_daramad_d = current_data.get((current_date, 401), 0)
        barghasht_az_forosh = current_data.get((current_date, 403), 0)  # منفی است
        khales_forosh_d = daramad_forosh + barghasht_az_forosh
        asnad_daryaftani = current_data.get((current_date, 101), 0)  # محاسبه asnad_daryaftani
        asnad_pardakhtani = current_data.get((current_date, 200), 0)  # محاسبه asnad_pardakhtani

        # محاسبه مجموع روزانه
        daily_total = daramad_forosh + barghasht_az_forosh + baha_tamam_forosh_d
        daily_total_vizhe = daramad_forosh + barghasht_az_forosh + baha_tamam_forosh_d + sayer_daramad_d + sayer_hazine_d
        daily_sood_navizhe.append(daily_total)  # ذخیره مقدار روزانه
        daily_sood_vizhe.append(daily_total_vizhe)  # ذخیره مقدار روزانه

        if daramad_forosh != 0 or baha_tamam_forosh_d != 0:
            active_day += 1
        sood_navizhe += daily_total
        sood_vizhe += daily_total_vizhe
        khales_forosh += khales_forosh_d
        baha_tamam_forosh += baha_tamam_forosh_d
        sayer_hazine += sayer_hazine_d
        sayer_daramad += sayer_daramad_d
        # ذخیره مقدار asnad_daryaftani با علامت منفی
        asnad_daryaftan.append(-asnad_daryaftani)
        asnad_pardakhtan.append(asnad_pardakhtani)

    # محاسبه حداقل و حداکثر
    min_sood_navizhe = min(daily_sood_navizhe) / 10000000 if daily_sood_navizhe else 0
    max_sood_navizhe = max(daily_sood_navizhe) / 10000000 if daily_sood_navizhe else 0

    min_sood_vizhe = min(daily_sood_vizhe) / 10000000 if daily_sood_vizhe else 0
    max_sood_vizhe = max(daily_sood_vizhe) / 10000000 if daily_sood_vizhe else 0

    to_return = {
        'khales_forosh': khales_forosh / 10000000,
        'baha_tamam_forosh': baha_tamam_forosh / -10000000,
        'sayer_hazine': sayer_hazine / -10000000,
        'sayer_daramad': sayer_daramad / 10000000,
        'sood_navizhe': sood_navizhe / 10000000,
        'sood_vizhe': sood_vizhe / 10000000,
        'active_day': active_day,
        'ave_sood_navizhe': sood_navizhe / active_day / 10000000 if active_day > 0 else 0,
        'min_sood_navizhe': min_sood_navizhe,
        'max_sood_navizhe': max_sood_navizhe,
        'ave_sood_vizhe': sood_vizhe / active_day / 10000000 if active_day > 0 else 0,
        'min_sood_vizhe': min_sood_vizhe,
        'max_sood_vizhe': max_sood_vizhe,
        'asnad_daryaftani': sum(asnad_daryaftan) / 10000000,  # جمع مقادیر asnad_daryaftani
        'asnad_pardakhtani': sum(asnad_pardakhtan) / 10000000,  # جمع مقادیر asnad_pardakhtani
    }
    return to_return

def TarazCal1day(day, data,acc_year2):
    m_info=MasterInfo.objects.filter(acc_year=acc_year2).last()
    # فیلتر کردن داده‌ها برای تمام روزها در یک بار
    current_data = defaultdict(int)
    for item in data:
        current_data[(item['date'], item['kol'])] = item['total_amount']

    asnad_daryaftan = []  # لیست برای ذخیره مقادیر asnad_daryaftan
    asnad_pardakhtan = []  # لیست برای ذخیره مقادیر asnad_pardakhtan

    baha_tamam_forosh = current_data.get((day, 500), 0)
    # sayer_hazine = current_data.get((day, 501), 0)
    daramad_forosh = current_data.get((day, 400), 0)
    # sayer_daramad = current_data.get((day, 401), 0)
    barghasht_az_forosh = current_data.get((day, 403), 0)  # منفی است
    khales_forosh = daramad_forosh + barghasht_az_forosh
    asnad_daryaftani = current_data.get((day, 101), 0)  # محاسبه asnad_daryaftani
    asnad_pardakhtani = current_data.get((day, 200), 0)  # محاسبه asnad_pardakhtani




    # محاسبه مجموع روزانه
    sood_navizhe = daramad_forosh + barghasht_az_forosh + baha_tamam_forosh
    sood_vizhe = daramad_forosh + barghasht_az_forosh + baha_tamam_forosh - m_info.sayer_hazine_ave*10000000 + m_info.sayer_daramad_ave*10000000

    # ذخیره مقدار asnad_daryaftani با علامت منفی
    asnad_daryaftan.append(-asnad_daryaftani)
    asnad_pardakhtan.append(asnad_pardakhtani)

    to_return = {
        'khales_forosh': khales_forosh / 10000000,
        'baha_tamam_forosh': baha_tamam_forosh / -10000000,
        'sayer_hazine': m_info.sayer_hazine_ave,
        'sayer_daramad': m_info.sayer_daramad_ave,
        'sood_navizhe': sood_navizhe / 10000000,
        'sood_vizhe': sood_vizhe / 10000000,
        'asnad_daryaftani': sum(asnad_daryaftan) / 10000000,  # جمع مقادیر asnad_daryaftani
        'asnad_pardakhtani': sum(asnad_pardakhtan) / 10000000,  # جمع مقادیر asnad_pardakhtani
    }
    return to_return

def generate_calendar_data_cheque2(month, year, cheque_recive_data,cheque_pay_data,loan_detail_data):
    # مشخص کردن اولین روز ماه
    start_time2 = time.time()  # زمان شروع تابع

    first_day_of_month = jdatetime.date(year, month, 1)

    # روز شروع ماه (شنبه = 0, یکشنبه = 1, ...)
    start_day_of_week = first_day_of_month.weekday()
    print(f"61: {time.time() - start_time2:.2f} ثانیه")
    # برای بدست آوردن آخرین روز ماه شمسی
    lday = first_day_of_month + jdatetime.timedelta(days=30)
    if lday.month != month:
        lday = first_day_of_month + jdatetime.timedelta(days=29)
        if lday.month != month:
            lday = first_day_of_month + jdatetime.timedelta(days=28)
    last_day_of_month = lday
    # تولید ماتریس روزهای ماه
    print(f"62: {time.time() - start_time2:.2f} ثانیه")
    days_in_month = []
    max_cheque = 0
    week = [None] * start_day_of_week  # اضافه کردن روزهای خالی
    print(f"63: {time.time() - start_time2:.2f} ثانیه")

    for i in range((last_day_of_month - first_day_of_month).days + 1):
        print(f"64: {time.time() - start_time2:.2f} ثانیه")

        current_day = first_day_of_month + jdatetime.timedelta(days=i)
        recive = sum (item.total_mandeh for item in cheque_recive_data if item.cheque_date == current_day) /10000000
        pay = sum(item.total_mandeh for item in cheque_pay_data if item.cheque_date == current_day )/10000000
        max_cheque = max(max_cheque, abs(recive), abs(pay))
        # تبدیل تاریخ شمسی به میلادی
        current_day_gregorian = current_day.togregorian().isoformat()
        today_recive_cheque = cheque_recive_data.filter(cheque_date=current_day_gregorian).order_by('-cost')
        today_pay_cheque = cheque_pay_data.filter(cheque_date=current_day_gregorian).order_by('-cost')

        #وام ها
        loans = sum((Decimal(1) - Decimal(item.complete_percent)) * item.cost for item in loan_detail_data if
                    item.date == current_day) / Decimal(10000000)

        today_loans = loan_detail_data.filter(date=current_day_gregorian).order_by('-cost')

        day_info = {
            'jyear': current_day.year,
            'jmonth': current_day.month,
            'jday': current_day.day,
            'recive': -1* recive,
            'pay': pay,
            'today_recive_cheque': today_recive_cheque,
            'today_pay_cheque': today_pay_cheque,
            'today_loans': today_loans,

            'loans':loans,
        }
        week.append(day_info)
        if len(week) == 7 or current_day == last_day_of_month:
            days_in_month.append(week)
            week = []

    # اضافه کردن هفته‌ای که کمتر از 7 روز است
    if len(week) > 0:
        days_in_month.append(week + [None] * (7 - len(week)))
    print(f"65: {time.time() - start_time2:.2f} ثانیه")

    past_recive = sum(item.total_mandeh for item in cheque_recive_data if item.cheque_date < first_day_of_month) / 10000000
    post_recive= sum(item.total_mandeh for item in cheque_recive_data if item.cheque_date > last_day_of_month) / 10000000
    this_month_recive = sum(item.total_mandeh for item in cheque_recive_data if item.cheque_date >= first_day_of_month and item.cheque_date <= last_day_of_month) / 10000000

    past_pay = sum(item.total_mandeh for item in cheque_pay_data if item.cheque_date < first_day_of_month) / 10000000
    post_pay= sum(item.total_mandeh for item in cheque_pay_data if item.cheque_date > last_day_of_month) / 10000000
    this_month_pay = sum(item.total_mandeh for item in cheque_pay_data if item.cheque_date >= first_day_of_month and item.cheque_date <= last_day_of_month) / 10000000
    print(f"66: {time.time() - start_time2:.2f} ثانیه")


    month_cheque_data={
        'past_recive': past_recive*-1,
        'post_recive': post_recive*-1,
        'this_month_recive': this_month_recive*-1,
        'past_pay': past_pay,
        'post_pay': post_pay,
        'this_month_pay': this_month_pay,
    }


    print(f"67: {time.time() - start_time2:.2f} ثانیه")

    total_bedehkar=BedehiMoshtari.objects.filter(total_mandeh__lt=0).aggregate(total_mandeh=Sum('total_mandeh'))['total_mandeh'] or 0
    not_loan=BedehiMoshtari.objects.filter(total_mandeh__lt=0,loans_total=0).aggregate(total_mandeh=Sum('total_mandeh'))['total_mandeh'] or 0
    loan_gap=BedehiMoshtari.objects.filter(total_mandeh__lt=0,loans_total__gt=0,total_with_loans__lt=0).aggregate(total_with_loans=Sum('total_with_loans'))['total_with_loans'] or 0
    this_month_loan = sum((Decimal(1) - Decimal(item.complete_percent)) * item.cost for item in loan_detail_data if
                item.date >= first_day_of_month and item.date <= last_day_of_month) / Decimal(10000000)
    past_month_loan = sum((Decimal(1) - Decimal(item.complete_percent)) * item.cost for item in loan_detail_data if
                    item.date < first_day_of_month) / Decimal(10000000)
    post_month_loan = sum((Decimal(1) - Decimal(item.complete_percent)) * item.cost for item in loan_detail_data if
                          item.date > last_day_of_month) / Decimal(10000000)
    print(f"68: {time.time() - start_time2:.2f} ثانیه")

    # تبدیل به float
    not_loan = float(not_loan)
    loan_gap = float(loan_gap)
    total_bedehkar = float(total_bedehkar)
    print(f"69: {time.time() - start_time2:.2f} ثانیه")

    month_loan_data={
        'not_loan': -1.0/10000000.0 * not_loan,
        'loan_gap':-1.0/10000000.0 * loan_gap,
        'this_month_loan':this_month_loan,
        'past_month_loan':past_month_loan,
        'post_month_loan':post_month_loan,
        'total_bedehkar':-1/10000000 * total_bedehkar,

    }


    return days_in_month,max_cheque,month_cheque_data,month_loan_data
def generate_calendar_data_cheque(month, year, cheque_recive_data, cheque_pay_data, loan_detail_data):
    start_time2 = time.time()  # زمان شروع تابع

    # مشخص کردن اولین و آخرین روز ماه
    first_day_of_month = jdatetime.date(year, month, 1)
    lday = first_day_of_month + jdatetime.timedelta(days=30)
    if lday.month != month:
        lday = first_day_of_month + jdatetime.timedelta(days=29)
        if lday.month != month:
            lday = first_day_of_month + jdatetime.timedelta(days=28)
    last_day_of_month = lday
    start_day_of_week = first_day_of_month.weekday()
    print(f"61: {time.time() - start_time2:.2f} ثانیه")

    days_in_month = []
    max_cheque = 0
    week = [None] * start_day_of_week
    print(f"62: {time.time() - start_time2:.2f} ثانیه")

    # تبدیل لیست داده‌ها به دیکشنری برای افزایش سرعت دسترسی
    cheque_recive_dict = {item.cheque_date: item.total_mandeh for item in cheque_recive_data}
    cheque_pay_dict = {item.cheque_date: item.total_mandeh for item in cheque_pay_data}
    loan_detail_dict = {item.date: item for item in loan_detail_data}
    print(f"63: {time.time() - start_time2:.2f} ثانیه")

    for i in range((last_day_of_month - first_day_of_month).days + 1):
        print(f"64: {time.time() - start_time2:.2f} ثانیه")

        current_day = first_day_of_month + jdatetime.timedelta(days=i)
        current_day_gregorian = current_day.togregorian().isoformat()

        # محاسبات مربوط به چک‌های دریافتی و پرداختی
        recive = cheque_recive_dict.get(current_day, 0) / 10000000
        pay = cheque_pay_dict.get(current_day, 0) / 10000000
        max_cheque = max(max_cheque, abs(recive), abs(pay))

        # دریافت جزئیات چک‌ها و وام‌ها
        today_recive_cheque = cheque_recive_data.filter(cheque_date=current_day_gregorian).order_by('-cost')
        today_pay_cheque = cheque_pay_data.filter(cheque_date=current_day_gregorian).order_by('-cost')
        loans = sum((Decimal(1) - Decimal(item.complete_percent)) * item.cost for item in loan_detail_data if
                    item.date == current_day) / Decimal(10000000)
        today_loans = loan_detail_data.filter(date=current_day_gregorian).order_by('-cost')

        day_info = {
            'jyear': current_day.year,
            'jmonth': current_day.month,
            'jday': current_day.day,
            'recive': -1 * recive,
            'pay': pay,
            'today_recive_cheque': today_recive_cheque,
            'today_pay_cheque': today_pay_cheque,
            'today_loans': today_loans,
            'loans': loans,
        }
        week.append(day_info)

        if len(week) == 7 or current_day == last_day_of_month:
            days_in_month.append(week)
            week = []

    if len(week) > 0:
        days_in_month.append(week + [None] * (7 - len(week)))
    print(f"65: {time.time() - start_time2:.2f} ثانیه")

    # محاسبات چک‌های ماه گذشته و آینده
    past_recive = sum(item.total_mandeh for item in cheque_recive_data if item.cheque_date < first_day_of_month) / 10000000
    post_recive = sum(item.total_mandeh for item in cheque_recive_data if item.cheque_date > last_day_of_month) / 10000000
    this_month_recive = sum(item.total_mandeh for item in cheque_recive_data if first_day_of_month <= item.cheque_date <= last_day_of_month) / 10000000

    past_pay = sum(item.total_mandeh for item in cheque_pay_data if item.cheque_date < first_day_of_month) / 10000000
    post_pay = sum(item.total_mandeh for item in cheque_pay_data if item.cheque_date > last_day_of_month) / 10000000
    this_month_pay = sum(item.total_mandeh for item in cheque_pay_data if first_day_of_month <= item.cheque_date <= last_day_of_month) / 10000000
    print(f"66: {time.time() - start_time2:.2f} ثانیه")

    month_cheque_data = {
        'past_recive': past_recive * -1,
        'post_recive': post_recive * -1,
        'this_month_recive': this_month_recive * -1,
        'past_pay': past_pay,
        'post_pay': post_pay,
        'this_month_pay': this_month_pay,
    }
    print(f"67: {time.time() - start_time2:.2f} ثانیه")

    # محاسبات وام‌ها
    total_bedehkar = BedehiMoshtari.objects.filter(total_mandeh__lt=0).aggregate(total_mandeh=Sum('total_mandeh'))['total_mandeh'] or 0
    not_loan = BedehiMoshtari.objects.filter(total_mandeh__lt=0, loans_total=0).aggregate(total_mandeh=Sum('total_mandeh'))['total_mandeh'] or 0
    loan_gap = BedehiMoshtari.objects.filter(total_mandeh__lt=0, loans_total__gt=0, total_with_loans__lt=0).aggregate(total_with_loans=Sum('total_with_loans'))['total_with_loans'] or 0
    this_month_loan = sum((Decimal(1) - Decimal(item.complete_percent)) * item.cost for item in loan_detail_data if first_day_of_month <= item.date <= last_day_of_month) / Decimal(10000000)
    past_month_loan = sum((Decimal(1) - Decimal(item.complete_percent)) * item.cost for item in loan_detail_data if item.date < first_day_of_month) / Decimal(10000000)
    post_month_loan = sum((Decimal(1) - Decimal(item.complete_percent)) * item.cost for item in loan_detail_data if item.date > last_day_of_month) / Decimal(10000000)
    print(f"68: {time.time() - start_time2:.2f} ثانیه")

    not_loan = float(not_loan)
    loan_gap = float(loan_gap)
    total_bedehkar = float(total_bedehkar)
    print(f"69: {time.time() - start_time2:.2f} ثانیه")

    month_loan_data = {
        'not_loan': -1.0 / 10000000.0 * not_loan,
        'loan_gap': -1.0 / 10000000.0 * loan_gap,
        'this_month_loan': this_month_loan,
        'past_month_loan': past_month_loan,
        'post_month_loan': post_month_loan,
        'total_bedehkar': -1 / 10000000 * total_bedehkar,
    }

    return days_in_month, max_cheque, month_cheque_data, month_loan_data


def generate_calendar_data_chequesider1(month, year, cheque_recive_data, cheque_pay_data, loan_detail_data):
    start_time = time.time()  # زمان شروع تابع

    # مشخص کردن اولین و آخرین روز ماه
    first_day_of_month = jdatetime.date(year, month, 1)
    lday = first_day_of_month + jdatetime.timedelta(days=30)
    if lday.month != month:
        lday = first_day_of_month + jdatetime.timedelta(days=29)
        if lday.month != month:
            lday = first_day_of_month + jdatetime.timedelta(days=28)
    last_day_of_month = lday
    start_day_of_week = first_day_of_month.weekday()

    # تبدیل لیست داده‌ها به دیکشنری برای افزایش سرعت دسترسی
    cheque_recive_dict = {item.cheque_date: item.total_mandeh for item in cheque_recive_data}
    cheque_pay_dict = {item.cheque_date: item.total_mandeh for item in cheque_pay_data}
    loan_detail_dict = {item.date: item for item in loan_detail_data}

    # ليست ديتاهاي ماه
    days_in_month = []
    week = [None] * start_day_of_week
    max_cheque = 0

    # بارگذاری چک‌ها و وام‌ها
    today_recive_cheques = {}
    today_pay_cheques = {}
    today_loans = {}

    for current_day in (first_day_of_month + jdatetime.timedelta(days=i) for i in range((last_day_of_month - first_day_of_month).days + 1)):
        current_day_gregorian = current_day.togregorian().isoformat()

        # محاسبات مربوط به چک‌های دریافتی و پرداختی
        recive = cheque_recive_dict.get(current_day, 0) / 10000000
        pay = cheque_pay_dict.get(current_day, 0) / 10000000
        max_cheque = max(max_cheque, abs(recive), abs(pay))

        # دریافت جزئیات چک‌ها و وام‌ها
        today_recive_cheque = today_recive_cheques.setdefault(current_day_gregorian, cheque_recive_data.filter(cheque_date=current_day_gregorian).order_by('-cost'))
        today_pay_cheque = today_pay_cheques.setdefault(current_day_gregorian, cheque_pay_data.filter(cheque_date=current_day_gregorian).order_by('-cost'))
        loans = today_loans.setdefault(current_day_gregorian, sum((Decimal(1) - Decimal(item.complete_percent)) * item.cost for item in loan_detail_data if item.date == current_day) / Decimal(10000000))

        day_info = {
            'jyear': current_day.year,
            'jmonth': current_day.month,
            'jday': current_day.day,
            'recive': -1 * recive,
            'pay': pay,
            'today_recive_cheque': today_recive_cheque,
            'today_pay_cheque': today_pay_cheque,
            'today_loans': today_loans,
            'loans': loans,
        }
        week.append(day_info)

        if len(week) == 7 or current_day == last_day_of_month:
            days_in_month.append(week)
            week = []

    if len(week) > 0:
        days_in_month.append(week + [None] * (7 - len(week)))

    # محاسبات چک‌های ماه گذشته و آینده
    past_recive = sum(item.total_mandeh for item in cheque_recive_data if item.cheque_date < first_day_of_month) / 10000000
    post_recive = sum(item.total_mandeh for item in cheque_recive_data if item.cheque_date > last_day_of_month) / 10000000
    this_month_recive = sum(item.total_mandeh for item in cheque_recive_data if first_day_of_month <= item.cheque_date <= last_day_of_month) / 10000000

    past_pay = sum(item.total_mandeh for item in cheque_pay_data if item.cheque_date < first_day_of_month) / 10000000
    post_pay = sum(item.total_mandeh for item in cheque_pay_data if item.cheque_date > last_day_of_month) / 10000000
    this_month_pay = sum(item.total_mandeh for item in cheque_pay_data if first_day_of_month <= item.cheque_date <= last_day_of_month) / 10000000

    month_cheque_data = {
        'past_recive': past_recive * -1,
        'post_recive': post_recive * -1,
        'this_month_recive': this_month_recive * -1,
        'past_pay': past_pay,
        'post_pay': post_pay,
        'this_month_pay': this_month_pay,
    }

    # محاسبات وام‌ها
    total_bedehkar = float(BedehiMoshtari.objects.filter(total_mandeh__lt=0).aggregate(total_mandeh=Sum('total_mandeh'))['total_mandeh'] or 0)
    not_loan = float(BedehiMoshtari.objects.filter(total_mandeh__lt=0, loans_total=0).aggregate(total_mandeh=Sum('total_mandeh'))['total_mandeh'] or 0)
    loan_gap = float(BedehiMoshtari.objects.filter(total_mandeh__lt=0, loans_total__gt=0, total_with_loans__lt=0).aggregate(total_with_loans=Sum('total_with_loans'))['total_with_loans'] or 0)
    this_month_loan = sum((Decimal(1) - Decimal(item.complete_percent)) * item.cost for item in loan_detail_data if first_day_of_month <= item.date <= last_day_of_month) / Decimal(10000000)
    past_month_loan = sum((Decimal(1) - Decimal(item.complete_percent)) * item.cost for item in loan_detail_data if item.date < first_day_of_month) / Decimal(10000000)
    post_month_loan = sum((Decimal(1) - Decimal(item.complete_percent)) * item.cost for item in loan_detail_data if item.date > last_day_of_month) / Decimal(10000000)

    month_loan_data = {
        'not_loan': -1.0 / 10000000.0 * not_loan,
        'loan_gap': -1.0 / 10000000.0 * loan_gap,
        'this_month_loan': this_month_loan,
        'past_month_loan': past_month_loan,
        'post_month_loan': post_month_loan,
        'total_bedehkar': -1 / 10000000 * total_bedehkar,
    }

    print(f"Total execution time: {time.time() - start_time:.2f} seconds")
    return days_in_month, max_cheque, month_cheque_data, month_loan_data


def generate_calendar_data_chequesider2(month, year, cheque_recive_data, cheque_pay_data, loan_detail_data):
    start_time = time.time()  # زمان شروع تابع

    # مشخص کردن اولین و آخرین روز ماه
    first_day_of_month = jdatetime.date(year, month, 1)
    last_day_of_month = first_day_of_month + jdatetime.timedelta(days=30)
    while last_day_of_month.month != month:
        last_day_of_month -= jdatetime.timedelta(days=1)
    start_day_of_week = first_day_of_month.weekday()

    # تبدیل لیست داده‌ها به دیکشنری برای افزایش سرعت دسترسی
    cheque_recive_dict = {item.cheque_date: item.total_mandeh for item in cheque_recive_data}
    cheque_pay_dict = {item.cheque_date: item.total_mandeh for item in cheque_pay_data}

    loan_dates = {item.date: item for item in loan_detail_data}

    days_in_month = []
    week = [None] * start_day_of_week
    max_cheque = 0

    cheque_recive_data_gregorian = {item.cheque_date.togregorian().isoformat(): item for item in cheque_recive_data}
    cheque_pay_data_gregorian = {item.cheque_date.togregorian().isoformat(): item for item in cheque_pay_data}

    loans_by_date = {}
    for item in loan_detail_data:
        loan_date = item.date.togregorian().isoformat()
        if loan_date not in loans_by_date:
            loans_by_date[loan_date] = []
        loans_by_date[loan_date].append(item)

    for i in range((last_day_of_month - first_day_of_month).days + 1):
        current_day = first_day_of_month + jdatetime.timedelta(days=i)
        current_day_gregorian = current_day.togregorian().isoformat()

        # محاسبات مربوط به چک‌های دریافتی و پرداختی
        recive = cheque_recive_dict.get(current_day, 0) / 10000000
        pay = cheque_pay_dict.get(current_day, 0) / 10000000
        max_cheque = max(max_cheque, abs(recive), abs(pay))

        # بدست آوردن جزئیات چک‌ها و وام‌ها
        today_recive_cheque = cheque_recive_data_gregorian.get(current_day_gregorian, None)
        today_pay_cheque = cheque_pay_data_gregorian.get(current_day_gregorian, None)

        loans_today = loans_by_date.get(current_day_gregorian, [])
        loans = sum((Decimal(1) - Decimal(item.complete_percent)) * item.cost for item in loans_today) / Decimal(
            10000000)

        day_info = {
            'jyear': current_day.year,
            'jmonth': current_day.month,
            'jday': current_day.day,
            'recive': -1 * recive,
            'pay': pay,
            'today_recive_cheque': today_recive_cheque,
            'today_pay_cheque': today_pay_cheque,
            'today_loans': loans_today,
            'loans': loans,
        }
        week.append(day_info)

        if len(week) == 7 or current_day == last_day_of_month:
            days_in_month.append(week)
            week = []

    if len(week) > 0:
        days_in_month.append(week + [None] * (7 - len(week)))

        # محاسبات چک‌های ماه گذشته و آینده
    past_recive = sum(
        item.total_mandeh for item in cheque_recive_data if item.cheque_date < first_day_of_month) / 10000000
    post_recive = sum(
        item.total_mandeh for item in cheque_recive_data if item.cheque_date > last_day_of_month) / 10000000
    this_month_recive = sum(item.total_mandeh for item in cheque_recive_data if
                            first_day_of_month <= item.cheque_date <= last_day_of_month) / 10000000

    past_pay = sum(item.total_mandeh for item in cheque_pay_data if item.cheque_date < first_day_of_month) / 10000000
    post_pay = sum(item.total_mandeh for item in cheque_pay_data if item.cheque_date > last_day_of_month) / 10000000
    this_month_pay = sum(item.total_mandeh for item in cheque_pay_data if
                         first_day_of_month <= item.cheque_date <= last_day_of_month) / 10000000

    month_cheque_data = {
        'past_recive': past_recive * -1,
        'post_recive': post_recive * -1,
        'this_month_recive': this_month_recive * -1,
        'past_pay': past_pay,
        'post_pay': post_pay,
        'this_month_pay': this_month_pay,
    }

    # محاسبات وام‌ها
    total_bedehkar = BedehiMoshtari.objects.filter(total_mandeh__lt=0).aggregate(total_mandeh=Sum('total_mandeh'))[
                         'total_mandeh'] or 0
    not_loan = \
    BedehiMoshtari.objects.filter(total_mandeh__lt=0, loans_total=0).aggregate(total_mandeh=Sum('total_mandeh'))[
        'total_mandeh'] or 0
    loan_gap = BedehiMoshtari.objects.filter(total_mandeh__lt=0, loans_total__gt=0, total_with_loans__lt=0).aggregate(
        total_with_loans=Sum('total_with_loans'))['total_with_loans'] or 0

    this_month_loan = sum((Decimal(1) - Decimal(item.complete_percent)) * item.cost for item in loan_detail_data if
                          first_day_of_month <= item.date <= last_day_of_month) / Decimal(10000000)
    past_month_loan = sum((Decimal(1) - Decimal(item.complete_percent)) * item.cost for item in loan_detail_data if
                          item.date < first_day_of_month) / Decimal(10000000)
    post_month_loan = sum((Decimal(1) - Decimal(item.complete_percent)) * item.cost for item in loan_detail_data if
                          item.date > last_day_of_month) / Decimal(10000000)

    month_loan_data = {
        'not_loan': -1.0 / 10000000.0 * float(not_loan),
        'loan_gap': -1.0 / 10000000.0 * float(loan_gap),
        'this_month_loan': this_month_loan,
        'past_month_loan': past_month_loan,
        'post_month_loan': post_month_loan,
        'total_bedehkar': -1 / 10000000 * float(total_bedehkar),
    }

    print(f"Total execution time: {time.time() - start_time:.2f} seconds")
    return days_in_month, max_cheque, month_cheque_data, month_loan_data
@login_required(login_url='/login')
def Home1(request, *args, **kwargs):
    user_agent = request.META['HTTP_USER_AGENT']
    # if 'Mobile' in user_agent or 'Tablet' in user_agent:
    is_not_mobile = True
    print('user_agent:')
    print(user_agent)
    if 'Mobile' in user_agent:
        is_not_mobile=False
    print('is_not_mobile:')
    print(is_not_mobile)

    minfo=MasterInfo.objects.filter(is_active=True).last()
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='داشبورد 1')

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
        print(f"12: {time.time() - start_time:.2f} ثانیه")
        months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
        month_name = months[current_month - 1]
        print("**Current Year:", current_year, "Current Month:", current_month)

        cheque_recive_data = ChequesRecieve.objects.exclude(total_mandeh=0)
        cheque_pay_data = ChequesPay.objects.exclude(total_mandeh=0)

        loan_detail_data = LoanDetil.objects.filter(complete_percent__lt=1)

        days_in_month, max_cheque, month_cheque_data,month_loan_data = generate_calendar_data_cheque(current_month, current_year,
                                                                                     cheque_recive_data,
                                                                                     cheque_pay_data, loan_detail_data)

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

        total_time = time.time() - start_time  # محاسبه زمان اجرا
        print(f"زمان کل اجرای تابع: {total_time:.2f} ثانیه")
        return render(request, 'partial_calendar.html', context)



    today = date.today()
    yesterday = today - timedelta(days=1)
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
    start_date_jalali = jdatetime.date(acc_year, 1, 1)  # ۱ فروردین سال مالی
    start_date_gregorian = start_date_jalali.togregorian()  # تبدیل به میلادی
    last_update_time = Mtables.objects.filter(name='Sanad_detail').last().last_update_time

    # فیلتر کردن داده‌ها
    data = SanadDetail.objects.filter(
        acc_year=acc_year,
        is_active=True,
        date__range=(start_date_gregorian, today)
    ).filter(
        Q(kol__in=[500, 400, 403, 101, 401, 501,200])
    ).values('date', 'kol').annotate(total_amount=Sum('curramount'))
    print(f"1: {time.time() - start_time:.2f} ثانیه")

    # محاسبه داده‌ها
    # today_data = TarazCal(today, today, data)
    today_data = TarazCalFromReport(today)
    print(f"1.1: {time.time() - start_time:.2f} ثانیه")
    # yesterday_data = TarazCal(yesterday, yesterday, data)
    yesterday_data = TarazCalFromReport(yesterday)
    print(f"1.2: {time.time() - start_time:.2f} ثانیه")
    # محاسبه داده‌ها برای 8 روز اخیر
    # chart7_data = [TarazCal(today - timedelta(days=i), today - timedelta(days=i), data)['asnad_daryaftani'] for i in
    #                range(8)]
    print(f"2: {time.time() - start_time:.2f} ثانیه")

    # دریافت اطلاعات چک‌های دریافتی
    chequesr = ChequesRecieve.objects.aggregate(total_mandeh_sum=Sum('total_mandeh'))
    postchequesr = ChequesRecieve.objects.filter(cheque_date__gt=today).aggregate(total_mandeh_sum=Sum('total_mandeh'))
    pastchequesr = ChequesRecieve.objects.filter(cheque_date__lte=today).aggregate(total_mandeh_sum=Sum('total_mandeh'))
    print(f"3: {time.time() - start_time:.2f} ثانیه")

    r_chequ_data = {
        'tmandeh': (chequesr['total_mandeh_sum'] / 10000000) * -1,
        'pastmandeh': (pastchequesr['total_mandeh_sum'] / 10000000) * -1,
        'postmandeh': (postchequesr['total_mandeh_sum'] / 10000000) * -1,
    }
    print(f"4: {time.time() - start_time:.2f} ثانیه")

    # دریافت اطلاعات چک‌های پرداختی
    chequesr = ChequesPay.objects.aggregate(total_mandeh_sum=Sum('total_mandeh'))
    postchequesr = ChequesPay.objects.filter(cheque_date__gt=today).aggregate(total_mandeh_sum=Sum('total_mandeh'))
    pastchequesr = ChequesPay.objects.filter(cheque_date__lte=today).aggregate(total_mandeh_sum=Sum('total_mandeh'))

    p_chequ_data = {
        'tmandeh': (chequesr['total_mandeh_sum'] / 10000000) ,
        'pastmandeh': (pastchequesr['total_mandeh_sum'] / 10000000) ,
        'postmandeh': (postchequesr['total_mandeh_sum'] / 10000000) ,
    }
    print(f"5: {time.time() - start_time:.2f} ثانیه")

    # دریافت گزارش‌ها
    start_date = today - timedelta(days=114)
    end_date = today - timedelta(days=107)
    dayly_reports = MasterReport.objects.filter(day__range=[start_date, end_date]).order_by('-day')
    dayly_reports = MasterReport.objects.order_by('-day')[:7][::-1]
    print(f"6: {time.time() - start_time:.2f} ثانیه")

    # روزهای هفته به زبان فارسی
    day_names_persian = {
        0: 'دوشنبه',
        1: 'سه‌شنبه',
        2: 'چهارشنبه',
        3: 'پنج‌شنبه',
        4: 'جمعه',
        5: 'شنبه',
        6: 'یکشنبه',
    }

    print(f"7: {time.time() - start_time:.2f} ثانیه")

    chart1_data = {
        'labels': [day_names_persian[report.day.weekday()] for report in dayly_reports],  # تبدیل شماره روز به نام روز
        'khales_forosh': [report.khales_forosh for report in dayly_reports],
        'baha_tamam_forosh': [report.baha_tamam_forosh for report in dayly_reports],
        'sood_navizhe': [report.sood_navizhe for report in dayly_reports],
    }
    print(f"8: {time.time() - start_time:.2f} ثانیه")

    monthly_reports = MonthlyReport.objects.order_by('-year', '-month')[:12][::-1]
    chart2_data = {
        # 'labels': [f"{report.month_name} {report.year}" for report in monthly_reports],
        'labels': [f"{report.month_name}" for report in monthly_reports],
        'khales_forosh': [report.khales_forosh for report in monthly_reports],
        'baha_tamam_forosh': [report.baha_tamam_forosh for report in monthly_reports],
        'sood_navizhe': [report.sood_navizhe for report in monthly_reports],
    }
    print(f"9: {time.time() - start_time:.2f} ثانیه")

    chart4_data = {
        'labels': [day_names_persian[report.day.weekday()] for report in dayly_reports],  # تبدیل شماره روز به نام روز
        'total_daramad': [report.khales_forosh+report.sayer_daramad for report in dayly_reports],
        'total_hazineh': [report.baha_tamam_forosh+report.sayer_hazine for report in dayly_reports],
        'sood_vizhe': [report.sood_vizhe for report in dayly_reports],
    }
    print(f"10: {time.time() - start_time:.2f} ثانیه")

    chart5_data = {
        # 'labels': [f"{report.month_name} {report.year}" for report in monthly_reports],
        'labels': [f"{report.month_name}" for report in monthly_reports],
        'total_daramad': [report.khales_forosh + report.sayer_daramad for report in monthly_reports],
        'total_hazineh': [report.baha_tamam_forosh + report.sayer_hazine for report in monthly_reports],
        'sood_vizhe': [report.sood_vizhe for report in monthly_reports],
    }

    print(f"11: {time.time() - start_time:.2f} ثانیه")

    #تکمیل تقویم

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
    print(f"12: {time.time() - start_time:.2f} ثانیه")
    months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    month_name = months[current_month - 1]
    print("**Current Year:", current_year, "Current Month:", current_month)

    cheque_recive_data=ChequesRecieve.objects.exclude(total_mandeh=0)
    cheque_pay_data=ChequesPay.objects.exclude(total_mandeh=0)

    loan_detail_data = LoanDetil.objects.filter(complete_percent__lt=1)

    if is_not_mobile:
        days_in_month,max_cheque,month_cheque_data,month_loan_data = generate_calendar_data_cheque(current_month, current_year, cheque_recive_data,cheque_pay_data,loan_detail_data)
    else:
        days_in_month, max_cheque, month_cheque_data, month_loan_data=None,None,None,None

    print(f"13: {time.time() - start_time:.2f} ثانیه")

    context = {
        'title': 'داشبورد مدیریتی',
        'user': user,
        'minfo': minfo,
        # 'is_dark_mode': user.is_dark_mode,

        'last_update_time': last_update_time,
        'today_data': today_data,
        'yesterday_data': yesterday_data,
        'r_chequ_data': r_chequ_data,
        'p_chequ_data': p_chequ_data,





        'chart1_data': chart1_data,
        'chart2_data': chart2_data,
        'chart4_data': chart4_data,
        'chart5_data': chart5_data,
        # 'chart7_data': chart7_data,
        #for calendar
        'month_name': month_name,
        'year': current_year,
        'month': current_month,
        'days_in_month': days_in_month,
        'max_cheque': max_cheque,
        'month_cheque_data': month_cheque_data,
        'month_loan_data': month_loan_data,

    }

    total_time = time.time() - start_time  # محاسبه زمان اجرا
    print(f"زمان کل اجرای تابع: {total_time:.2f} ثانیه")

    # if request.headers.get('x-requested-with') == 'XMLHttpRequest':
    #     return render(request, 'partial_calendar.html', context)
    return render(request, 'home1.html', context)


def Home5(request):
    user = request.user

    factor = Factor.objects.all()
    mablagh_factor_total = factor.aggregate(Sum('mablagh_factor'))['mablagh_factor__sum']
    count_factor_total = factor.count()

    factor_detile = FactorDetaile.objects.all()
    count_factor_detile = factor_detile.count()

    for i in factor_detile:
        print(i.kala.name)
    print('i.kala=====================================================================.name')

    yakhfa = FactorDetaile.objects.filter(kala__name__contains='يخچال')
    mablagh_yakh = yakhfa.aggregate(Sum('mablagh_nahaee'))['mablagh_nahaee__sum']
    yakhdarsad = mablagh_yakh / mablagh_factor_total * 100

    lebafa = FactorDetaile.objects.filter(kala__name__contains='لباسشويي')
    mablagh_leba = lebafa.aggregate(Sum('mablagh_nahaee'))['mablagh_nahaee__sum']
    lebadarsad = mablagh_leba / mablagh_factor_total * 100

    colfa = FactorDetaile.objects.filter(kala__name__contains='کولر')
    mablagh_col = colfa.aggregate(Sum('mablagh_nahaee'))['mablagh_nahaee__sum']
    coldarsad = mablagh_col / mablagh_factor_total * 100

    print(mablagh_factor_total)

    context = {

        'factor': factor,
        'user': user,
        'mablagh_factor_total': mablagh_factor_total,
        'count_factor_total': count_factor_total,
        'factor_detile': factor_detile,
        'mablagh_yakh': mablagh_yakh,
        'yakhdarsad': yakhdarsad,

        'mablagh_leba': mablagh_leba,
        'lebadarsad': lebadarsad,

        'mablagh_col': mablagh_col,
        'coldarsad': coldarsad,
    }

    return render(request, 'homepage.html', context)



from django.db.models import Sum, Min, Max, Avg, F, ExpressionWrapper, FloatField

from django.db.models import Sum

import time
from decimal import Decimal
from django.shortcuts import redirect

def CreateTotalReport(request):
    start_time = time.time()  # زمان شروع ویو
    report = MasterInfo.objects.all()

    for repo in report:
        acc_year = repo.acc_year
        print('acc_year=', acc_year)

        sanad_details400 = SanadDetail.objects.filter(acc_year=acc_year, is_active=True, kol=400, curramount__gt=0)
        dates400 = sanad_details400.values_list('date', flat=True)
        unique_dates400 = set(dates400)
        active_day = len(unique_dates400)

        repo.active_day=active_day

        print('active_day=', active_day)

        sanad_details = SanadDetail.objects.filter(acc_year=acc_year, is_active=True)
        dates = sanad_details.values_list('date', flat=True)
        unique_dates = set(dates)
        date_rang = sorted(unique_dates)

        print('date_rang:',date_rang)

        sayer_hazine_total = sum([Decimal(sanad.curramount) for sanad in sanad_details if sanad.kol == 501]) / Decimal(
            10000000)
        sayer_daramad_total = sum([Decimal(sanad.curramount) for sanad in sanad_details if sanad.kol == 401]) / Decimal(
            10000000)
        repo.asnad_daryaftani = -sum([Decimal(sanad.curramount) for sanad in sanad_details if sanad.kol == 101]) / Decimal(
            10000000)
        repo.asnad_pardakhtani = sum([Decimal(sanad.curramount) for sanad in sanad_details if sanad.kol == 200]) / Decimal(
                    10000000)

        repo.sayer_hazine_ave = sayer_hazine_total / active_day * -1 if active_day else 0
        repo.sayer_daramad_ave = sayer_daramad_total / active_day if active_day else 0

        # ایجاد لیست سود ناویژه و ویژه برای تمام رکوردها
        sood_navizhe_list = []
        sood_vizhe_list = []

        for day in date_rang:
            print('day:',day)
            sanads = SanadDetail.objects.filter(acc_year=acc_year, is_active=True, date=day)
            print('len(sanads):',len(sanads))
            daramad_forosh = Decimal(sum([sanad.curramount for sanad in sanads if sanad.kol == 400])) / Decimal(
                10000000)
            print('daramad_forosh',daramad_forosh)
            baha_tamam_forosh = Decimal(sum([sanad.curramount for sanad in sanads if sanad.kol == 500])) / Decimal(
                10000000)
            barghasht_az_forosh = Decimal(sum([sanad.curramount for sanad in sanads if sanad.kol == 403])) / Decimal(
                10000000)

            if daramad_forosh > 0:
                sood_navizhe = daramad_forosh + barghasht_az_forosh + baha_tamam_forosh
                sood_navizhe_list.append(sood_navizhe)
                sood_vizhe = sood_navizhe + Decimal(repo.sayer_daramad_ave) - Decimal(repo.sayer_hazine_ave)
                sood_vizhe_list.append(sood_vizhe)

        sood_navizhe_list_positive = [value for value in sood_navizhe_list if value > 1]

        print('sood_navizhe_list:',sood_navizhe_list)

        # محاسبه حداقل، حداکثر، میانگین و مجموع سود ناویژه
        repo.sood_navizhe_min = min(sood_navizhe_list_positive) if sood_navizhe_list_positive else 0
        repo.sood_navizhe_max = max(sood_navizhe_list) if sood_navizhe_list else 0
        repo.sood_navizhe_ave = sum(sood_navizhe_list) / active_day if active_day else 0
        repo.sood_navizhe_total = sum(sood_navizhe_list)

        sood_vizhe_list_positive = [value for value in sood_vizhe_list if value > 1]

        # محاسبه حداقل، حداکثر، میانگین و مجموع سود ویژه
        repo.sood_vizhe_min = min(sood_vizhe_list_positive) if sood_vizhe_list_positive else 0
        repo.sood_vizhe_max = max(sood_vizhe_list) if sood_vizhe_list else 0
        repo.sood_vizhe_ave = sum(sood_vizhe_list) / active_day if active_day else 0
        repo.sood_vizhe_total = sum(sood_vizhe_list)

        repo.save()

    total_time = time.time() - start_time  # محاسبه زمان اجرا
    print(f"زمان کل اجرای تابع: {total_time:.2f} ثانیه")

    return redirect('/updatedb')


def CreateTotalReport9(request):
    start_time = time.time()  # زمان شروع ویو
    report=MasterInfo.objects.all()

    for repo in report:
        acc_year=repo.acc_year
        active_day=SanadDetail.objects.filter(acc_year=acc_year, is_active=True, kol=400,curramount__gt=0).count()

        daramad_forosh = SanadDetail.objects.filter(acc_year=acc_year, is_active=True, kol=400).aggregate(total_curramount=Sum('curramount') or 0)['total_curramount']
        baha_tamam_forosh = SanadDetail.objects.filter(acc_year=acc_year, is_active=True, kol=500).aggregate(total_curramount=Sum('curramount') or 0)['total_curramount']
        sayer_hazine = SanadDetail.objects.filter(acc_year=acc_year, is_active=True, kol=501).aggregate(total_curramount=Sum('curramount') or 0)['total_curramount']
        sayer_daramad = SanadDetail.objects.filter(acc_year=acc_year, is_active=True, kol=401).aggregate(total_curramount=Sum('curramount') or 0)['total_curramount']
        barghasht_az_forosh = SanadDetail.objects.filter(acc_year=acc_year, is_active=True, kol=403).aggregate(total_curramount=Sum('curramount') or 0)['total_curramount']

        repo.sayer_hazine_ave = sayer_hazine/active_day
        repo.sayer_daramad_ave =sayer_daramad/active_day
        repo.sood_navizhe_min =0
        repo.sood_navizhe_max =0
        repo.sood_navizhe_ave =0
        repo.sood_navizhe_total =daramad_forosh + barghasht_az_forosh + baha_tamam_forosh
        repo.sood_vizhe_min =0
        repo.sood_vizhe_max =0
        repo.sood_vizhe_ave =0
        repo.sood_vizhe_total = daramad_forosh + barghasht_az_forosh + baha_tamam_forosh + sayer_daramad + sayer_hazine

        repo.save()

        total_time = time.time() - start_time  # محاسبه زمان اجرا
        print(f"زمان کل اجرای تابع: {total_time:.2f} ثانیه")


    return redirect('/updatedb')


def CreateReport(request):
    start_time = time.time()  # زمان شروع ویو

    # بررسی وجود MasterInfo فعال
    master_info = MasterInfo.objects.filter(is_active=True).last()
    if not master_info:
        print("هیچ شرکت فعالی یافت نشد.")
        return

    acc_year = master_info.acc_year

    try:
        # تبدیل ۱/۱/سال مالی به تاریخ میلادی
        start_date_jalali = jdatetime.date(acc_year, 1, 1)  # ۱ فروردین سال مالی
        start_date_gregorian = start_date_jalali.togregorian()  # تبدیل به میلادی
    except Exception as e:
        logger.error(f"خطا در تبدیل تاریخ: {str(e)}")
        print("خطا در تبدیل تاریخ.")
        return

    # تاریخ کنونی
    end_date_gregorian = timezone.now().date()

    # لیست روزها بین تاریخ شروع و پایان
    all_days = []
    current_date = start_date_gregorian
    while current_date <= end_date_gregorian:
        all_days.append(current_date)
        current_date += timedelta(days=1)

    # گرفتن رکوردهای موجود در مدل MasterReport
    existing_reports = MasterReport.objects.filter(day__in=all_days).values_list('day', flat=True)
    existing_reports = set(existing_reports)  # تبدیل به مجموعه برای جستجوی سریع‌تر

    # ایجاد رکوردهای پیش‌فرض برای روزهای موجود در all_days که در existing_reports نیستند
    reports_to_create = []

    for day in all_days:
        if day not in existing_reports:
            reports_to_create.append(MasterReport(
                day=day,
                total_mojodi=0,
                value_of_purchased_goods=0,
                khales_forosh=0,
                baha_tamam_forosh=0,
                sayer_hazine=0,
                sayer_daramad=0,
                sood_navizhe=0,
                sood_vizhe=0,
                asnad_daryaftani=0,
                asnad_pardakhtani=0,
            ))

    # اگر رکوردهای جدیدی برای ایجاد وجود داشت، آنها را ذخیره کنید
    if reports_to_create:
        MasterReport.objects.bulk_create(reports_to_create)

    # قبل از ادامه به روزرسانی، بارگذاری گزارش‌ها
    report_days = MasterReport.objects.filter(day__range=(start_date_gregorian, end_date_gregorian))

    current_time = datetime.now()
    print('current_time.hour')
    print(current_time.hour)
    # بررسی اینکه آیا ساعت 1 بامداد است یا خیر
    if current_time.hour != 1:
        report_days = report_days.order_by('-day')[:10]

    # لیست برای به‌روزرسانی
    reports_to_update = []

    # جمع‌آوری اطلاعات از SanadDetail
    for report in report_days:
        current_date = report.day
        print(report.day)
        if not SanadDetail.objects.filter(date=current_date):
            continue
        acc_year2=SanadDetail.objects.filter(date= current_date).last().acc_year
        data = SanadDetail.objects.filter(
            # acc_year=acc_year,
            is_active=True,
            date= current_date
        ).filter(
            # Q(kol=500) | Q(kol=400) | Q(kol=403) | Q(kol=101) | Q(kol=401) | Q(kol=501)| Q(kol=200)
            Q(kol=500) | Q(kol=400) | Q(kol=403) | Q(kol=101) | Q(kol=200)
        ).values('date', 'kol').annotate(total_amount=Sum('curramount'))

        # محاسبه داده‌ها برای روزهای مختلف
        # today_data = TarazCal(current_date, current_date, data)
        today_data = TarazCal1day(current_date, data,acc_year2)

        report.khales_forosh = today_data['khales_forosh']
        report.baha_tamam_forosh = today_data['baha_tamam_forosh']
        report.sayer_hazine = today_data['sayer_hazine']
        report.sayer_daramad = today_data['sayer_daramad']
        report.sood_navizhe = today_data['sood_navizhe']
        report.sood_vizhe = today_data['sood_vizhe']
        report.asnad_daryaftani = today_data['asnad_daryaftani']
        report.asnad_pardakhtani = today_data['asnad_pardakhtani']

        reports_to_update.append(report)  # افزودن به لیست برای بروزرسانی در batch
    # آپدیت تمامی رکوردها به صورت bulk
    if reports_to_update:
        MasterReport.objects.bulk_update(reports_to_update, [
            'khales_forosh',
            'baha_tamam_forosh',
            'sayer_hazine',
            'sayer_daramad',
            'sood_navizhe',
            'sood_vizhe',
            'asnad_daryaftani',
            'asnad_pardakhtani'
        ])

    # محاسبه زمان اجرای ویو
    end_time = time.time()
    execution_time = end_time - start_time

    # ذخیره زمان آخرین گزارش در مدل MasterInfo
    master_info.last_report_time = timezone.now()
    master_info.save()

    # چاپ نتیجه در کنسول
    print(f"message: گزارش‌ها با موفقیت ایجاد شدند")
    print(f"execution_time: {execution_time:.2f} ثانیه")
    print(f"start_date: {start_date_gregorian}")
    print(f"end_date: {end_date_gregorian}")

    return redirect('/updatedb')





def get_last_day_of_jalali_month(year, month):
    if month == 12:
        return jdatetime.date(year + 1, 1, 1) - timedelta(days=1)  # آخرین روز اسفند
    else:
        return jdatetime.date(year, month + 1, 1) - timedelta(days=1)  # آخرین روز ماه


def CreateMonthlyReport(request):
    start_time = time.time()  # زمان شروع ویو

    # بررسی وجود MasterInfo فعال
    master_info = MasterInfo.objects.filter(is_active=True).last()
    if not master_info:
        print("هیچ شرکت فعالی یافت نشد.")
        return

    acc_year = master_info.acc_year

    try:
        # تبدیل ۱/۱/سال مالی به تاریخ میلادی
        start_date_jalali = jdatetime.date(acc_year, 1, 1)  # ۱ فروردین سال مالی
        start_date_gregorian = start_date_jalali.togregorian()  # تبدیل به میلادی
    except Exception as e:
        print("خطا در تبدیل تاریخ:", e)
        return

    # تاریخ کنونی
    end_date_gregorian = timezone.now().date()

    # لیست ماه‌های بین تاریخ شروع و پایان
    all_months = []
    current_date = start_date_gregorian
    while current_date <= end_date_gregorian:
        jalali_date = jdatetime.date.fromgregorian(date=current_date)
        year = jalali_date.year
        month = jalali_date.month
        month_name = jalali_date.strftime('%B')  # نام ماه به فارسی

        # محاسبه روز اول و آخر ماه
        month_first_day_jalali = jdatetime.date(year, month, 1)
        month_last_day_jalali = get_last_day_of_jalali_month(year, month)

        # تبدیل به میلادی
        month_first_day = month_first_day_jalali.togregorian()
        month_last_day = month_last_day_jalali.togregorian()

        all_months.append({
            'year': year,
            'month': month,
            'month_name': month_name,
            'month_first_day': month_first_day,
            'month_last_day': month_last_day,
        })

        # به ماه بعد بروید
        if month == 12:
            current_date = jdatetime.date(year + 1, 1, 1).togregorian()
        else:
            current_date = (jdatetime.date(year, month + 1, 1)).togregorian()

    # گرفتن رکوردهای موجود در مدل MonthlyReport
    existing_reports = MonthlyReport.objects.filter(
        year__in=[m['year'] for m in all_months],
        month__in=[m['month'] for m in all_months]
    ).values_list('year', 'month')
    existing_reports = set(existing_reports)  # تبدیل به مجموعه برای جستجوی سریع‌تر

    # ایجاد رکوردهای پیش‌فرض برای ماه‌های موجود در all_months که در existing_reports نیستند
    reports_to_create = []

    for month_data in all_months:
        if (month_data['year'], month_data['month']) not in existing_reports:
            reports_to_create.append(MonthlyReport(
                year=month_data['year'],
                month=month_data['month'],
                month_name=month_data['month_name'],
                month_first_day=month_data['month_first_day'],
                month_last_day=month_data['month_last_day'],
            ))

    # اگر رکوردهای جدیدی برای ایجاد وجود داشت، آنها را ذخیره کنید
    if reports_to_create:
        MonthlyReport.objects.bulk_create(reports_to_create)

    # آپدیت رکوردها
    report_months = MonthlyReport.objects.filter(
        year__in=[m['year'] for m in all_months],
        month__in=[m['month'] for m in all_months]
    )

    reports_to_update = []
    # جمع‌آوری اطلاعات از SanadDetail
    for report in report_months:
        current_date_start = report.month_first_day
        current_date_end = report.month_last_day

        data = SanadDetail.objects.filter(
            # acc_year=acc_year,
            is_active=True,
            date__range=(current_date_start, current_date_end)
        ).filter(
            Q(kol=500) | Q(kol=400) | Q(kol=403) | Q(kol=101) | Q(kol=401) | Q(kol=501)| Q(kol=200)
        ).values('date', 'kol').annotate(total_amount=Sum('curramount'))

        # محاسبه داده‌ها برای ماه‌های مختلف
        month_data = TarazCal(current_date_start, current_date_end, data)

        report.khales_forosh = month_data['khales_forosh']
        report.baha_tamam_forosh = month_data['baha_tamam_forosh']
        report.sayer_hazine = month_data['sayer_hazine']
        report.sayer_daramad = month_data['sayer_daramad']
        report.sood_navizhe = month_data['sood_navizhe']
        report.sood_vizhe = month_data['sood_vizhe']
        report.asnad_daryaftani = month_data['asnad_daryaftani']
        report.asnad_pardakhtani = month_data['asnad_pardakhtani']

        reports_to_update.append(report)  # افزودن به لیست برای بروزرسانی در batch

    # آپدیت تمامی رکوردها به صورت bulk
    if reports_to_update:
        MonthlyReport.objects.bulk_update(reports_to_update, [
            'khales_forosh',
            'baha_tamam_forosh',
            'sayer_hazine',
            'sayer_daramad',
            'sood_navizhe',
            'sood_vizhe',
            'asnad_daryaftani',
            'asnad_pardakhtani'
        ])

    # محاسبه زمان اجرای ویو
    end_time = time.time()
    execution_time = end_time - start_time

    # ذخیره زمان آخرین گزارش در مدل MasterInfo
    master_info.last_report_time = timezone.now()
    master_info.save()

    # چاپ نتیجه در کنسول
    print(f"message: گزارش‌ها با موفقیت ایجاد شدند")
    print(f"execution_time: {execution_time:.2f} ثانیه")
    print(f"start_date: {start_date_gregorian}")
    print(f"end_date: {end_date_gregorian}")

    return redirect('/updatedb')



@login_required(login_url='/login')
def ReportsDailySummary(request):
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='خلاصه گزارش های روزانه')
    start_time = time.time()  # زمان شروع تابع
    dailyr= MasterReport.objects.all().order_by('-day')








    total_time = time.time() - start_time  # محاسبه زمان اجرا
    print(f"زمان کل اجرای تابع: {total_time:.2f} ثانیه")


    context = {
        'title': 'خلاصه گزارش های روزانه',
        'user': user,
        'dailyr': dailyr,
    }

    return render(request, 'reports_daily_summary.html', context)





@login_required(login_url='/login')
def ReportsDailyDetile(request, *args, **kwargs):
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='گزارش های روز')
    start_time = time.time()  # زمان شروع تابع
    day = kwargs['day']
    try:
        # فرض کنیم فرمت day در URL به شکل 'YYYY-MM-DD' است
        day_date = datetime.strptime(day, '%Y-%m-%d').date()
        print('Converted day to date:')
        print(day_date)
    except ValueError:
        print('Invalid date format:', day)

    kol=(500, 400, 403, 401, 501)
    # sanads=SanadDetail.objects.filter(date=day_date,kol__in=kol)

    sanads = SanadDetail.objects.filter(date=day_date, kol__in=kol).annotate(
        acc_name=Subquery(
            AccCoding.objects.filter(code=OuterRef('kol')).values('name')[:1]
        )
    )



    print(len(sanads))


    total_time = time.time() - start_time  # محاسبه زمان اجرا
    print(f"زمان کل اجرای تابع: {total_time:.2f} ثانیه")

    day_report = MasterReport.objects.filter(day=day_date).last()
    minfo=MasterInfo.objects.filter(is_active=True).last()

    context = {
        'title': 'گزارش روز',
        'user': user,
        'day_date': day_date,
        'minfo': minfo,
        'sanads': sanads,
        'day_report': day_report,
    }

    return render(request, 'reports_daily_detail.html', context)

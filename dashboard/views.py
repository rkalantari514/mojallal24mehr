import logging
logger = logging.getLogger(__name__)
from custom_login.models import UserLog
from mahakupdate.models import Factor, FactorDetaile, SanadDetail, Mtables
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import MasterInfo, MasterReport
from django.utils import timezone
import jdatetime
import time
from django.db.models import Sum
from datetime import date, timedelta

from django.db.models import Sum, Q

from django.db.models import Q


from collections import defaultdict

from collections import defaultdict
from django.db.models import Sum, Q
from datetime import timedelta

def TarazCal(fday, lday):
    # ایجاد لیستی از تمام روزهای بین fday و lday
    day_range = [fday + timedelta(days=x) for x in range((lday - fday).days + 1)]

    # فیلتر کردن داده‌ها برای تمام روزها در یک بار
    data = SanadDetail.objects.filter(
        date__range=(fday, lday)
    ).filter(
        Q(kol=500) | Q(kol=400)
    ).values('date', 'kol').annotate(total_amount=Sum('curramount'))

    sood_navizhe = 0
    active_day = 0
    daily_sood_navizhe = []  # لیست برای ذخیره مقادیر روزانه

    # استفاده از defaultdict برای ذخیره‌سازی داده‌ها
    current_data = defaultdict(int)
    for item in data:
        current_data[(item['date'], item['kol'])] = item['total_amount']

    for current_date in day_range:
        baha_tamam_forosh = current_data.get((current_date, 500), 0)
        daramad_forosh = current_data.get((current_date, 400), 0)

        # محاسبه مجموع روزانه
        daily_total = daramad_forosh + baha_tamam_forosh
        daily_sood_navizhe.append(daily_total)  # ذخیره مقدار روزانه

        if daramad_forosh != 0 or baha_tamam_forosh != 0:
            active_day += 1

        sood_navizhe += daily_total

    # محاسبه حداقل و حداکثر
    min_sood_navizhe = min(daily_sood_navizhe) / 10000000 if daily_sood_navizhe else 0
    max_sood_navizhe = max(daily_sood_navizhe) / 10000000 if daily_sood_navizhe else 0

    to_return = {
        'sood_navizhe': sood_navizhe / 10000000,
        'active_day': active_day,
        'ave_sood_navizhe': sood_navizhe / active_day / 10000000 if active_day > 0 else 0,
        'min_sood_navizhe': min_sood_navizhe,
        'max_sood_navizhe': max_sood_navizhe,
    }

    return to_return
@login_required(login_url='/login')
def Home1(request, *args, **kwargs):
    user=request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(
            user=user,
            page='داشبورد 1',
        )
    start_time = time.time()  # زمان شروع تابع

    today = date.today()
    yesterday = today - timedelta(days=1)
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
    start_date_jalali = jdatetime.date(acc_year, 1, 1)  # ۱ فروردین سال مالی
    start_date_gregorian = start_date_jalali.togregorian()  # تبدیل به میلادی
    last_update_time=Mtables.objects.filter(name='Sanad_detail').last().last_update_time
    today_data=TarazCal(today,today)
    yesterday_data=TarazCal(yesterday,yesterday)
    allday_data=TarazCal(start_date_gregorian,today)
    print(today_data)
    print(yesterday_data)
    context = {
        'title': 'داشبورد مدیرریتی',
        'user': user,
        'last_update_time': last_update_time,
        'today_data': today_data,
        'yesterday_data': yesterday_data,
        'allday_data': allday_data,

    }

    total_time = time.time() - start_time  # محاسبه زمان اجرا
    print(f"زمان کل اجرای تابع: {total_time:.2f} ثانیه")
    return render(request, 'home1.html', context)




@login_required(login_url='/login')
def Home5(request):
    user=request.user

    factor=Factor.objects.all()
    mablagh_factor_total = factor.aggregate(Sum('mablagh_factor'))['mablagh_factor__sum']
    count_factor_total = factor.count()





    factor_detile=FactorDetaile.objects.all()
    count_factor_detile = factor_detile.count()







    for i in factor_detile:
        print(i.kala.name)
    print('i.kala=====================================================================.name')




    yakhfa = FactorDetaile.objects.filter(kala__name__contains='يخچال')
    mablagh_yakh=yakhfa.aggregate(Sum('mablagh_nahaee'))['mablagh_nahaee__sum']
    yakhdarsad = mablagh_yakh /mablagh_factor_total*100

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
        'mablagh_factor_total':mablagh_factor_total,
        'count_factor_total':count_factor_total,
        'factor_detile':factor_detile,
        'mablagh_yakh':mablagh_yakh,
        'yakhdarsad':yakhdarsad,


        'mablagh_leba':mablagh_leba,
        'lebadarsad':lebadarsad,


        'mablagh_col':mablagh_col,
        'coldarsad':coldarsad,
    }



    return render(request, 'homepage.html',context)







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

    # تاریخ جاری
    end_date_gregorian = timezone.now().date()

    # شناسایی تمامی روزها بین تاریخ شروع و پایان گزارش
    report_days = MasterReport.objects.filter(day__range=(start_date_gregorian, end_date_gregorian))
    if time.time() != 1:
        report_days = MasterReport.objects.filter(day__range=(start_date_gregorian, end_date_gregorian)).order_by(
            '-day')[:10]

    # لیست برای به‌روزرسانی
    reports_to_update = []

    # جمع‌آوری اطلاعات از SanadDetail
    for report in report_days:

        current_date =report.day
        print(report.day)
        baha_tamam_forosh = SanadDetail.objects.filter(
            date=current_date,
            kol=500
        ).aggregate(Sum('curramount'))['curramount__sum'] or 0

        daramad_forosh = SanadDetail.objects.filter(
            date=current_date,
            kol=400
        ).aggregate(Sum('curramount'))['curramount__sum'] or 0

        # به‌روزرسانی مقادیر در MasterReport
        report.baha_tamam_forosh = -1 * baha_tamam_forosh
        report.daramad_forosh = daramad_forosh

        reports_to_update.append(report)  # افزودن به لیست برای بروزرسانی در batch

    # آپدیت تمامی رکوردها به صورت bulk
    if reports_to_update:
        MasterReport.objects.bulk_update(reports_to_update, ['baha_tamam_forosh', 'daramad_forosh'])

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
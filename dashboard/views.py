import logging
logger = logging.getLogger(__name__)
from custom_login.models import UserLog
from mahakupdate.models import Factor, FactorDetaile, SanadDetail, Mtables, ChequesRecieve
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .models import MasterInfo, MasterReport
from django.utils import timezone
from datetime import datetime
from collections import defaultdict
from datetime import timedelta, date
from django.db.models import Sum, Q
from django.shortcuts import render
import time
import jdatetime
import pandas as pd
import plotly.express as px

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from django.shortcuts import render


def TarazCal(fday, lday, data):
    # ایجاد لیستی از تمام روزهای بین fday و lday
    day_range = [fday + timedelta(days=x) for x in range((lday - fday).days + 1)]

    # فیلتر کردن داده‌ها برای تمام روزها در یک بار
    current_data = defaultdict(int)
    for item in data:
        current_data[(item['date'], item['kol'])] = item['total_amount']
    khales_forosh=0
    baha_tamam_forosh=0
    sood_navizhe = 0
    sood_vizhe = 0
    active_day = 0
    sayer_hazine=0
    sayer_daramad=0
    daily_sood_navizhe = []  # لیست برای ذخیره مقادیر روزانه
    daily_sood_vizhe = []  # لیست برای ذخیره مقادیر روزانه
    asnad_pardakhtani = []  # لیست برای ذخیره مقادیر asnad_pardakhtani

    for current_date in day_range:
        baha_tamam_forosh_d = current_data.get((current_date, 500), 0)
        sayer_hazine_d = current_data.get((current_date, 501), 0)
        daramad_forosh = current_data.get((current_date, 400), 0)
        sayer_daramad_d = current_data.get((current_date, 401), 0)
        barghasht_az_forosh = current_data.get((current_date, 403), 0) #منفی است
        khales_forosh_d=daramad_forosh+barghasht_az_forosh
        asnad_pardakhtan = current_data.get((current_date, 101), 0)  # محاسبه asnad_pardakhtani

        # محاسبه مجموع روزانه
        daily_total = daramad_forosh +barghasht_az_forosh+ baha_tamam_forosh_d
        daily_total_vizhe = daramad_forosh +barghasht_az_forosh+ baha_tamam_forosh_d+sayer_daramad_d+sayer_hazine_d
        daily_sood_navizhe.append(daily_total)  # ذخیره مقدار روزانه
        daily_sood_vizhe.append(daily_total_vizhe)  # ذخیره مقدار روزانه

        if daramad_forosh != 0 or baha_tamam_forosh_d != 0:
            active_day += 1

        sood_navizhe += daily_total
        sood_vizhe += daily_total_vizhe
        khales_forosh += khales_forosh_d
        baha_tamam_forosh += baha_tamam_forosh_d
        sayer_hazine+=sayer_hazine_d
        sayer_daramad+=sayer_daramad_d
        # ذخیره مقدار asnad_pardakhtani با علامت منفی
        asnad_pardakhtani.append(-asnad_pardakhtan)

    # محاسبه حداقل و حداکثر
    min_sood_navizhe = min(daily_sood_navizhe) / 10000000 if daily_sood_navizhe else 0
    max_sood_navizhe = max(daily_sood_navizhe) / 10000000 if daily_sood_navizhe else 0

    min_sood_vizhe = min(daily_sood_vizhe) / 10000000 if daily_sood_vizhe else 0
    max_sood_vizhe = max(daily_sood_vizhe) / 10000000 if daily_sood_vizhe else 0

    to_return = {
        'khales_forosh':khales_forosh/10000000,
        'baha_tamam_forosh':baha_tamam_forosh/-10000000,
        'sayer_hazine':sayer_hazine/-10000000,
        'sayer_daramad':sayer_daramad/10000000,
        'sood_navizhe': sood_navizhe / 10000000,
        'sood_vizhe': sood_vizhe / 10000000,
        'active_day': active_day,
        'ave_sood_navizhe': sood_navizhe / active_day / 10000000 if active_day > 0 else 0,
        'min_sood_navizhe': min_sood_navizhe,
        'max_sood_navizhe': max_sood_navizhe,
        'ave_sood_vizhe': sood_vizhe / active_day / 10000000 if active_day > 0 else 0,
        'min_sood_vizhe': min_sood_vizhe,
        'max_sood_vizhe': max_sood_vizhe,
        'asnad_pardakhtani': sum(asnad_pardakhtani) / 10000000,  # جمع مقادیر asnad_pardakhtani
    }
    return to_return


def TarazCalFromReport(day):

    repo=MasterReport.objects.filter(day=day).last()

    to_return = {
        'khales_forosh':repo.khales_forosh,
        'baha_tamam_forosh':repo.baha_tamam_forosh,
        'sayer_hazine':repo.sayer_hazine,
        'sayer_daramad':repo.sayer_daramad,
        'sood_navizhe': repo.sood_navizhe,
        'sood_vizhe': repo.sood_vizhe,
        'asnad_pardakhtani': repo.asnad_pardakhtani,  # جمع مقادیر asnad_pardakhtani
    }
    return to_return






    # reports = MasterReport.objects.order_by('-day')[:8]



@login_required(login_url='/login')
def Home1(request, *args, **kwargs):
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='داشبورد 1')

    start_time = time.time()  # زمان شروع تابع

    today = date.today()
    yesterday = today - timedelta(days=1)
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
    start_date_jalali = jdatetime.date(acc_year, 1, 1)  # ۱ فروردین سال مالی
    start_date_gregorian = start_date_jalali.togregorian()  # تبدیل به میلادی
    last_update_time = Mtables.objects.filter(name='Sanad_detail').last().last_update_time

    # فیلتر کردن داده‌ها
    data = SanadDetail.objects.filter(
        is_active=True,
        date__range=(start_date_gregorian, today)
    ).filter(
        Q(kol__in=[500, 400, 403, 101, 401, 501])
    ).values('date', 'kol').annotate(total_amount=Sum('curramount'))

    # محاسبه داده‌ها
    today_data = TarazCal(today, today, data)
    yesterday_data = TarazCal(yesterday, yesterday, data)
    allday_data = TarazCal(start_date_gregorian, today, data)

    # محاسبه داده‌ها برای 8 روز اخیر
    chart4_data = [TarazCal(today - timedelta(days=i), today - timedelta(days=i), data)['asnad_pardakhtani'] for i in range(8)]

    # دریافت اطلاعات چک‌ها
    chequesr = ChequesRecieve.objects.aggregate(total_mandeh_sum=Sum('total_mandeh'))
    postchequesr = ChequesRecieve.objects.filter(cheque_date__gt=today).aggregate(total_mandeh_sum=Sum('total_mandeh'))
    pastchequesr = ChequesRecieve.objects.filter(cheque_date__lte=today).aggregate(total_mandeh_sum=Sum('total_mandeh'))

    chequ_data = {
        'tmandeh': (chequesr['total_mandeh_sum'] / 10000000) * -1,
        'pastmandeh': (pastchequesr['total_mandeh_sum'] / 10000000) * -1,
        'postmandeh': (postchequesr['total_mandeh_sum'] / 10000000) * -1,
    }

    # دریافت گزارش‌ها
    start_date = today - timedelta(days=114)
    end_date = today - timedelta(days=107)
    reports = MasterReport.objects.filter(day__range=[start_date, end_date]).order_by('-day')
    reports = MasterReport.objects.order_by('-day')[:8]
    # آماده‌سازی داده‌ها برای نمودار
    data = {
        'day': [report.day for report in reports],
        'khales_forosh': [report.khales_forosh for report in reports],
        'baha_tamam_forosh': [-1 * report.baha_tamam_forosh for report in reports],
        'sood_navizhe': [report.sood_navizhe for report in reports],
    }

    df = pd.DataFrame(data)
    persian_names = {
        'khales_forosh': 'خالص فروش',
        'baha_tamam_forosh': 'بهای تمام شده فروش',
        'sood_navizhe': 'سود ناویژه',
    }

    df_melted = pd.melt(df, id_vars=['day'], value_vars=list(persian_names.keys()), var_name='Type', value_name='Value')
    df_melted['Type'] = df_melted['Type'].map(persian_names)

    color_map = {
        'خالص فروش': '#007bff',
        'بهای تمام شده فروش': '#FF0000',
        'سود ناویژه': '#00FF00',
    }

    # تنظیمات نمودار با عرض میله‌های کمتر و فاصله بیشتر
    fig = px.bar(
        df_melted,
        x='day',
        y='Value',
        color='Type',
        barmode='group',
        color_discrete_map=color_map,
        labels={'Type': '', 'day': '', 'Value': ''},
    )

    # تنظیم عرض میله‌ها و فاصله بین گروه‌ها
    fig.update_traces(width=0.3)  # عرض میله‌ها
    fig.update_layout(bargap=0.4)  # فاصله بین گروه‌های میله‌ها

    # روزهای هفته به زبان فارسی
    day_names_persian = {
        0: 'شنبه',
        1: 'یکشنبه',
        2: 'دوشنبه',
        3: 'سه‌شنبه',
        4: 'چهارشنبه',
        5: 'پنج‌شنبه',
        6: 'جمعه',
    }

    # اضافه کردن نام روزها در محور x
    fig.update_xaxes(tickvals=df['day'], ticktext=[day_names_persian[day.weekday()] for day in df['day']])

    fig.update_layout(
        font=dict(family="B Nazanin, Arial, sans-serif", size=14, color="#333333"),
        title_font=dict(family="B Nazanin, Arial, sans-serif", size=20, color="#333333"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        xaxis=dict(showgrid=True, gridcolor='#e0e0e0'),
        yaxis=dict(showgrid=True, gridcolor='#e0e0e0'),
        plot_bgcolor='#FFFFFF',
        paper_bgcolor='#FFFFFF',
    )

    # تولید نمودار به فرمت HTML
    fig_html = fig.to_html(full_html=False, include_plotlyjs='cdn')  # Include Plotly via CDN

    context = {
        'title': 'داشبورد مدیریتی',
        'user': user,
        'last_update_time': last_update_time,
        'today_data': today_data,
        'yesterday_data': yesterday_data,
        'allday_data': allday_data,
        'chequ_data': chequ_data,
        'chart4_data': chart4_data,
        'fig_html': fig_html,
    }

    total_time = time.time() - start_time  # محاسبه زمان اجرا
    print(f"زمان کل اجرای تابع: {total_time:.2f} ثانیه")
    return render(request, 'home1.html', context)














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

from datetime import timedelta

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
                asnad_pardakhtani=0,
            ))

    # اگر رکوردهای جدیدی برای ایجاد وجود داشت، آنها را ذخیره کنید
    if reports_to_create:
        MasterReport.objects.bulk_create(reports_to_create)

    # قبل از ادامه به روزرسانی، بارگذاری گزارش‌ها
    report_days = MasterReport.objects.filter(day__range=(start_date_gregorian, end_date_gregorian))

    current_time = datetime.now()

    # بررسی اینکه آیا ساعت 1 بامداد است یا خیر
    if current_time.hour != 1:
        report_days = report_days.order_by('-day')[:10]

    # لیست برای به‌روزرسانی
    reports_to_update = []

    # جمع‌آوری اطلاعات از SanadDetail
    for report in report_days:
        current_date = report.day
        print(report.day)

        data = SanadDetail.objects.filter(
            is_active=True,
            date__range=(current_date, current_date)
        ).filter(
            Q(kol=500) | Q(kol=400) | Q(kol=403) | Q(kol=101) | Q(kol=401) | Q(kol=501)
        ).values('date', 'kol').annotate(total_amount=Sum('curramount'))

        # محاسبه داده‌ها برای روزهای مختلف
        today_data = TarazCal(current_date, current_date, data)

        report.khales_forosh = today_data['khales_forosh']
        report.baha_tamam_forosh = today_data['baha_tamam_forosh']
        report.sayer_hazine = today_data['sayer_hazine']
        report.sayer_daramad = today_data['sayer_daramad']
        report.sood_navizhe = today_data['sood_navizhe']
        report.sood_vizhe = today_data['sood_vizhe']
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
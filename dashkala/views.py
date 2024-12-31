from django.contrib.gis.measure import pretty_name
from django.http import HttpResponseBadRequest
from django.contrib.auth.decorators import login_required

from custom_login.models import UserLog
from mahakupdate.models import Kardex, Mtables, Category, Mojodi, Storagek, Kala
from persianutils import standardize
from django.db.models import Max, Subquery
from .forms import FilterForm, KalaSelectForm, Kala_Detail_Form
import time
from django.shortcuts import render, redirect
from django.db.models import Sum, F, FloatField
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.db.models.functions import TruncMonth
from khayyam import JalaliDate, JalaliDatetime
from datetime import date
import jdatetime
from django.shortcuts import render


def fix_persian_characters(value):
    return standardize(value)

@login_required(login_url='/login')
def DsshKala(request):
    start_time = time.time()  # زمان شروع تابع
    default_storage_id = 3  # می‌توانید این مقدار را به ۳ تنظیم کنید یا از دیتابیس بگیرید
    # پردازش فرم فیلتر
    form = FilterForm(request.GET or None, initial={
        'storage': 7,

    })
    filters = {}

    if form.is_valid():
        if form.cleaned_data['kala']:
            filters['kala'] = form.cleaned_data['kala']
        if form.cleaned_data['storage']:
            filters['storage'] = form.cleaned_data['storage']
        if form.cleaned_data['category']:
            filters['kala__category'] = form.cleaned_data['category']  # فرض بر این است که Kala به Category مرتبط است

    # گرفتن آخرین آیدی برای هر `code_kala` و `warehousecode`
    latest_mojodi = Kardex.objects.values('code_kala', 'warehousecode').annotate(
        latest_id=Max('id')
    ).values('latest_id')  # فقط آخرین ID را برگردانید

    # استفاده از Subquery برای دریافت رکوردهای مربوط به آخرین موجودی و حذف موجودی‌های صفر
    mojodi = Kardex.objects.filter(
        id__in=Subquery(latest_mojodi),
        stock__gt=0  # حذف موجودی‌های صفر
    ).filter(**filters).select_related('kala')  # بارگذاری اطلاعات مرتبط با kala

    # پردازش موجودی‌ها و محاسبه ارزش
    for entry in mojodi:
        if entry.kala is not None:
            entry.kala.name = fix_persian_characters(entry.kala.name)
            entry.arzesh = entry.stock * entry.averageprice

    context = {
        'mojodi': mojodi,
        'form': form,
    }

    # تغییر بررسی درخواست AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'partials/mojodi_list.html', context)

    return render(request, 'totalkala.html', context)


def DsshKala2(request):
    start_time = time.time()  # زمان شروع تابع

    # گرفتن آخرین آیدی برای هر `code_kala` و `warehousecode`
    latest_mojodi = Kardex.objects.values('code_kala', 'warehousecode').annotate(
        latest_id=Max('id')
    ).values('latest_id')  # فقط آخرین ID را برگردانید

    # استفاده از Subquery برای دریافت رکوردهای مربوط به آخرین موجودی و حذف موجودی‌های صفر
    mojodi = Kardex.objects.filter(
        id__in=Subquery(latest_mojodi),
        stock__gt=0  # حذف موجودی‌های صفر
    ).select_related('kala')  # بارگذاری اطلاعات مرتبط با kala

    # پردازش موجودی‌ها و محاسبه ارزش
    for entry in mojodi:
        if entry.kala is not None:
            entry.kala.name = fix_persian_characters(entry.kala.name)
            entry.arzesh = entry.stock * entry.averageprice

    table = Mtables.objects.filter(name='Kardex').last()
    tsinse = (timezone.now() - table.last_update_time).total_seconds() / 60

    if tsinse / table.update_period >= 1:
        table.progress_bar_width = 100
        table.progress_class = 'skill2-bar bg-danger'
    elif tsinse / table.update_period < 0.4:
        table.progress_class = 'skill2-bar bg-success'
        table.progress_bar_width = tsinse / table.update_period * 100
    elif tsinse / table.update_period < 0.9:
        table.progress_bar_width = tsinse / table.update_period * 100
        table.progress_class = 'skill2-bar bg-warning'
    elif tsinse / table.update_period < 1:
        table.progress_bar_width = tsinse / table.update_period * 100
        table.progress_class = 'skill2-bar bg-danger'

    top_5_arzesh = sorted(mojodi, key=lambda x: x.arzesh, reverse=True)[:5]
    total_arzesh = sum([item.arzesh for item in top_5_arzesh if item.kala is not None])
    current_start = 0
    for item in top_5_arzesh:
        if item.kala is not None:
            item.start = current_start
            item.end = current_start + item.arzesh / total_arzesh
            current_start = item.end

    context = {
        'title': 'داشبورد کالاها',
        'mojodi': mojodi,
        'top_5_arzesh': top_5_arzesh,
    }

    response = render(request, 'dash_kala.html', context)  # نام قالب خود را به‌روز کنید

    total_time = time.time() - start_time
    print(f"زمان کل تابع DsshKala: {total_time:.2f} ثانیه")

    return response


# AJAX برای بارگذاری دسته‌بندی سطح 2
def load_categories_level2(request):
    category1_id = request.GET.get('category1_id')
    if category1_id:
        try:
            category1_id = int(category1_id)
            categories = Category.objects.filter(parent_id=category1_id, level=2).all()
        except ValueError:
            categories = Category.objects.none()
    else:
        categories = Category.objects.none()
    return render(request, 'partials/category_dropdown_list_options.html', {'categories': categories})


# AJAX برای بارگذاری دسته‌بندی سطح 3
def load_categories_level3(request):
    category2_id = request.GET.get('category2_id')
    if category2_id:
        try:
            category2_id = int(category2_id)
            categories = Category.objects.filter(parent_id=category2_id, level=3).all()
        except ValueError:
            categories = Category.objects.none()
    else:
        categories = Category.objects.none()
    return render(request, 'partials/category_dropdown_list_options.html', {'categories': categories})


@login_required(login_url='/login')
def TotalKala(request, *args, **kwargs):
    start_time = time.time()  # زمان شروع تابع
    user=request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(
            user=user,
            page='کل کالاها',
        )
    st = kwargs['st']
    cat1 = kwargs['cat1']
    cat2 = kwargs['cat2']
    cat3 = kwargs['cat3']
    tt = kwargs['total']
    kala_detail_form = Kala_Detail_Form(request.POST or None)
    if 'submit_form' in request.POST and request.POST['submit_form'] == 'kala_detail' and kala_detail_form.is_valid():
        try:
            code_kala = (kala_detail_form.cleaned_data.get('kala')).code
            return redirect(f'/dash/kala/detail/{code_kala}')
        except:
            try:
                code_kala = kala_detail_form.cleaned_data.get('code_kala')
                return redirect(f'/dash/kala/detail/{code_kala}')
            except:
                return redirect(f'/dash/kala/total/{st}/{cat1}/{cat2}/{cat3}/total')

    detailaddress = f'/dash/kala/total/{st}/{cat1}/{cat2}/{cat3}/detail'

    total = False if tt == 'total' else True

    # جستجو در مدل‌ها
    formst = Storagek.objects.filter(id=int(st)).last() if st != 'all' else None
    formcat1 = Category.objects.filter(id=int(cat1)).last() if cat1 != 'all' else None
    formcat2 = Category.objects.filter(id=int(cat2)).last() if cat2 != 'all' else None
    formcat3 = Category.objects.filter(id=int(cat3)).last() if cat3 != 'all' else None

    kala_select_form = KalaSelectForm(request.POST or None,
                                      # initial={
                                      #     'storage': formst,
                                      #     'category1': formcat1,
                                      #     'category2': formcat2,
                                      #     'category3': formcat3,
                                      # }
                                      )

    # واکنش به ارسال فرم
    def get_cleaned_data_or_default(form, field_name, default='all'):
        field_value = form.cleaned_data.get(field_name)
        return field_value.id if field_value else default

    if 'submit_form' in request.POST and request.POST['submit_form'] == 'kala_select' and kala_select_form.is_valid():
        storage = get_cleaned_data_or_default(kala_select_form, 'storage')
        category1 = get_cleaned_data_or_default(kala_select_form, 'category1')
        category2 = get_cleaned_data_or_default(kala_select_form, 'category2')
        category3 = get_cleaned_data_or_default(kala_select_form, 'category3')
        # ساخت آدرس جدید با پارامترهای فیلتر شده
        return redirect(f'/dash/kala/total/{storage}/{category1}/{category2}/{category3}/total')

    mojodi = Mojodi.objects.all()  # شروع با تمام رکوردها

    # فیلتر بر اساس انتخاب
    if formst and st != 'all':
        mojodi = mojodi.filter(storage__id=st)
    if formcat1 and cat1 != 'all':
        mojodi = mojodi.filter(kala__category__parent__parent__id=cat1)
    if formcat2 and cat2 != 'all':
        mojodi = mojodi.filter(kala__category__parent__id=cat2)
    if formcat3 and cat3 != 'all':
        mojodi = mojodi.filter(kala__category__id=cat3)

    table = Mtables.objects.filter(name='Kardex').last()
    tsinse = (timezone.now() - table.last_update_time).total_seconds() / 60

    if tsinse / table.update_period >= 1:
        table.progress_bar_width = 100
        table.progress_class = 'skill2-bar bg-danger'
    elif tsinse / table.update_period < 0.4:
        table.progress_class = 'skill2-bar bg-success'
        table.progress_bar_width = tsinse / table.update_period * 100
    elif tsinse / table.update_period < 0.9:
        table.progress_bar_width = tsinse / table.update_period * 100
        table.progress_class = 'skill2-bar bg-warning'
    elif tsinse / table.update_period < 1:
        table.progress_bar_width = tsinse / table.update_period * 100
        table.progress_class = 'skill2-bar bg-danger'

    # ساخت خلاصه کلی
    summary = {
        'storage': Storagek.objects.filter(id=int(st)).last().name if st != 'all' else 'همه انبار ها',
        'cat1': Category.objects.filter(id=int(cat1)).last().name if cat1 != 'all' else 'همه',
        'cat2': Category.objects.filter(id=int(cat2)).last().name if cat2 != 'all' else '',
        'cat3': Category.objects.filter(id=int(cat3)).last().name if cat3 != 'all' else '',
        'tedad': mojodi.values('kala').distinct().count(),
        'total_item_count': mojodi.aggregate(total_stock=Coalesce(Sum(F('stock'), output_field=FloatField()), 0.0))[
            'total_stock'],
        'total_value': mojodi.aggregate(total_arzesh=Coalesce(Sum(F('arzesh'), output_field=FloatField()), 0.0))[
            'total_arzesh'],
        'weighted_average_value': mojodi.aggregate(weighted_avg_value=Coalesce(
            Sum(F('stock') * F('averageprice'), output_field=FloatField()) / Coalesce(
                Sum(F('stock'), output_field=FloatField()), 1.0), 0.0))['weighted_avg_value'],
    }

    # ساخت خلاصه برای هر انبار در صورت انتخاب 'all'
    all_storage_summaries = []
    if st == 'all':
        storages = Storagek.objects.all()
    else:
        storages = Storagek.objects.filter(id=st)

    for storage in storages:
        storage_mojodi = mojodi.filter(storage=storage)
        storage_summary = {
            'storage': storage.name,
            'tedad': storage_mojodi.values('kala').distinct().count(),
            'total_item_count':
                storage_mojodi.aggregate(total_stock=Coalesce(Sum(F('stock'), output_field=FloatField()), 0.0))[
                    'total_stock'],
            'total_value':
                storage_mojodi.aggregate(total_arzesh=Coalesce(Sum(F('arzesh'), output_field=FloatField()), 0.0))[
                    'total_arzesh'],
            'weighted_average_value': storage_mojodi.aggregate(weighted_avg_value=Coalesce(
                Sum(F('stock') * F('averageprice'), output_field=FloatField()) / Coalesce(
                    Sum(F('stock'), output_field=FloatField()), 1.0), 0.0))['weighted_avg_value'],
        }
        if storage_mojodi.values('kala').distinct().count() > 0:
            all_storage_summaries.append(storage_summary)

    # ساخت خلاصه برای هر دسته‌بندی سطح ۳
    all_category_summaries_1 = []
    categories = Category.objects.filter(level=1)

    for category in categories:
        category_mojodi = mojodi.filter(kala__category__parent__parent=category)
        category_summary = {
            'category': category.name,
            'tedad': category_mojodi.values('kala').distinct().count(),
            'total_item_count':
                category_mojodi.aggregate(total_stock=Coalesce(Sum(F('stock'), output_field=FloatField()), 0.0))[
                    'total_stock'],
            'total_value':
                category_mojodi.aggregate(total_arzesh=Coalesce(Sum(F('arzesh'), output_field=FloatField()), 0.0))[
                    'total_arzesh'],
            'weighted_average_value': category_mojodi.aggregate(weighted_avg_value=Coalesce(
                Sum(F('stock') * F('averageprice'), output_field=FloatField()) / Coalesce(
                    Sum(F('stock'), output_field=FloatField()), 1.0), 0.0))['weighted_avg_value'],
        }
        if category_mojodi.values('kala').distinct().count() > 0:
            all_category_summaries_1.append(category_summary)

    all_category_summaries_2 = []
    categories = Category.objects.filter(level=2)

    for category in categories:
        category_mojodi = mojodi.filter(kala__category__parent=category)
        category_summary = {
            'category': category.name,
            'tedad': category_mojodi.values('kala').distinct().count(),
            'total_item_count':
                category_mojodi.aggregate(total_stock=Coalesce(Sum(F('stock'), output_field=FloatField()), 0.0))[
                    'total_stock'],
            'total_value':
                category_mojodi.aggregate(total_arzesh=Coalesce(Sum(F('arzesh'), output_field=FloatField()), 0.0))[
                    'total_arzesh'],
            'weighted_average_value': category_mojodi.aggregate(weighted_avg_value=Coalesce(
                Sum(F('stock') * F('averageprice'), output_field=FloatField()) / Coalesce(
                    Sum(F('stock'), output_field=FloatField()), 1.0), 0.0))['weighted_avg_value'],
        }
        if category_mojodi.values('kala').distinct().count() > 0:
            all_category_summaries_2.append(category_summary)

    all_category_summaries_3 = []
    categories = Category.objects.filter(level=3)

    for category in categories:
        category_mojodi = mojodi.filter(kala__category=category)
        category_summary = {
            'category': category.name,
            'tedad': category_mojodi.values('kala').distinct().count(),
            'total_item_count':
                category_mojodi.aggregate(total_stock=Coalesce(Sum(F('stock'), output_field=FloatField()), 0.0))[
                    'total_stock'],
            'total_value':
                category_mojodi.aggregate(total_arzesh=Coalesce(Sum(F('arzesh'), output_field=FloatField()), 0.0))[
                    'total_arzesh'],
            'weighted_average_value': category_mojodi.aggregate(weighted_avg_value=Coalesce(
                Sum(F('stock') * F('averageprice'), output_field=FloatField()) / Coalesce(
                    Sum(F('stock'), output_field=FloatField()), 1.0), 0.0))['weighted_avg_value'],
        }
        if category_mojodi.values('kala').distinct().count() > 0:
            all_category_summaries_3.append(category_summary)

    context = {
        'title': 'موجودی کالاها',
        'user':user,
        'mojodi': mojodi,  # جدول برای نمایش
        'kala_select_form': kala_select_form,  # فرم فیلترها
        'table': table,
        'summary': summary,
        'all_storage_summaries': all_storage_summaries,  # خلاصه برای هر انبار در صورت انتخاب 'all'
        'all_category_summaries_1': all_category_summaries_1,  # خلاصه برای هر دسته‌بندی سطح 1
        'all_category_summaries_2': all_category_summaries_2,  # خلاصه برای هر دسته‌بندی سطح 2
        'all_category_summaries_3': all_category_summaries_3,  # خلاصه برای هر دسته‌بندی سطح ۳
        'total': total,
        'detailaddress': detailaddress,
        'kala_detail_form': kala_detail_form,
    }

    total_time = time.time() - start_time
    print(f"زمان کل تابع TotalKala: {total_time:.2f} ثانیه")

    return render(request, 'total_kala.html', context)


import jdatetime
from datetime import datetime


def generate_calendar_data(month, year, kardex_data):
    # مشخص کردن اولین روز ماه
    first_day_of_month = jdatetime.date(year, month, 1)

    # روز شروع ماه (شنبه = 0, یکشنبه = 1, ...)
    start_day_of_week = first_day_of_month.weekday()

    # برای بدست آوردن آخرین روز ماه شمسی
    lday = first_day_of_month + jdatetime.timedelta(days=30)

    if lday.month != month:
        lday = first_day_of_month + jdatetime.timedelta(days=29)
        if lday.month != month:
            lday = first_day_of_month + jdatetime.timedelta(days=28)

    last_day_of_month = lday

    # تولید ماتریس روزهای ماه
    days_in_month = []

    week = [None] * start_day_of_week  # اضافه کردن روزهای خالی
    for i in range((last_day_of_month - first_day_of_month).days + 1):
        current_day = first_day_of_month + jdatetime.timedelta(days=i)
        sales = sum (item.count for item in kardex_data if item.date == current_day and item.ktype == 1) * -1
        kharid = sum(item.count for item in kardex_data if item.date == current_day and item.ktype==2 )
        day_info = {
            'jyear': current_day.year,
            'jmonth': current_day.month,
            'jday': current_day.day,
            'sales': sales,  # تعداد فروش
            'kharid': kharid  # تعداد خرید
        }
        week.append(day_info)
        if len(week) == 7 or current_day == last_day_of_month:
            days_in_month.append(week)
            week = []

    # اضافه کردن هفته‌ای که کمتر از 7 روز است
    if len(week) > 0:
        days_in_month.append(week + [None] * (7 - len(week)))

    return days_in_month

@login_required(login_url='/login')
def DetailKala1(request, *args, **kwargs):
    start_time = time.time()  # زمان شروع تابع

    # چاپ اطلاعات ورودی
    print('kwargscode')
    print(kwargs['code'])

    month = request.GET.get('month', None)
    year = request.GET.get('year', None)
    print("Query params - Year:", year, "Month:", month)

    code_kala = int(kwargs['code'])
    print('code')
    print(kwargs['code'])

    # دریافت ماه و سال جاری شمسی
    today_jalali = JalaliDate.today()
    print("Today Jalali:", today_jalali)

    # دریافت تاریخ شمسی امروز
    month = request.GET.get('month', None)
    year = request.GET.get('year', None)
    print("Request GET params - Year:", year, "Month:", month)

    if month is not None and year is not None:
        current_month = int(month)
        current_year = int(year)
    else:
        today_jalali = JalaliDate.today()
        current_year = today_jalali.year
        current_month = today_jalali.month

    print("Current Year:", current_year, "Current Month:", current_month)

    # تعریف بازه زمانی: 12 ماه گذشته تا ماه جاری
    month_list = []
    for i in range(12):
        month = current_month - i
        year = current_year
        if month < 1:
            month += 12
            year -= 1
        month_list.append((year, month))
    month_list.reverse()  # ترتیب به صورت قدیمی به جدید

    print("Month List:", month_list)

    # پردازش داده‌ها
    kardex_data = Kardex.objects.filter(code_kala=code_kala, ktype=1)
    print("Kardex Data Count:", kardex_data.count())

    chart1_data_dict = {}
    for item in kardex_data:
        pdate = item.pdate
        year, month, _ = map(int, pdate.split('/'))
        key = f"{year}/{month}"
        if key not in chart1_data_dict:
            chart1_data_dict[key] = 0
        chart1_data_dict[key] += item.count

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
        12: 'اسفند'
    }

    final_data = []
    for year, month in month_list:
        key = f"{year}/{month}"
        total_count = chart1_data_dict.get(key, 0)
        month_name = f"{month_names[month]}{str(year)[-2:]}"
        final_data.append({
            'year': year,
            'month': month,
            'month_name': month_name,
            'total_count': -total_count  # ضرب در منفی
        })

    print("Final Data:", final_data)

    # دریافت اطلاعات کالا
    kala = Kala.objects.filter(code=code_kala).last()
    kardex = Kardex.objects.filter(code_kala=code_kala).order_by('date', 'radif')
    mojodi = Mojodi.objects.filter(code_kala=code_kala)
    related_kalas = Kala.objects.filter(category=kala.category).order_by('-total_sale')

    rel_kala = []
    for k in related_kalas:
        rel_kala.append({
            'code': k.code,
            'name': k.name,
            'total_sale': k.total_sale,
            'mojodi_roz': k.total_sale / k.s_m_ratio if (k.s_m_ratio is not None and k.s_m_ratio != 0) else '0.00',
            's_m_ratio': f'{float(k.s_m_ratio):.2f}' if k.s_m_ratio is not None else '0.00',
        })

    today = date.today()

    # محاسبه تفاوت روزها با بررسی موجود بودن داده‌ها
    try:
        rosob = (today - Kardex.objects.filter(code_kala=code_kala, ktype=1).order_by('date',
                                                                                      'radif').last().date).days if Kardex.objects.filter(
            code_kala=code_kala, ktype=1).exists() else (
                today - Kardex.objects.filter(code_kala=code_kala).order_by('date', 'radif').first().date).days
    except:
        rosob = 0

    # بررسی موجودی کالا و تنظیم rosob
    last_mojodi = mojodi.last()
    if last_mojodi and last_mojodi.total_stock == 0:
        rosob = 0

    # محاسبه درصد rosob
    rosobper = rosob / 365 if rosob > 0 else 0

    # ایجاد لیست یکتا از s_m_ratio و پیدا کردن رتبه
    s_m_ratios = list(set(k.s_m_ratio for k in related_kalas))
    s_m_ratios.sort(reverse=True)  # مرتب‌سازی نزولی
    rank = s_m_ratios.index(kala.s_m_ratio) + 1 if kala.s_m_ratio in s_m_ratios else None
    rankper = (len(s_m_ratios) - rank) / (len(s_m_ratios) - 1) if len(s_m_ratios) > 1 else 1

    try:
        m_r_s = kala.total_sales() / mojodi.last().mojodi_roz * 100
    except:
        m_r_s = 0

    # current_year = 1403
    # current_month = 2
    months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    month_name = months[current_month - 1]

    kardex_data2 = Kardex.objects.filter(code_kala=code_kala)
    days_in_month = generate_calendar_data(current_month, current_year, kardex_data2)

    context = {
        'title': f'{kala.name}',
        'kala': kala,
        'kardex': kardex,
        'mojodi': mojodi,
        'rel_kala': rel_kala,
        'chart1_data': final_data,  # داده‌هایی که برای نمودار نیاز داریم
        'rosob': rosob,
        'rosobper': rosobper,
        'rank': rank,
        'rankper': rankper,
        'm_r_s': m_r_s,
        'days_in_month': days_in_month,
        'month_name': month_name,
        'year': current_year,
        'month': current_month,
        'code_kala': code_kala,
    }

    total_time = time.time() - start_time  # محاسبه زمان اجرا
    print(f"زمان کل اجرای تابع: {total_time:.2f} ثانیه")
    return render(request, 'detil_kala.html', context)


@login_required(login_url='/login')
def DetailKala(request, *args, **kwargs):
    user=request.user
    code_kala = int(kwargs['code'])
    if user.mobile_number != '09151006447':
        UserLog.objects.create(
            user=user,
            page='جزئیات کالا',
            code=code_kala,
        )
    start_time = time.time()  # زمان شروع تابع

    # چاپ اطلاعات ورودی
    print('kwargscode')
    print(kwargs['code'])

    month = request.GET.get('month', None)
    year = request.GET.get('year', None)
    print("Query params - Year:", year, "Month:", month)

    code_kala = int(kwargs['code'])
    print('code')
    print(kwargs['code'])

    # دریافت ماه و سال جاری شمسی
    today_jalali = JalaliDate.today()
    print("Today Jalali:", today_jalali)

    # دریافت تاریخ شمسی امروز
    month = request.GET.get('month', None)
    year = request.GET.get('year', None)
    print("Request GET params - Year:", year, "Month:", month)

    if month is not None and year is not None:
        current_month = int(month)
        current_year = int(year)
    else:
        today_jalali = JalaliDate.today()
        current_year = today_jalali.year
        current_month = today_jalali.month

    print("Current Year:", current_year, "Current Month:", current_month)

    # تعریف بازه زمانی: 12 ماه گذشته تا ماه جاری
    month_list = []
    for i in range(12):
        month = current_month - i
        year = current_year
        if month < 1:
            month += 12
            year -= 1
        month_list.append((year, month))
    month_list.reverse()  # ترتیب به صورت قدیمی به جدید

    print("Month List:", month_list)

    # پردازش داده‌ها
    kardex_data = Kardex.objects.filter(code_kala=code_kala, ktype=1)
    print("Kardex Data Count:", kardex_data.count())

    chart1_data_dict = {}
    for item in kardex_data:
        pdate = item.pdate
        year, month, _ = map(int, pdate.split('/'))
        key = f"{year}/{month}"
        if key not in chart1_data_dict:
            chart1_data_dict[key] = 0
        chart1_data_dict[key] += item.count

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
        12: 'اسفند'
    }

    final_data = []
    for year, month in month_list:
        key = f"{year}/{month}"
        total_count = chart1_data_dict.get(key, 0)
        month_name = f"{month_names[month]}{str(year)[-2:]}"
        final_data.append({
            'year': year,
            'month': month,
            'month_name': month_name,
            'total_count': -total_count  # ضرب در منفی
        })

    print("Final Data:", final_data)

    # دریافت اطلاعات کالا
    kala = Kala.objects.filter(code=code_kala).last()
    kardex = Kardex.objects.filter(code_kala=code_kala).order_by('date', 'radif')
    mojodi = Mojodi.objects.filter(code_kala=code_kala)
    related_kalas = Kala.objects.filter(category=kala.category).order_by('-total_sale')

    rel_kala = []
    for k in related_kalas:
        rel_kala.append({
            'code': k.code,
            'name': k.name,
            'total_sale': k.total_sale,
            'mojodi_roz': k.total_sale / k.s_m_ratio if (k.s_m_ratio is not None and k.s_m_ratio != 0) else '0.00',
            's_m_ratio': f'{float(k.s_m_ratio):.2f}' if k.s_m_ratio is not None else '0.00',
        })

    today = date.today()

    # محاسبه تفاوت روزها با بررسی موجود بودن داده‌ها
    try:
        rosob = (today - Kardex.objects.filter(code_kala=code_kala, ktype=1).order_by('date',
                                                                                      'radif').last().date).days if Kardex.objects.filter(
            code_kala=code_kala, ktype=1).exists() else (
                today - Kardex.objects.filter(code_kala=code_kala).order_by('date', 'radif').first().date).days
    except:
        rosob = 0

    # بررسی موجودی کالا و تنظیم rosob
    last_mojodi = mojodi.last()
    if last_mojodi and last_mojodi.total_stock == 0:
        rosob = 0

    # محاسبه درصد rosob
    rosobper = rosob / 365 if rosob > 0 else 0

    # ایجاد لیست یکتا از s_m_ratio و پیدا کردن رتبه
    s_m_ratios = list(set(k.s_m_ratio for k in related_kalas))
    s_m_ratios.sort(reverse=True)  # مرتب‌سازی نزولی
    rank = s_m_ratios.index(kala.s_m_ratio) + 1 if kala.s_m_ratio in s_m_ratios else None
    rankper = (len(s_m_ratios) - rank) / (len(s_m_ratios) - 1) if len(s_m_ratios) > 1 else 1

    try:
        m_r_s = kala.total_sale / mojodi.last().mojodi_roz * 100
    except:
        m_r_s = 0

    # current_year = 1403
    # current_month = 2
    months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    month_name = months[current_month - 1]

    kardex_data2 = Kardex.objects.filter(code_kala=code_kala)
    days_in_month = generate_calendar_data(current_month, current_year, kardex_data2)

    context = {
        'title': f'{kala.name}',
        'user': user,
        'kala': kala,
        'kardex': kardex,
        'mojodi': mojodi,
        'rel_kala': rel_kala,
        'chart1_data': final_data,  # داده‌هایی که برای نمودار نیاز داریم
        'rosob': rosob,
        'rosobper': rosobper,
        'rank': rank,
        'rankper': rankper,
        'm_r_s': m_r_s,
        'days_in_month': days_in_month,
        'month_name': month_name,
        'year': current_year,
        'month': current_month,
        'code_kala': code_kala,
    }

    total_time = time.time() - start_time  # محاسبه زمان اجرا
    print(f"زمان کل اجرای تابع: {total_time:.2f} ثانیه")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'partial_kala.html', context)
    return render(request, 'detil_kala.html', context)

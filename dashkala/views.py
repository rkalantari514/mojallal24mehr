from django.contrib.auth.decorators import login_required
from openpyxl.styles.builtins import title

from custom_login.models import UserLog
from custom_login.views import page_permision
from mahakupdate.models import Kardex, Mtables, Category, Mojodi, Storagek, Kala, SanadDetail, FactorDetaile
from persianutils import standardize
from django.db.models import Max, Subquery
from .forms import FilterForm, KalaSelectForm, Kala_Detail_Form
import time
from django.db.models import Sum, F, FloatField
from django.db.models.functions import Coalesce
from django.utils import timezone
from khayyam import JalaliDate, JalaliDatetime
from datetime import date
from django.shortcuts import render, redirect
import jdatetime

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
    name = 'موجودی کالاها'
    result = page_permision(request, name)  # بررسی دسترسی
    if result:  # اگر هدایت انجام شده است
        return result
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



def generate_calendar_data2(month, year, kardex_data):
    start_time = time.time()
    # مشخص کردن اولین روز ماه
    first_day_of_month = jdatetime.date(year, month, 1)

    # روز شروع ماه (شنبه = 0, یکشنبه = 1, ...)
    start_day_of_week = first_day_of_month.weekday()

    # برای بدست آوردن آخرین روز ماه شمسی
    lday = first_day_of_month + jdatetime.timedelta(days=30)
    print(f"5.10 {time.time() - start_time:.2f} ثانیه")
    start_time = time.time()
    if lday.month != month:
        lday = first_day_of_month + jdatetime.timedelta(days=29)
        if lday.month != month:
            lday = first_day_of_month + jdatetime.timedelta(days=28)

    last_day_of_month = lday
    print(f"5.11 {time.time() - start_time:.2f} ثانیه")
    start_time = time.time()
    # تولید ماتریس روزهای ماه
    days_in_month = []
    print(f"5.12 {time.time() - start_time:.2f} ثانیه")
    start_time = time.time()
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
    print(f"5.13 {time.time() - start_time:.2f} ثانیه")
    start_time = time.time()
    # اضافه کردن هفته‌ای که کمتر از 7 روز است
    if len(week) > 0:
        days_in_month.append(week + [None] * (7 - len(week)))
    print(f"5.14 {time.time() - start_time:.2f} ثانیه")
    return days_in_month

from django.db.models import Sum
from collections import defaultdict
import jdatetime
import time

def generate_calendar_data(month, year, kardex_queryset): # تغییر نام پارامتر برای وضوح
    aggregated_data = kardex_queryset.values('date', 'ktype').annotate(total_count=Sum('count'))
    daily_kardex_summary = defaultdict(lambda: defaultdict(float))
    for item in aggregated_data:
        if isinstance(item['date'], jdatetime.date):
            jdate = item['date']
        else: # فرض می‌کنیم datetime.date است
            jdate = jdatetime.date.fromgregorian(date=item['date'])

        daily_kardex_summary[jdate][item['ktype']] += item['total_count']
    first_day_of_month = jdatetime.date(year, month, 1)
    start_day_of_week = first_day_of_month.weekday()
    lday = first_day_of_month + jdatetime.timedelta(days=30)
    if lday.month != month:
        lday = first_day_of_month + jdatetime.timedelta(days=29)
        if lday.month != month:
            lday = first_day_of_month + jdatetime.timedelta(days=28)
    last_day_of_month = lday
    days_in_month = []
    week = [None] * start_day_of_week
    for i in range((last_day_of_month - first_day_of_month).days + 1):
        current_day = first_day_of_month + jdatetime.timedelta(days=i)
        sales_count = daily_kardex_summary[current_day][1]
        kharid_count = daily_kardex_summary[current_day][2]
        sales = sales_count * -1
        kharid = kharid_count
        day_info = {
            'jyear': current_day.year,
            'jmonth': current_day.month,
            'jday': current_day.day,
            'sales': sales,
            'kharid': kharid
        }
        week.append(day_info)
        if len(week) == 7 or current_day == last_day_of_month:
            days_in_month.append(week)
            week = []
    if len(week) > 0:
        days_in_month.append(week + [None] * (7 - len(week)))
    return days_in_month

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

    chart1_data = []
    for year, month in month_list:
        key = f"{year}/{month}"
        total_count = chart1_data_dict.get(key, 0)
        month_name = f"{month_names[month]}{str(year)[-2:]}"
        chart1_data.append({
            'year': year,
            'month': month,
            'month_name': month_name,
            'total_count': -total_count  # ضرب در منفی
        })

    print("Final Data:", chart1_data)

    # دریافت اطلاعات کالا
    kala = Kala.objects.filter(code=code_kala).last()
    kardex = Kardex.objects.filter(code_kala=code_kala).order_by('date', 'radif')
    mojodi = Mojodi.objects.filter(code_kala=code_kala)
    related_kalas = Kala.objects.filter(category=kala.category).order_by('-total_sale')

    # rel_kala = []
    # for k in related_kalas:
    #     rel_kala.append({
    #         'code': k.code,
    #         'name': k.name,
    #         'total_sale': k.total_sale,
    #         'mojodi_roz': k.total_sale / k.s_m_ratio if (k.s_m_ratio is not None and k.s_m_ratio != 0) else '0.00',
    #         's_m_ratio': f'{float(k.s_m_ratio):.2f}' if k.s_m_ratio is not None else '0.00',
    #     })

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

    kardex_data2 = Kardex.objects.filter(code_kala=code_kala,ktype__in=(1,2))
    days_in_month = generate_calendar_data(current_month, current_year, kardex_data2)

    context = {
        'title': f'{kala.name}',
        'user': user,
        'kala': kala,
        'kardex': kardex,
        'mojodi': mojodi,
        # 'rel_kala': rel_kala,
        'chart1_data': chart1_data,  # داده‌هایی که برای نمودار نیاز داریم
        'rosob': rosob,
        'rosobper': rosobper,
        'rank': rank,
        'rankper': rankper,
        # 'm_r_s': m_r_s,
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
    return render(request, 'detail_kala.html', context)

from decimal import Decimal, InvalidOperation
from collections import defaultdict
from django.db.models import Sum, Avg
import time
import jdatetime
import time
from collections import defaultdict
from django.db.models import Sum, Avg
from decimal import Decimal
import time
from collections import defaultdict
from django.db.models import Sum, Func, F
from decimal import Decimal, InvalidOperation
@login_required(login_url='/login')
def CategoryDetail(request, *args, **kwargs):
    name = 'دسته بندی کالاها'
    result = page_permision(request, name)  # بررسی دسترسی
    if result:  # اگر هدایت انجام شده است
        return result
    start_time2 = time.time()  # زمان شروع تابع
    start_time = time.time()  # زمان شروع تابع
    user=request.user

    cat_id=int(kwargs['id'])
    if cat_id==0:
        cat='همه دسته بندی ها'
        cat_level=0
    else:
        cat=Category.objects.filter(id=cat_id).last()
        cat_level = cat.level

    if user.mobile_number != '09151006447':
        UserLog.objects.create(
            user=user,
            page='جزئیات دسته بندی',
            code=cat_id,
        )


    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        name = 'دسته بندی کالاها'
        result = page_permision(request, name)  # بررسی دسترسی
        if result:  # اگر هدایت انجام شده است
            return result
        start_time2 = time.time()  # زمان شروع تابع
        user = request.user

        cat_id = int(kwargs['id'])
        if cat_id == 0:
            cat_level = 0
        else:
            cat = Category.objects.filter(id=cat_id).last()
            cat_level = cat.level

        if user.mobile_number != '09151006447':
            UserLog.objects.create(
                user=user,
                page='جزئیات دسته بندی',
                code=cat_id,
            )

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
        if cat_level == 3:
            kardex_data2 = Kardex.objects.filter(kala__category=cat, ktype__in=(1, 2))
        if cat_level == 2:
            kardex_data2 = Kardex.objects.filter(kala__category__parent=cat, ktype__in=(1, 2))
        if cat_level == 1:
            kardex_data2 = Kardex.objects.filter(kala__category__parent__parent=cat, ktype__in=(1, 2))
        if cat_level == 0:
            kardex_data2 = Kardex.objects.filter(ktype__in=(1, 2))
        days_in_month = generate_calendar_data(current_month, current_year, kardex_data2)

        context = {
            'month': current_month,
            'cat_id': f'{cat.id}',
            'days_in_month': days_in_month,
            'month_name': month_name,
            'year': current_year,
        }

        total_time = time.time() - start_time2  # محاسبه زمان اجرا
        print(f"زمان کل اجرای تابع: {total_time:.2f} ثانیه")

        return render(request, 'partial_category.html', context)

#------------------------------------------------------------------------------------------
    print(f"stage 10: {time.time() - start_time:.2f} ثانیه")
    start_time = time.time()

    month = request.GET.get('month', None)
    year = request.GET.get('year', None)
    print("Query params - Year:", year, "Month:", month)

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
    month_list = []
    for i in range(12):
        month = current_month - i
        year = current_year
        if month < 1:
            month += 12
            year -= 1
        month_list.append((year, month))
    month_list.reverse()  # ترتیب به صورت قدیمی به جدید
    cat1 = Category.objects.filter(level=1).order_by('id')
    print(f"stage 20: {time.time() - start_time:.2f} ثانیه")
    start_time = time.time()
    if cat_level == 3:
        kalas = Kala.objects.filter(category=cat)
        kardex = Kardex.objects.filter(kala__category=cat,ktype__in=(1,2)).order_by('date', 'radif')
        kardex_data2 = Kardex.objects.filter(kala__category=cat,ktype__in=(1,2))
        print('cat_level==3')
        par2=cat.parent
        par1=par2.parent
        cat2=Category.objects.filter(parent=par1)
        cat3=Category.objects.filter(parent=par2)
        distinct_kalas = Mojodi.objects.filter(kala__category=cat).values('kala').distinct()

    if cat_level==2:
        kalas = Kala.objects.filter(category__parent=cat)
        kardex = Kardex.objects.filter(kala__category__parent=cat,ktype__in=(1,2)).order_by('date', 'radif')
        kardex_data2 = Kardex.objects.filter(kala__category__parent=cat,ktype__in=(1,2))
        print('cat_level==2')
        par1=cat.parent
        par2=cat
        cat2=Category.objects.filter(parent=par1)
        cat3=Category.objects.filter(parent=cat)
        distinct_kalas = Mojodi.objects.filter(kala__category__parent=cat).values('kala').distinct()

    if cat_level==1:
        kalas = Kala.objects.filter(category__parent__parent=cat)
        kardex = Kardex.objects.filter(kala__category__parent__parent=cat,ktype__in=(1,2)).order_by('date', 'radif')
        kardex_data2 = Kardex.objects.filter(kala__category__parent__parent=cat,ktype__in=(1,2))
        print('cat_level==1')
        par1=cat
        par2=None
        cat2=Category.objects.filter(parent=cat)
        # cat3=Category.objects.filter(parent__parent=cat)
        cat3=None
        distinct_kalas = Mojodi.objects.filter(kala__category__parent__parent=cat).values('kala').distinct()

    if cat_level==0:
        kalas = Kala.objects.all()
        kardex = Kardex.objects.filter(ktype__in=(1,2)).order_by('date', 'radif')
        kardex_data2 = Kardex.objects.filter(ktype__in=(1,2))
        print('cat_level==0')
        par1=None
        par2=None
        cat2=None
        # cat3=Category.objects.filter(parent__parent=cat)
        cat3=None
        distinct_kalas = Mojodi.objects.values('kala').distinct()


    print(f"stage 30: {time.time() - start_time:.2f} ثانیه")
    start_time = time.time()
# چارت اول:-------------------------------------------------------------- فروش ماهانه تعداد



    start_time = time.time()

    # مرحله ۱: گرفتن لیست کاله‌های مرتبط
    taf_list = list(kalas.values_list('kala_taf', flat=True).distinct())
    print(f"stage 31: {time.time() - start_time:.2f} ثانیه")
    start_time = time.time()

    # مرحله ۲: فیلتر کردن فاکتورها بر اساس لیست کاله‌ها، با استفاده از کوئری‌های گروهی
    fac = FactorDetaile.objects.filter(kala__kala_taf__in=taf_list)
    print(f"stage 32: {time.time() - start_time:.2f} ثانیه")
    start_time = time.time()

    # ساختن نام ماه‌های جلالی
    month_names_jalali = {
        1: 'فروردین', 2: 'اردیبهشت', 3: 'خرداد', 4: 'تیر',
        5: 'مرداد', 6: 'شهریور', 7: 'مهر', 8: 'آبان',
        9: 'آذر', 10: 'دی', 11: 'بهمن', 12: 'اسفند'
    }

    # مرحله ۳: جمع‌آوری تعداد فروش بر اساس تاریخ (جمع‌آوری سریع‌تر با کوئری‌ گروهی)
    sales_stats_count = fac.annotate(
        year=Func(F('factor__pdate'), function='SUBSTRING', template="SUBSTRING(%(expressions)s, 1, 4)"),
        month=Func(F('factor__pdate'), function='SUBSTRING', template="SUBSTRING(%(expressions)s, 6, 2)")
    ).values('year', 'month').annotate(total=Sum('count'))

    sales_by_year_month_count = defaultdict(lambda: defaultdict(int))
    for item in sales_stats_count:
        try:
            year = int(item['year'])
            month = int(item['month'])
            sales_by_year_month_count[year][month] += item['total']
        except (ValueError, KeyError, TypeError):
            continue
    print(f"stage 34: {time.time() - start_time:.2f} ثانیه")
    start_time = time.time()

    # لیست سال‌ها برای رسم نمودار
    all_years = sorted(sales_by_year_month_count.keys())

    # تهیه لیبل‌های ماه‌های جلالی
    chart1_labels = list(month_names_jalali.values())

    # ساخت داده‌های مربوط به فروش تعداد در هر سال و ماه‌ها
    chart1_datasets = []
    for year in all_years:
        data_for_year = []
        for month_num in range(1, 13):
            data_for_year.append(sales_by_year_month_count[year][month_num])
        chart1_datasets.append({
            'label': f'فروش {year}',
            'data': data_for_year,
            'borderWidth': 1,
            'categoryPercentage': 0.8,
            'barPercentage': 0.9
        })

        # مرحله ۴: جمع‌آوری مبلغ فروش بر اساس تاریخ (کوتاه و سریع‌تر با کوئری گروهی)
    sales_stats_amount = fac.annotate(
        year=Func(F('factor__pdate'), function='SUBSTRING', template="SUBSTRING(%(expressions)s, 1, 4)"),
        month=Func(F('factor__pdate'), function='SUBSTRING', template="SUBSTRING(%(expressions)s, 6, 2)")
    ).values('year', 'month').annotate(total_amount=Sum('mablagh_nahaee'))

    sales_by_year_month_amount = defaultdict(lambda: defaultdict(lambda: Decimal('0')))
    for item in sales_stats_amount:
        try:
            year = int(item['year'])
            month = int(item['month'])
            amount = Decimal(str(item['total_amount'])) if item['total_amount'] is not None else Decimal('0')
            sales_by_year_month_amount[year][month] += amount / 10000000000
        except (InvalidOperation, ValueError, KeyError, TypeError):
            continue
    print(f"stage 42: {time.time() - start_time:.2f} ثانیه")
    start_time = time.time()

    # تهیه لیست سال‌های موجود برای نمودار مبلغ فروش
    # تهیه لیست سال‌های موجود برای نمودار مبلغ فروش
    all_years_amount = sorted(sales_by_year_month_amount.keys())

    # ساخت داده‌های مربوط به مبلغ فروش در هر سال و ماه‌ها
    chart2_labels = list(month_names_jalali.values())

    chart2_datasets = []
    for year in all_years_amount:
        data_for_year = []
        for month_num in range(1, 13):
            data_for_year.append(sales_by_year_month_amount[year][month_num])
        chart2_datasets.append({
            'label': f'فروش {year}',
            'data': data_for_year,
            'borderWidth': 1,
            'categoryPercentage': 0.8,
            'barPercentage': 0.9
        })





    #----------------------------------------------------------------------------- دریافت اطلاعات کالا
    print(f"stage 50: {time.time() - start_time:.2f} ثانیه")
    start_time = time.time()

    months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    month_name = months[current_month - 1]

    days_in_month = generate_calendar_data(current_month, current_year, kardex_data2)

    # ابتدا شناسه‌های کالای مورد نیاز را استخراج می‌کنیم
    kala_ids = [item['kala'] for item in distinct_kalas]

    mojodi_queryset = Mojodi.objects.filter(kala__in=kala_ids)

    mojodi_data = mojodi_queryset.values('kala').annotate(
        total_stock=Sum('total_stock'),
        average_price=Avg('averageprice'),
        mojodi_roz=Sum('mojodi_roz'),
        mojodi_roz_arzesh=Sum('mojodi_roz_arzesh')
    )
    print(f"stage 60: {time.time() - start_time:.2f} ثانیه")
    start_time = time.time()

    totl_mojodi = sum([item['total_stock'] or 0 for item in mojodi_data])

    total_arzesh = sum(
        (item['total_stock'] or 0) * (item['average_price'] or 0) for item in mojodi_data
    )
    try:
        total_sale = kardex.filter(ktype=1).aggregate(total_count=Sum('count'))['total_count'] * -1
    except:
        total_sale=0
    kala_ids = [item['kala'] for item in distinct_kalas]
    mojodi_qs = Mojodi.objects.filter(kala__in=kala_ids)
    mojodi_data = mojodi_qs.values('kala').annotate(
        mojodi_roz=Sum('mojodi_roz'),
        mojodi_roz_arzesh=Sum('mojodi_roz_arzesh')
    )
    mojodi_dict = {item['kala']: item for item in mojodi_data}
    mojodi_roz = sum([mojodi_dict.get(kala, {}).get('mojodi_roz', 0) for kala in kala_ids])
    mojodi_roz_arzesh = sum([mojodi_dict.get(kala, {}).get('mojodi_roz_arzesh', 0) for kala in kala_ids])
    s_m_ratio = total_sale / mojodi_roz * 100 if mojodi_roz != 0 else 0
    master_data = {
        'totl_mojodi': totl_mojodi,
        'total_arzesh': total_arzesh,
        'total_sale': total_sale,
        's_m_ratio': s_m_ratio,
        'mojodi_roz': mojodi_roz,
        'mojodi_roz_arzesh': mojodi_roz_arzesh,
    }
    print(f"stage 70: {time.time() - start_time:.2f} ثانیه")
    start_time = time.time()

    donat_forosh_data=[]
    donat_forosh_mablagh=[]
    if cat_level==0:
        for category in cat1:
            kalas_cat = Kala.objects.filter(category__parent__parent=category)
            taf_list_cat = list(kalas_cat.values_list('kala_taf', flat=True).distinct())
            fac_cat = FactorDetaile.objects.filter(kala__kala_taf__in=taf_list_cat)
            total_sale = fac_cat.aggregate(total_count=Sum('count'))['total_count'] or 0
            total_sale_mab = fac_cat.aggregate(total_count=Sum('mablagh_nahaee'))['total_count'] or 0
            donat_forosh_mablagh.append({
                'name': category.name,
                'count': total_sale_mab
            })
            donat_forosh_data.append({
                'name': category.name,
                'count': total_sale
            })


    if cat_level == 1:
        # برای هر دسته در سطح 2
        for category in cat2:
            # گرفتن کاله‌های زیرمجموعه دسته
            kalas_cat = Kala.objects.filter(category__parent=category)
            # استخراج کدهای تاف کاله‌ها در لیست
            taf_list_cat = list(kalas_cat.values_list('kala_taf', flat=True).distinct())
            # فیلتر فاکتورها بر اساس کاله‌های تاف
            fac_cat = FactorDetaile.objects.filter(kala__kala_taf__in=taf_list_cat)
            # جمع کردن تعداد فروش و مبلغ فروش
            total_sale = fac_cat.aggregate(total=Sum('count'))['total'] or 0
            total_sale_mab = fac_cat.aggregate(total=Sum('mablagh_nahaee'))['total'] or 0
            # افزودن به لیست‌ها
            donat_forosh_mablagh.append({
                'name': category.name,
                'count': total_sale_mab
            })
            donat_forosh_data.append({
                'name': category.name,
                'count': total_sale
            })

    elif cat_level == 2:
        # برای هر دسته در سطح 3
        for category in cat3:
            kalas_cat = Kala.objects.filter(category=category)
            taf_list_cat = list(kalas_cat.values_list('kala_taf', flat=True).distinct())
            fac_cat = FactorDetaile.objects.filter(kala__kala_taf__in=taf_list_cat)
            total_sale = fac_cat.aggregate(total=Sum('count'))['total'] or 0
            total_sale_mab = fac_cat.aggregate(total=Sum('mablagh_nahaee'))['total'] or 0
            donat_forosh_mablagh.append({
                'name': category.name,
                'count': total_sale_mab
            })
            donat_forosh_data.append({
                'name': category.name,
                'count': total_sale
            })

    elif cat_level == 3:
        # برای سطح دسته‌بندی خودش
        kalas_cat = Kala.objects.filter(category=cat)
        for kal in kalas_cat:
            fac_cat = FactorDetaile.objects.filter(kala=kal)
            total_sale = fac_cat.aggregate(total=Sum('count'))['total'] or 0
            total_sale_mab = fac_cat.aggregate(total=Sum('mablagh_nahaee'))['total'] or 0
            donat_forosh_mablagh.append({
                'name': kal.name,
                'count': total_sale_mab
            })
            donat_forosh_data.append({
                'name': kal.name,
                'count': total_sale
            })

    if cat_level==0:
        cat_id_1='0'
    else:
        cat_id_1=f'{cat.id}'
    print(f"stage 90: {time.time() - start_time:.2f} ثانیه")
    start_time = time.time()

    context = {
        'title': f'{cat}',
        'cat_id': cat_id_1,
        'cat_level': cat_level,
        'user': user,
        'cat': cat,
        'cat1': cat1,
        'cat2': cat2,
        'cat3': cat3,
        'par1': par1,
        'par2': par2,
        'master_data':master_data,
        'donat_forosh_data': donat_forosh_data,
        'donat_forosh_mablagh': donat_forosh_mablagh,
        'days_in_month': days_in_month,
        'month_name': month_name,
        'year': current_year,
        'month': current_month,
        'kalas': kalas,
        'chart1_labels': chart1_labels,
        'chart1_datasets': chart1_datasets,
        'chart2_labels': chart2_labels,
        'chart2_datasets': chart2_datasets,
    }

    total_time = time.time() - start_time2  # محاسبه زمان اجرا
    print(f"زمان کل اجرای تابع: {total_time:.2f} ثانیه")
    return render(request, 'category_detail.html', context)






def CategoryDetail1(request, *args, **kwargs):
    name = 'دسته بندی کالاها'
    result = page_permision(request, name)  # بررسی دسترسی
    if result:  # اگر هدایت انجام شده است
        return result
    start_time2 = time.time()  # زمان شروع تابع
    user=request.user

    cat_id=int(kwargs['id'])
    if cat_id==0:
        cat='همه دسته بندی ها'
        cat_level=0
    else:
        cat=Category.objects.filter(id=cat_id).last()
        cat_level = cat.level

    if user.mobile_number != '09151006447':
        UserLog.objects.create(
            user=user,
            page='جزئیات دسته بندی',
            code=cat_id,
        )


    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        name = 'دسته بندی کالاها'
        result = page_permision(request, name)  # بررسی دسترسی
        if result:  # اگر هدایت انجام شده است
            return result
        start_time2 = time.time()  # زمان شروع تابع
        user = request.user

        cat_id = int(kwargs['id'])
        if cat_id == 0:
            cat_level = 0
        else:
            cat = Category.objects.filter(id=cat_id).last()
            cat_level = cat.level

        if user.mobile_number != '09151006447':
            UserLog.objects.create(
                user=user,
                page='جزئیات دسته بندی',
                code=cat_id,
            )

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
        if cat_level == 3:
            kardex_data2 = Kardex.objects.filter(kala__category=cat, ktype__in=(1, 2))
        if cat_level == 2:
            kardex_data2 = Kardex.objects.filter(kala__category__parent=cat, ktype__in=(1, 2))
        if cat_level == 1:
            kardex_data2 = Kardex.objects.filter(kala__category__parent__parent=cat, ktype__in=(1, 2))
        if cat_level == 0:
            kardex_data2 = Kardex.objects.filter(ktype__in=(1, 2))
        days_in_month = generate_calendar_data(current_month, current_year, kardex_data2)

        context = {
            'month': current_month,
            'cat_id': f'{cat.id}',
            'days_in_month': days_in_month,
            'month_name': month_name,
            'year': current_year,
        }

        total_time = time.time() - start_time2  # محاسبه زمان اجرا
        print(f"زمان کل اجرای تابع: {total_time:.2f} ثانیه")

        return render(request, 'partial_category.html', context)

#------------------------------------------------------------------------------------------
    month = request.GET.get('month', None)
    year = request.GET.get('year', None)
    print("Query params - Year:", year, "Month:", month)

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
    month_list = []
    for i in range(12):
        month = current_month - i
        year = current_year
        if month < 1:
            month += 12
            year -= 1
        month_list.append((year, month))
    month_list.reverse()  # ترتیب به صورت قدیمی به جدید

    if cat_level == 3:
        kalas = Kala.objects.filter(category=cat)
        kardex = Kardex.objects.filter(kala__category=cat,ktype__in=(1,2)).order_by('date', 'radif')

    if cat_level==2:
        kalas = Kala.objects.filter(category__parent=cat)
        kardex = Kardex.objects.filter(kala__category__parent=cat,ktype__in=(1,2)).order_by('date', 'radif')

    if cat_level==1:
        kalas = Kala.objects.filter(category__parent__parent=cat)
        kardex = Kardex.objects.filter(kala__category__parent__parent=cat,ktype__in=(1,2)).order_by('date', 'radif')

    if cat_level==0:
        kalas = Kala.objects.all()
        kardex = Kardex.objects.filter(ktype__in=(1,2)).order_by('date', 'radif')

    if cat_level == 3:
        kalas = Kala.objects.filter(category=cat)
        kardex = Kardex.objects.filter(kala__category=cat,ktype__in=(1,2)).order_by('date', 'radif')

    if cat_level==2:
        kalas = Kala.objects.filter(category__parent=cat)
        kardex = Kardex.objects.filter(kala__category__parent=cat,ktype__in=(1,2)).order_by('date', 'radif')

    if cat_level==1:
        kalas = Kala.objects.filter(category__parent__parent=cat)
        kardex = Kardex.objects.filter(kala__category__parent__parent=cat,ktype__in=(1,2)).order_by('date', 'radif')

    if cat_level==0:
        kalas = Kala.objects.all()
        kardex = Kardex.objects.filter(ktype__in=(1,2)).order_by('date', 'radif')


    if cat_level == 3:
        kardex_data2 = Kardex.objects.filter(kala__category=cat,ktype__in=(1,2))
    if cat_level == 2:
        kardex_data2 = Kardex.objects.filter(kala__category__parent=cat,ktype__in=(1,2))
    if cat_level == 1:
        kardex_data2 = Kardex.objects.filter(kala__category__parent__parent=cat,ktype__in=(1,2))
    if cat_level == 0:
        kardex_data2 = Kardex.objects.filter(ktype__in=(1,2))

    cat1 = Category.objects.filter(level=1).order_by('id')
    if cat_level==0:
        print('cat_level==0')
        par1=None
        par2=None
        cat2=None
        # cat3=Category.objects.filter(parent__parent=cat)
        cat3=None
        distinct_kalas = Mojodi.objects.values('kala').distinct()


    elif cat_level==1:
        print('cat_level==1')
        par1=cat
        par2=None
        cat2=Category.objects.filter(parent=cat)
        # cat3=Category.objects.filter(parent__parent=cat)
        cat3=None
        distinct_kalas = Mojodi.objects.filter(kala__category__parent__parent=cat).values('kala').distinct()
    elif cat_level==2:
        print('cat_level==2')
        par1=cat.parent
        par2=cat
        cat2=Category.objects.filter(parent=par1)
        cat3=Category.objects.filter(parent=cat)
        distinct_kalas = Mojodi.objects.filter(kala__category__parent=cat).values('kala').distinct()
    elif cat_level==3:
        print('cat_level==3')
        par2=cat.parent
        par1=par2.parent
        cat2=Category.objects.filter(parent=par1)
        cat3=Category.objects.filter(parent=par2)
        distinct_kalas = Mojodi.objects.filter(kala__category=cat).values('kala').distinct()


# چارت اول:-------------------------------------------------------------- فروش ماهانه تعداد

    taf_list = list(kalas.values_list('kala_taf', flat=True).distinct())
    fac=FactorDetaile.objects.filter(kala__kala_taf__in=taf_list)

    month_names_jalali = {
        1: 'فروردین', 2: 'اردیبهشت', 3: 'خرداد', 4: 'تیر',
        5: 'مرداد', 6: 'شهریور', 7: 'مهر', 8: 'آبان',
        9: 'آذر', 10: 'دی', 11: 'بهمن', 12: 'اسفند'
    }

    from collections import defaultdict

    sales_by_year_month_count = defaultdict(lambda: defaultdict(lambda: 0))

    for item in fac:
        try:
            # بررسی اگر factor وجود دارد
            if not hasattr(item, 'factor') or item.factor is None:
                continue
            pdate = item.factor.pdate
            year, month, _ = map(int, pdate.split('/'))
            sales_by_year_month_count[year][month] += item.count
        except (ValueError, AttributeError):
            pass
    all_years = sorted(sales_by_year_month_count.keys())

    chart1_labels = list(month_names_jalali.values())

    chart1_datasets = []
    for year in all_years:
        data_for_year = []
        for month_num in range(1, 13):
            data_for_year.append(sales_by_year_month_count[year][month_num])
        chart1_datasets.append({
            'label': f'فروش {year}',
            'data': data_for_year,
            'borderWidth': 1,
            'categoryPercentage': 0.8,
            'barPercentage': 0.9
        })

    # چارت دوم: مبلغ فروش ----------------------------------------------------------------------



    sales_by_year_month_amount = defaultdict(lambda: defaultdict(lambda: Decimal('0')))

    for item in fac:
        try:
            tarikh = item.factor.pdate

            year, month, _ = map(int, tarikh.split('/'))
            # بررسی و تبدیل مقدار مبلغ، با مدیریت خطا
            try:
                amount = Decimal(str(item.mablagh_nahaee))
            except (InvalidOperation, ValueError, TypeError):
                amount = Decimal('0')
            sales_by_year_month_amount[year][month] += amount/10000000000
        except (ValueError, KeyError, AttributeError):
            pass


    all_years_amount = sorted(sales_by_year_month_amount.keys())

    chart2_labels = list(month_names_jalali.values())

    chart2_datasets = []
    for year in all_years_amount:
        data_for_year = []
        for month_num in range(1, 13):
            data_for_year.append(sales_by_year_month_amount[year][month_num])
        chart2_datasets.append({
            'label': f'فروش {year}',
            'data': data_for_year,
            'borderWidth': 1,
            'categoryPercentage': 0.8,
            'barPercentage': 0.9
        })

    #----------------------------------------------------------------------------- دریافت اطلاعات کالا

    months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
    month_name = months[current_month - 1]

    days_in_month = generate_calendar_data(current_month, current_year, kardex_data2)

    # ابتدا شناسه‌های کالای مورد نیاز را استخراج می‌کنیم
    kala_ids = [item['kala'] for item in distinct_kalas]

    mojodi_queryset = Mojodi.objects.filter(kala__in=kala_ids)

    mojodi_data = mojodi_queryset.values('kala').annotate(
        total_stock=Sum('total_stock'),
        average_price=Avg('averageprice'),
        mojodi_roz=Sum('mojodi_roz'),
        mojodi_roz_arzesh=Sum('mojodi_roz_arzesh')
    )

    totl_mojodi = sum([item['total_stock'] or 0 for item in mojodi_data])

    total_arzesh = sum(
        (item['total_stock'] or 0) * (item['average_price'] or 0) for item in mojodi_data
    )
    try:
        total_sale = kardex.filter(ktype=1).aggregate(total_count=Sum('count'))['total_count'] * -1
    except:
        total_sale=0
    kala_ids = [item['kala'] for item in distinct_kalas]
    mojodi_qs = Mojodi.objects.filter(kala__in=kala_ids)
    mojodi_data = mojodi_qs.values('kala').annotate(
        mojodi_roz=Sum('mojodi_roz'),
        mojodi_roz_arzesh=Sum('mojodi_roz_arzesh')
    )
    mojodi_dict = {item['kala']: item for item in mojodi_data}
    mojodi_roz = sum([mojodi_dict.get(kala, {}).get('mojodi_roz', 0) for kala in kala_ids])
    mojodi_roz_arzesh = sum([mojodi_dict.get(kala, {}).get('mojodi_roz_arzesh', 0) for kala in kala_ids])
    s_m_ratio = total_sale / mojodi_roz * 100 if mojodi_roz != 0 else 0
    master_data = {
        'totl_mojodi': totl_mojodi,
        'total_arzesh': total_arzesh,
        'total_sale': total_sale,
        's_m_ratio': s_m_ratio,
        'mojodi_roz': mojodi_roz,
        'mojodi_roz_arzesh': mojodi_roz_arzesh,
    }
    donat_forosh_data=[]
    donat_forosh_mablagh=[]
    if cat_level==0:
        for category in cat1:
            kalas_cat = Kala.objects.filter(category__parent__parent=category)
            taf_list_cat = list(kalas_cat.values_list('kala_taf', flat=True).distinct())
            fac_cat = FactorDetaile.objects.filter(kala__kala_taf__in=taf_list_cat)
            total_sale = fac_cat.aggregate(total_count=Sum('count'))['total_count'] or 0
            total_sale_mab = fac_cat.aggregate(total_count=Sum('mablagh_nahaee'))['total_count'] or 0
            donat_forosh_mablagh.append({
                'name': category.name,
                'count': total_sale_mab
            })
            donat_forosh_data.append({
                'name': category.name,
                'count': total_sale
            })

    if cat_level==1:
        for category in cat2:
            kalas_cat = Kala.objects.filter(category__parent=category)
            taf_list_cat = list(kalas_cat.values_list('kala_taf', flat=True).distinct())
            fac_cat = FactorDetaile.objects.filter(kala__kala_taf__in=taf_list_cat)
            total_sale = fac_cat.aggregate(total_count=Sum('count'))['total_count'] or 0
            total_sale_mab = fac_cat.aggregate(total_count=Sum('mablagh_nahaee'))['total_count'] or 0
            donat_forosh_mablagh.append({
                'name': category.name,
                'count': total_sale_mab
            })
            donat_forosh_data.append({
                'name': category.name,
                'count': total_sale
            })

    if cat_level==2:
        for category in cat3:
            kalas_cat = Kala.objects.filter(category=category)
            taf_list_cat = list(kalas_cat.values_list('kala_taf', flat=True).distinct())
            fac_cat = FactorDetaile.objects.filter(kala__kala_taf__in=taf_list_cat)
            total_sale = fac_cat.aggregate(total_count=Sum('count'))['total_count'] or 0
            total_sale_mab = fac_cat.aggregate(total_count=Sum('mablagh_nahaee'))['total_count'] or 0
            donat_forosh_mablagh.append({
                'name': category.name,
                'count': total_sale_mab
            })
            donat_forosh_data.append({
                'name': category.name,
                'count': total_sale
            })

    if cat_level==3:
        kalas_cat = Kala.objects.filter(category=cat)
        for kal in kalas_cat:
            fac_cat = FactorDetaile.objects.filter(kala=kal)
            total_sale = fac_cat.aggregate(total_count=Sum('count'))['total_count'] or 0
            total_sale_mab = fac_cat.aggregate(total_count=Sum('mablagh_nahaee'))['total_count'] or 0
            donat_forosh_mablagh.append({
                'name': category.name,
                'count': total_sale_mab
            })

            donat_forosh_data.append({
                'name': kal.name,
                'count': total_sale
            })

    if cat_level==0:
        cat_id_1='0'
    else:
        cat_id_1=f'{cat.id}'


    context = {
        'title': f'{cat}',
        'cat_id': cat_id_1,
        'cat_level': cat_level,
        'user': user,
        'cat': cat,
        'cat1': cat1,
        'cat2': cat2,
        'cat3': cat3,
        'par1': par1,
        'par2': par2,
        'master_data':master_data,
        'donat_forosh_data': donat_forosh_data,
        'donat_forosh_mablagh': donat_forosh_mablagh,
        'days_in_month': days_in_month,
        'month_name': month_name,
        'year': current_year,
        'month': current_month,
        'kalas': kalas,

        'chart1_labels': chart1_labels,
        'chart1_datasets': chart1_datasets,

        'chart2_labels': chart2_labels,
        'chart2_datasets': chart2_datasets,



    }

    total_time = time.time() - start_time2  # محاسبه زمان اجرا
    print(f"زمان کل اجرای تابع: {total_time:.2f} ثانیه")
    return render(request, 'category_detail.html', context)

from django.db.models import Q


@login_required(login_url='/login')
def CategorySale(request, *args, **kwargs):
    total = kwargs['total']
    if total == 'total':
        cat_id='all'
    else:
        cat_id = int(kwargs['id'])
    since = kwargs['since']
    to = kwargs['to']
    name = 'گزارش فروش کالا'
    result = page_permision(request, name)  # بررسی دسترسی
    if result:  # اگر هدایت انجام شده است
        return result
    start_time = time.time()  # زمان شروع تابع
    user=request.user


    if user.mobile_number != '09151006447':
        UserLog.objects.create(
            user=user,
            page='جزئیات دسته بندی',
            code=cat_id,
        )

    st_with = ['کالا در فاکتور فروش', 'کالاهاي برگشت شده در برگشت از فروش']
    q_objects = Q()
    for phrase in st_with:
        q_objects |= Q(sharh__startswith=phrase)
    sale_sanad = SanadDetail.objects.filter(q_objects)
    print('sale_sanad.count()')
    # print(sale_sanad.count())
    cat_level=0
    cat=None
    if cat_id != 'all':
        cat = Category.objects.filter(id=cat_id).last()
        print('cat', cat)
        cat_level = cat.level

        print('cat_level',cat_level)
        if cat_level == 1:
            kalas = Kala.objects.filter(category__parent__parent=cat)
        elif cat_level == 2:
            kalas = Kala.objects.filter(category__parent=cat)
        elif cat_level == 3:
            kalas = Kala.objects.filter(category=cat)

        print('kalas.count():', kalas.count())
        taf_list = kalas.values_list('kala_taf', flat=True).distinct()
        taf_list = list(taf_list)
        sale_sanad=sale_sanad.filter(tafzili__in=taf_list)


        khales_forosh = sale_sanad.aggregate(total_sale=Sum('curramount'))['total_sale'] or 0
        print('khales_forosh')
        print(khales_forosh)
        print('+++++++++++++++++++++++++++++++++++++++++++')




        import re
        all_sharh_descriptions = SanadDetail.objects.filter(kol=102).values_list('sharh', flat=True)
        unique_sharh_patterns = set()
        pattern = re.compile(r'(.*?)\(')
        for sharh_text in all_sharh_descriptions:
            if '(' in sharh_text:
                match = pattern.match(sharh_text)
                if match:
                    extracted_pattern = match.group(1).strip()
                    unique_sharh_patterns.add(extracted_pattern)

        print("حالت‌های منحصر به فرد (کلمات قبل از پرانتز باز):")
        for pattern_found in sorted(list(unique_sharh_patterns)):  # مرتب‌سازی برای نمایش بهتر
            print(f"- '{pattern_found}'")

        print(f"\nتعداد کل حالت‌های منحصر به فرد: {len(unique_sharh_patterns)}")

    cat1 = Category.objects.filter(level=1).order_by('id')
    if cat_level == 0:
        print('cat_level==0')
        par1 = None
        par2 = None
        cat2 = None
        cat3 = None


    if cat_level == 1:
        print('cat_level==1')
        par1 = cat
        par2 = None
        cat2 = Category.objects.filter(parent=cat)
        # cat3=Category.objects.filter(parent__parent=cat)
        cat3 = None
    if cat_level == 2:
        print('cat_level==2')
        par1 = cat.parent
        par2 = cat
        cat2 = Category.objects.filter(parent=par1)
        cat3 = Category.objects.filter(parent=cat)

    if cat_level == 3:
        print('cat_level==3')
        par2 = cat.parent
        par1 = par2.parent
        cat2 = Category.objects.filter(parent=par1)
        cat3 = Category.objects.filter(parent=par2)

    try:
        title=f'{cat}'
    except:
        title='همه دسته بندی ها'

    try:
        cid=f'{cat.id}'
    except:
        cid=0





    context = {
        'title': title,
        'cat_id': cid,
        'cat_level': cat_level,
        'user': user,
        'cat': cat,
        'cat1': cat1,
        'cat2': cat2,
        'cat3': cat3,
        'par1': par1,
        'par2': par2,


    }

    total_time = time.time() - start_time  # محاسبه زمان اجرا
    print(f"زمان کل اجرای تابع: {total_time:.2f} ثانیه")


    return render(request, 'category_sale_report.html', context)
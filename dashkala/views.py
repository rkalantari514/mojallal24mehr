from django.shortcuts import render
from mahakupdate.models import Kardex, Mtables, Category
from persianutils import standardize
from django.utils import timezone
from django.shortcuts import render
from django.db.models import Max, Subquery
from .forms import FilterForm, KalaSelectForm
import time
from django.http import JsonResponse


def fix_persian_characters(value):
    return standardize(value)


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


def TotalKala(request):
    start_time = time.time()  # زمان شروع تابع
    kala_select_form = KalaSelectForm(request.POST or None,
                                          # initial={
                                          #     'product': pro,
                                          #     'seller': sell,
                                          #     'year': year,
                                          #     'mab': mab,
                                          #     'tam': tam,
                                          #
                                          # }
                                          )

    # گرفتن آخرین آیدی برای هر `code_kala` و `warehousecode`
    latest_mojodi = Kardex.objects.values('code_kala', 'warehousecode').annotate(
        latest_id=Max('id')
    ).values('latest_id')  # فقط آخرین ID را برگردانید

    # استفاده از Subquery برای دریافت رکوردهای مربوط به آخرین موجودی و حذف موجودی‌های صفر
    mojodi = Kardex.objects.filter(
        id__in=Subquery(latest_mojodi),
        stock__gt=0,  # حذف موجودی‌های صفر
        warehousecode=13
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

    context = {
        'title': 'داشبورد کالاها',
        'mojodi': mojodi,
        'kala_select_form': kala_select_form,
        'table':table,
    }

    response = render(request, 'total_kala.html', context)  # نام قالب خود را به‌روز کنید

    total_time = time.time() - start_time
    print(f"زمان کل تابع DsshKala: {total_time:.2f} ثانیه")

    return response



def load_categories(request):
    parent_id = request.GET.get('parent_id')
    level = request.GET.get('level')

    # اطمینان از این که مقادیر درست هستند
    print(f"Received parent_id: {parent_id} and level: {level}")  # برای تست در کنسول

    categories = Category.objects.filter(parent_id=parent_id, level=level)  # یا هر منطق مناسب دیگر
    data = list(categories.values('id', 'name'))
    return JsonResponse(data, safe=False)






def filter_kardex(request):
    form = KalaSelectForm(request.GET or None)
    query = Kardex.objects.all()

    if form.is_valid():
        if form.cleaned_data['storage']:
            query = query.filter(storage=form.cleaned_data['storage'])
        if form.cleaned_data['category1']:
            if form.cleaned_data['category1'] != 0:  # فیلتر 'همه' را نادیده می‌گیریم
                query = query.filter(kala__category__level=1, kala__category=form.cleaned_data['category1'])
        if form.cleaned_data['category2']:
            if form.cleaned_data['category2'] != 0:  # فیلتر 'همه' را نادیده می‌گیریم
                query = query.filter(kala__category__level=2, kala__category=form.cleaned_data['category2'])
        if form.cleaned_data['category3']:
            if form.cleaned_data['category3'] != 0:  # فیلتر 'همه' را نادیده می‌گیریم
                query = query.filter(kala__category__level=3, kala__category=form.cleaned_data['category3'])

    data = list(query.values('pdate', 'date', 'percode', 'warehousecode', 'mablaghsanad', 'code_kala', 'radif', 'kala', 'code_factor', 'count', 'averageprice', 'stock'))
    return JsonResponse({'data': data})

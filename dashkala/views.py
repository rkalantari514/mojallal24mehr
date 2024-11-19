from django.shortcuts import render
from mahakupdate.models import Kardex, Mtables, Category, Mojodi
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




def TotalKala(request):
    start_time = time.time()  # زمان شروع تابع
    mojodi = Mojodi.objects.all().order_by('-id')[:1000]

    kala_select_form = KalaSelectForm(request.POST or None)

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
        'table': table,
    }

    response = render(request, 'total_kala.html', context)  # نام قالب خود را به‌روز کنید

    total_time = time.time() - start_time
    print(f"زمان کل تابع DsshKala: {total_time:.2f} ثانیه")

    return response






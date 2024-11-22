from mahakupdate.models import Kardex, Mtables, Category, Mojodi, Storagek
from persianutils import standardize
from django.db.models import Max, Subquery
from .forms import FilterForm, KalaSelectForm
import time
from django.shortcuts import render, redirect
from django.db.models import Sum, F, FloatField
from django.db.models.functions import Coalesce
from django.utils import timezone

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





def TotalKala(request, *args, **kwargs):
    start_time = time.time()  # زمان شروع تابع
    st = kwargs['st']
    cat1 = kwargs['cat1']
    cat2 = kwargs['cat2']
    cat3 = kwargs['cat3']
    tt = kwargs['total']

    print(st,cat1,cat2,cat3)


    detailaddress=f'/dash/kala/total/{st}/{cat1}/{cat2}/{cat3}/detaile'

    total=False if tt== 'total' else True


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

    if kala_select_form.is_valid():
        print("فرم شروع شد")
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
        if storage_mojodi.values('kala').distinct().count()>0:
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
        if category_mojodi.values('kala').distinct().count() >0:
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
        if category_mojodi.values('kala').distinct().count() >0:
            all_category_summaries_3.append(category_summary)




    context = {
        'title': 'موجودی کالاها',
        'mojodi': mojodi,  # جدول برای نمایش
        'kala_select_form': kala_select_form,  # فرم فیلترها
        'table': table,
        'summary': summary,
        'all_storage_summaries': all_storage_summaries,  # خلاصه برای هر انبار در صورت انتخاب 'all'
        'all_category_summaries_1': all_category_summaries_1,  # خلاصه برای هر دسته‌بندی سطح 1
        'all_category_summaries_2': all_category_summaries_2,  # خلاصه برای هر دسته‌بندی سطح 2
        'all_category_summaries_3': all_category_summaries_3,  # خلاصه برای هر دسته‌بندی سطح ۳
        'total':total,
        'detailaddress':detailaddress,
    }

    total_time = time.time() - start_time
    print(f"زمان کل تابع TotalKala: {total_time:.2f} ثانیه")

    return render(request, 'total_kala.html', context)

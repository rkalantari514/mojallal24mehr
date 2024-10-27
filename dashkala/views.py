from django.shortcuts import render
from mahakupdate.models import Kardex, Mtables
from persianutils import standardize
from django.utils import timezone
from django.db.models import OuterRef, Subquery, Max
import time

def fix_persian_characters(value):
    return standardize(value)

def DsshKala(request):
    start_time = time.time()  # زمان شروع تابع
    print("شروع تابع DsshKala")

    # گرفتن آخرین آیدی برای هر `code_kala` و `warehousecode`
    latest_mojodi_start_time = time.time()
    latest_mojodi = Kardex.objects.values('code_kala', 'warehousecode').annotate(
        latest_id=Max('id')
    ).values('latest_id')  # فقط آخرین ID را برگردانید
    latest_mojodi_time = time.time() - latest_mojodi_start_time
    print(f"زمان دریافت آخرین موجودی: {latest_mojodi_time:.2f} ثانیه")

    # حالا میتوانیم از Subquery برای دریافت رکوردهای مربوط به آخرین موجودی استفاده کنیم.
    mojodi_start_time = time.time()
    mojodi = Kardex.objects.filter(
        id__in=Subquery(latest_mojodi)
    ).select_related('kala')  # بارگذاری اطلاعات مرتبط با kala
    mojodi_time = time.time() - mojodi_start_time
    print(f"زمان دریافت موجودی: {mojodi_time:.2f} ثانیه")

    # نمایش نتایج و پردازش برای هر موجودی
    process_start_time = time.time()
    for entry in mojodi:
        if entry.kala is not None:
            entry.kala.name = fix_persian_characters(entry.kala.name)
            entry.arzesh = entry.stock * entry.averageprice
            # print(entry.pdate, entry.code_kala, entry.stock, entry.kala.name)  # پرینت هر entry
        else:
            print(f"No 'kala' found for entry with code_kala: {entry.code_kala}")
    process_time = time.time() - process_start_time
    print(f"زمان پردازش موجودی: {process_time:.2f} ثانیه")

    table_start_time = time.time()
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
    table_time = time.time() - table_start_time
    print(f"زمان تنظیمات جدول: {table_time:.2f} ثانیه")

    top_5_start_time = time.time()
    top_5_arzesh = sorted(mojodi, key=lambda x: x.arzesh, reverse=True)[:5]
    print("Top 5 مقدار ارزش:", [(entry.kala.name, entry.arzesh) for entry in top_5_arzesh if entry.kala is not None])
    total_arzesh = sum([item.arzesh for item in top_5_arzesh if item.kala is not None])
    current_start = 0
    for item in top_5_arzesh:
        if item.kala is not None:
            item.start = current_start
            item.end = current_start + item.arzesh / total_arzesh
            current_start = item.end
    top_5_time = time.time() - top_5_start_time
    print(f"زمان پردازش Top 5: {top_5_time:.2f} ثانیه")

    context_start_time = time.time()
    context = {
        'title': 'داشبورد کالاها',
        'mojodi': mojodi,
        'top_5_arzesh': top_5_arzesh,
    }
    context_time = time.time() - context_start_time
    print(f"زمان آماده سازی context: {context_time:.2f} ثانیه")

    render_start_time = time.time()
    response = render(request, 'dash_kala.html', context)  # نام قالب خود را بهروز کنید
    render_time = time.time() - render_start_time
    print(f"زمان render: {render_time:.2f} ثانیه")

    total_time = time.time() - start_time
    print(f"زمان کل تابع DsshKala: {total_time:.2f} ثانیه")

    return response

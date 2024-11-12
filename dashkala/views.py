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

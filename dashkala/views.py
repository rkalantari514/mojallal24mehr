from django.shortcuts import render
from mahakupdate.models import Kardex, Mtables
from persianutils import standardize
from django.utils import timezone
from django.db.models import OuterRef, Subquery, Max

def fix_persian_characters(value):
    return standardize(value)


# Create your views here.
import time


from django.db.models import OuterRef, Subquery, Max

from django.db.models import OuterRef, Subquery, Max
from django.utils import timezone
import time

def DsshKala(request):
    start_time = time.time()  # زمان شروع تابع
    print("شروع تابع DsshKala")

    # گرفتن آخرین آی‌دی برای هر `code_kala` و `warehousecode`
    latest_mojodi = Kardex.objects.values('code_kala', 'warehousecode').annotate(
        latest_id=Max('id')
    ).values('latest_id')  # فقط آخرین ID را برگردانید

    # حالا می‌توانیم از Subquery برای دریافت رکوردهای مربوط به آخرین موجودی استفاده کنیم.
    mojodi = Kardex.objects.filter(
        id__in=Subquery(latest_mojodi)
    ).select_related('kala')  # بارگذاری اطلاعات مرتبط با kala

    # پرینت بعد از mojodi
    mojodi_time = time.time() - start_time
    print(f"زمان دریافت موجودی: {mojodi_time:.2f} ثانیه")

    # نمایش نتایج و پردازش برای هر موجودی
    for entry in mojodi:
        if entry.kala is not None:
            entry.kala.name = fix_persian_characters(entry.kala.name)
            entry.arzesh = entry.stock * entry.averageprice
            print(entry.pdate, entry.code_kala, entry.stock, entry.kala.name)  # پرینت هر entry
        else:
            print(f"No 'kala' found for entry with code_kala: {entry.code_kala}")

    processing_time = time.time() - start_time
    print("تمام موارد موجود پردازش شدند")
    print(f"زمان پردازش موجودی: {processing_time:.2f} ثانیه")

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

    # پرینت بعد از تنظیم table
    table_time = time.time() - start_time
    print("تنظیمات جدول انجام شد")
    print(f"زمان تنظیمات جدول: {table_time:.2f} ثانیه")

    top_5_arzesh = sorted(mojodi, key=lambda x: x.arzesh, reverse=True)[:5]
    print("Top 5 مقدار ارزش:", [(entry.kala.name, entry.arzesh) for entry in top_5_arzesh if entry.kala is not None])

    total_arzesh = sum([item.arzesh for item in top_5_arzesh if item.kala is not None])
    current_start = 0

    for item in top_5_arzesh:
        if item.kala is not None:
            item.start = current_start
            item.end = current_start + item.arzesh / total_arzesh
            current_start = item.end

    top_5_time = time.time() - start_time
    print("Top 5 پردازش شدند")
    print(f"زمان پردازش Top 5: {top_5_time:.2f} ثانیه")

    context = {
        'title': 'داشبورد کالاها',
        'mojodi': mojodi,
        'top_5_arzesh': top_5_arzesh,
    }

    return render(request, 'your_template_name.html', context)  # نام قالب خود را به‌روز کنید
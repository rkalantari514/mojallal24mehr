from django.shortcuts import render
from django.db.models import Subquery, OuterRef
from mahakupdate.models import Kardex, Mtables
from persianutils import standardize
from django.utils import timezone

def fix_persian_characters(value):
    return standardize(value)


# Create your views here.
import time


def DsshKala(request):
    start_time = time.time()  # زمان شروع تابع
    print("شروع تابع DsshKala")

    # زیر پرسوجو برای دریافت آخرین ردیف از هر `code_kala`
    subquery = Kardex.objects.filter(
        code_kala=OuterRef('code_kala'),
        warehousecode=OuterRef('warehousecode')
    ).values('id')[:1]

    # پرینت بعد از subquery
    print("Subquery ایجاد شد")
    subquery_time = time.time() - start_time
    print(f"زمان ایجاد Subquery: {subquery_time:.2f} ثانیه")

    # دریافت آخرین ردیف از هر `code_kala`
    mojodi = Kardex.objects.filter(id__in=Subquery(subquery))

    # پرینت بعد از mojodi
    print("موارد موجود دریافت شدند:", len(mojodi))
    mojodi_time = time.time() - start_time
    print(f"زمان دریافت موجودی: {mojodi_time:.2f} ثانیه")

    # نمایش نتایج
    for entry in mojodi:
        entry.kala.name = fix_persian_characters(entry.kala.name)
        entry.arzesh = entry.stock * entry.averageprice
        print(entry.pdate, entry.code_kala, entry.stock, entry.kala.name)  # پرینت هر entry

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
    print("Top 5 مقدار ارزش:", [(entry.kala.name, entry.arzesh) for entry in top_5_arzesh])

    total_arzesh = sum([item.arzesh for item in top_5_arzesh])
    current_start = 0

    for item in top_5_arzesh:
        item.start = current_start
        item.end = current_start + item.arzesh / total_arzesh
        current_start = item.end

    top_5_time = time.time() - start_time
    print("Top 5 پردازش شدند")
    print(f"زمان پردازش Top 5: {top_5_time:.2f} ثانیه")

    context = {
        'title': 'داشبورد کالاها',
        'mojodi': mojodi,
        'table': table,
        'top_5_arzesh': top_5_arzesh,
    }

    # پرینت قبل از render
    render_time = time.time() - start_time
    print("آماده سازی context و render")
    print(f"زمان آماده سازی context و render: {render_time:.2f} ثانیه")

    return render(request, 'dash_kala.html', context)

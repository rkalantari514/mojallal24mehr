from functools import update_wrapper

import jdatetime
import pyodbc
from django.shortcuts import render, redirect
import os
from django.http import HttpResponse
import time
from django.db import transaction
from django.utils.timesince import timesince

from mahakupdate.models import Mtables, Kala, Factor, FactorDetaile, WordCount, Kardex, Person
import sys
from django.utils import timezone
import shutil
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
import time
from collections import Counter
from django.shortcuts import render, get_object_or_404
from .forms import CategoryForm, KalaForm
from .models import Kala
import sqlite3

# Create your views here.
def connect_to_mahak():
    sn = os.getenv('COMPUTERNAME')
    print('sn')
    print(sn)

    # hp home
    if sn == 'DESKTOP-ITU3EHV':
        conn = pyodbc.connect('Driver={SQL Server};'
                              'Server=DESKTOP-ITU3EHV\\MAHAK14;'
                              'Database=mahak;'
                              'Trusted_Connection=yes;')
        return conn  # برگرداندن conn در اینجا
    else:

        # surface
        if sn == 'TECH_MANAGER':
            print('====================================================')
            conn = pyodbc.connect('Driver={SQL Server};'
                                  'Server=TECH_MANAGER\\RKALANTARI;'
                                  'Database=mahak;'
                                  'Trusted_Connection=yes;'
                                  # 'Trusted_Connection=no;'
                                  # 'UID=kalan;'
                                  # 'PWD=12345;'
                                  )

            return conn  # برگرداندن conn در اینجا
        else:
            # hp office
            if sn == 'DESKTOP-1ERPR1M':
                conn = pyodbc.connect('Driver={SQL Server};'
                                      'Server=DESKTOP-1ERPR1M\\MAHAK;'
                                      'Database=mahak2;'
                                      'Trusted_Connection=yes;')
                return conn  # برگرداندن conn در اینجا
            else:
                raise EnvironmentError("The computer name does not match.")


# صفحه عملیات آپدیت
def Updatedb(request):
    ff = Kardex.objects.filter(code_kala=58692)
    print(ff)
    for f in ff:
        print(f.pdate, f.stock, f.radif)
    tables = Mtables.objects.filter(in_use=True)
    for t in tables:
        tsinse = (timezone.now() - t.last_update_time).total_seconds() / 60
        if tsinse / t.update_period >= 1:
            t.progress_bar_width = 100
            t.progress_class = 'skill2-bar bg-danger'
        elif tsinse / t.update_period < 0.4:
            t.progress_class = 'skill2-bar bg-success'
            t.progress_bar_width = tsinse / t.update_period * 100
        elif tsinse / t.update_period < 0.9:
            t.progress_bar_width = tsinse / t.update_period * 100
            t.progress_class = 'skill2-bar bg-warning'
        elif tsinse / t.update_period < 1:
            t.progress_bar_width = tsinse / t.update_period * 100
            t.progress_class = 'skill2-bar bg-danger'

        if t.name == 'Fact_Fo':
            t.url1 = 'update/factor'

        if t.name == 'GoodInf':
            t.url1 = 'update/kala'

        if t.name == 'Fact_Fo_Detail':
            t.url1 = 'update/factor-detail'

        if t.name == 'Kardex':
            t.url1 = 'update/kardex'

        if t.name == 'PerInf':
            t.url1 = 'update/person'

    context = {
        'title': 'صفحه آپدیت جداول',
        'tables': tables
    }
    return render(request, 'updatepage.html', context)


# آپدیت همه جدوال که موقع آن است
def Updateall(request):
    tables = Mtables.objects.filter(in_use=True)
    responses = []

    view_map = {
        'Fact_Fo': UpdateFactor,
        'GoodInf': UpdateKala,
        'Fact_Fo_Detail': UpdateFactorDetail,
        'Kardex': UpdateKardex,
        'PerInf': UpdatePerson,
    }

    for t in tables:
        tsinse = (timezone.now() - t.last_update_time).total_seconds() / 60
        if tsinse / t.update_period > 0.0007:
            view_func = view_map.get(t.name)
            if view_func:
                response = view_func(request)
                responses.append(response)

    combined_content = b'\n'.join([response.content for response in responses])
    return redirect('/updatedb')


# آپدیت فاکتور
def UpdateFactor(request):
    import time
    from django.db import transaction

    t0 = time.time()
    print('شروع آپدیت')

    conn = connect_to_mahak()
    cursor = conn.cursor()
    t1 = time.time()

    cursor.execute("SELECT * FROM Fact_Fo")
    mahakt_data = cursor.fetchall()
    existing_in_mahak = {row[0] for row in mahakt_data}

    factors_to_create = []
    factors_to_update = []

    current_factors = {factor.code: factor for factor in Factor.objects.all()}

    for row in mahakt_data:
        code = row[0]
        defaults = {
            'pdate': row[4],
            'mablagh_factor': row[5],
            'takhfif': row[6],
            'create_time': row[38],
            'darsad_takhfif': row[44],
        }

        if code in current_factors:
            factor = current_factors[code]
            for attr, value in defaults.items():
                setattr(factor, attr, value)
            factors_to_update.append(factor)
        else:
            factors_to_create.append(Factor(code=code, **defaults))

    with transaction.atomic():
        # Bulk create new factors
        Factor.objects.bulk_create(factors_to_create)

        # Bulk update existing factors
        Factor.objects.bulk_update(factors_to_update, ['pdate', 'mablagh_factor', 'takhfif', 'create_time', 'darsad_takhfif'])

        # Delete obsolete factors
        Factor.objects.exclude(code__in=existing_in_mahak).delete()

    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" اتصال به دیتا بیس:{db_time:.2f} ثانیه")
    print(f" زمان آپدیت جدول:{update_time:.2f} ثانیه")

    cursor.execute(f"SELECT COUNT(*) FROM Fact_Fo")
    row_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Fact_Fo'")
    column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='Fact_Fo').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    table.row_count = row_count
    table.cloumn_count = column_count
    table.save()

    return redirect('/updatedb')



def UpdateFactor2(request):
    t0 = time.time()
    print('شروع آپدیت')
    conn = connect_to_mahak()
    cursor = conn.cursor()
    print('cursor')
    print(cursor)
    t1 = time.time()
    # ==============================================================# پر کردن جدول فاکتور
    cursor.execute("SELECT * FROM Fact_Fo")  # یا نام همه ستون‌ها را به جا column4, column7, column11 وارد کنید
    mahakt_data = cursor.fetchall()
    existing_in_mahak = {row[0] for row in mahakt_data}  # مجموعه‌ای از کدهای موجود در Fact_Fo
    print('existing_in_mahak')
    print(existing_in_mahak)
    for row in mahakt_data:
        Factor.objects.update_or_create(
            code=row[0],
            defaults={
                'pdate': row[4],
                'mablagh_factor': row[5],
                'takhfif': row[6],
                'create_time': row[38],
                'darsad_takhfif': row[44],
            }
        )
    print('update finish')
    model_to_delete = Factor.objects.exclude(code__in=existing_in_mahak)
    print('model_to_delete')
    print(model_to_delete)
    model_to_delete.delete()
    print('delete finish')
    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" اتصال به دیتا بیس:{db_time:.2f} ثانیه")
    print(f" زمان آپدیت جدول:{update_time:.2f} ثانیه")

    # شمارش تعداد سطرها
    cursor.execute(f"SELECT COUNT(*) FROM Fact_Fo")
    row_count = cursor.fetchone()[0]
    ## شمارش تعداد ستون‌ها
    cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Fact_Fo'")
    column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='Fact_Fo').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    table.row_count = row_count
    table.cloumn_count = column_count
    table.save()

    return redirect('/updatedb')


# آپدیت کاردکس



def UpdateKardex(request):
    import time
    from django.db import transaction

    t0 = time.time()
    print('شروع آپدیت')

    conn = connect_to_mahak()
    cursor = conn.cursor()
    t1 = time.time()

    cursor.execute("SELECT * FROM Kardex")
    mahakt_data = cursor.fetchall()
    existing_in_mahak = set((row[0], row[4], row[12]) for row in mahakt_data)

    kardex_to_create = []
    kardex_to_update = []

    current_kardex = {(kardex.pdate, kardex.code_kala, kardex.stock): kardex for kardex in Kardex.objects.all()}

    for row in mahakt_data:
        pdate = row[0]
        code_kala = row[4]
        stock = row[12]
        defaults = {
            'code_factor': row[6],
            'percode': row[1],
            'warehousecode': row[2],
            'mablaghsanad': row[3],
            'count': row[7],
            'averageprice': row[11],
            'radif': row[14]
        }

        if (pdate, code_kala, stock) in current_kardex:
            kardex = current_kardex[(pdate, code_kala, stock)]
            if any(getattr(kardex, attr) != value for attr, value in defaults.items()):
                for attr, value in defaults.items():
                    setattr(kardex, attr, value)
                kardex_to_update.append(kardex)
        else:
            kardex_to_create.append(Kardex(pdate=pdate, code_kala=code_kala, stock=stock, **defaults))

    with transaction.atomic():
        # Bulk create new kardex records
        if kardex_to_create:
            Kardex.objects.bulk_create(kardex_to_create)

        # Bulk update existing kardex records
        if kardex_to_update:
            Kardex.objects.bulk_update(kardex_to_update, ['code_factor', 'percode', 'warehousecode', 'mablaghsanad', 'count', 'averageprice', 'radif'])

        # Delete obsolete kardex records
        obsolete_kardex = Kardex.objects.exclude(
            pdate__in=[k[0] for k in existing_in_mahak],
            code_kala__in=[k[1] for k in existing_in_mahak],
            stock__in=[k[2] for k in existing_in_mahak]
        )
        if obsolete_kardex.exists():
            obsolete_kardex.delete()
    print('پایان بالک و شروع بررسی به جای سیگنال')
    # اجرای حلقه جایگزین سیگنال‌ها
    for kardex in Kardex.objects.all():
        # اعمال همان تغییراتی که سیگنال‌ها انجام می‌دادند
        try:
            kardex.factor = Factor.objects.get(code=kardex.code_factor)
        except Factor.DoesNotExist:
            kardex.factor = None

        try:
            kardex.kala = Kala.objects.get(code=kardex.code_kala)
        except Kala.DoesNotExist:
            kardex.kala = None

        if kardex.kala:
            kardex.code_kala = kardex.kala.code

        if kardex.factor:
            kardex.code_factor = kardex.factor.code

        if kardex.pdate:
            jalali_date = jdatetime.date(*map(int, kardex.pdate.split('/')))
            kardex.date = jalali_date.togregorian()

        kardex.save()

    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" اتصال به دیتابیس:{db_time:.2f} ثانیه")
    print(f" زمان آپدیت جدول:{update_time:.2f} ثانیه")

    cursor.execute(f"SELECT COUNT(*) FROM Kardex")
    row_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Kardex'")
    column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='Kardex').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    table.row_count = row_count
    table.cloumn_count = column_count
    table.save()

    return redirect('/updatedb')


def UpdateKardex1(request):
    import time
    from django.db import transaction

    t0 = time.time()
    print('شروع آپدیت')

    conn = connect_to_mahak()
    cursor = conn.cursor()
    t1 = time.time()

    cursor.execute("SELECT * FROM Kardex")
    mahakt_data = cursor.fetchall()
    existing_in_mahak = set((row[0], row[4], row[12]) for row in mahakt_data)

    for row in mahakt_data:
        pdate = row[0]
        code_kala = row[4]
        stock = row[12]
        defaults = {
            'code_factor': row[6],
            'percode': row[1],
            'warehousecode': row[2],
            'mablaghsanad': row[3],
            'count': row[7],
            'averageprice': row[11],
            'radif': row[14]
        }

        Kardex.objects.update_or_create(
            pdate=pdate,
            code_kala=code_kala,
            stock=stock,
            defaults=defaults
        )

    # Delete obsolete kardex records
    Kardex.objects.exclude(
        pdate__in=[k[0] for k in existing_in_mahak],
        code_kala__in=[k[1] for k in existing_in_mahak],
        stock__in=[k[2] for k in existing_in_mahak]
    ).delete()

    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" اتصال به دیتا بیس:{db_time:.2f} ثانیه")
    print(f" زمان آپدیت جدول:{update_time:.2f} ثانیه")

    cursor.execute(f"SELECT COUNT(*) FROM Kardex")
    row_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Kardex'")
    column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='Kardex').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    table.row_count = row_count
    table.cloumn_count = column_count
    table.save()

    return redirect('/updatedb')





def UpdateKardex2(request):
    t0 = time.time()
    print('شروع آپدیت')
    conn = connect_to_mahak()
    cursor = conn.cursor()
    print('cursor')
    print(cursor)
    t1 = time.time()

    # پر کردن جدول فاکتور
    cursor.execute("SELECT * FROM Kardex")
    mahakt_data = cursor.fetchall()
    existing_in_mahak = set((row[0], row[4], row[12]) for row in mahakt_data)
    print('existing_in_mahak')
    print(existing_in_mahak)
    for row in mahakt_data:
        print('pdate', row[0])
        print('percode', row[1])
        print('warehousecode', row[2])
        print('mablaghsanad', row[3])
        print('codekala', row[4])
        print('codefactor', row[6])
        print('count', row[7])
        print('averageprice', row[11])
        print('stock ', row[12])
        print('-------------------------------')
        Kardex.objects.update_or_create(
            pdate=row[0],
            code_kala=row[4],
            stock=row[12],
            defaults={
                'code_factor': row[6],
                'percode': row[1],
                'warehousecode': row[2],
                'mablaghsanad': row[3],
                'count': row[7],
                'averageprice': row[11],
                'radif': row[14],
            }
        )
    print('update finish')

    existing_keys = set((detail.pdate, detail.code_kala, detail.stock) for detail in Kardex.objects.all())
    model_to_delete = existing_keys - existing_in_mahak
    for key in model_to_delete:
        if len(key) == 3:
            Kardex.objects.filter(pdate=key[0], code_kala=key[1], stock=key[2]).delete()

    print('delete finish')
    tend = time.time()
    total_time = tend - t0
    print(f"زمان کل: {total_time:.2f} ثانیه")

    print('delete finish')
    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" اتصال به دیتا بیس:{db_time:.2f} ثانیه")
    print(f" زمان آپدیت جدول:{update_time:.2f} ثانیه")

    # شمارش تعداد سطرها
    cursor.execute(f"SELECT COUNT(*) FROM Kardex")
    row_count = cursor.fetchone()[0]
    ## شمارش تعداد ستون‌ها
    cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Kardex'")
    column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='Kardex').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    table.row_count = row_count
    table.cloumn_count = column_count
    table.save()

    return redirect('/updatedb')

def UpdateFactorDetail(request):
    import time
    from django.db import transaction

    t0 = time.time()
    print('شروع آپدیت')

    conn = connect_to_mahak()
    cursor = conn.cursor()
    t1 = time.time()

    cursor.execute("SELECT * FROM Fact_Fo_Detail")
    mahakt_data = cursor.fetchall()
    existing_in_mahak = set((row[0], row[1]) for row in mahakt_data)

    for row in mahakt_data:
        code_factor = row[0]
        radif = row[1]
        defaults = {
            'code_kala': row[3],
            'count': row[5],
            'mablagh_vahed': row[6],
            'mablagh_nahaee': row[29],
        }

        FactorDetaile.objects.update_or_create(
            code_factor=code_factor,
            radif=radif,
            defaults=defaults
        )

    # حذف رکوردهای غیرضروری
    FactorDetaile.objects.exclude(
        code_factor__in=[k[0] for k in existing_in_mahak],
        radif__in=[k[1] for k in existing_in_mahak]
    ).delete()

    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" اتصال به دیتابیس:{db_time:.2f} ثانیه")
    print(f" زمان آپدیت جدول:{update_time:.2f} ثانیه")

    cursor.execute(f"SELECT COUNT(*) FROM Fact_Fo_Detail")
    row_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Fact_Fo_Detail'")
    column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='Fact_Fo_Detail').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    table.row_count = row_count
    table.cloumn_count = column_count
    table.save()

    return redirect('/updatedb')

def UpdateFactorDetail2(request):
    t0 = time.time()
    print('شروع آپدیت')
    conn = connect_to_mahak()
    cursor = conn.cursor()
    print('cursor')
    print(cursor)
    t1 = time.time()
    # ==================================================================پر کردن جدول جزئیات فاکتور
    cursor.execute("SELECT * FROM Fact_Fo_Detail")
    mahakt_data = cursor.fetchall()
    existing_in_mahak = set((row[0], row[1]) for row in mahakt_data)
    for row in mahakt_data:
        print(row)
        # با استفاده از ترکیب چند فیلد
        FactorDetaile.objects.update_or_create(
            code_factor=row[0],  # فیلد اول برای شناسایی
            radif=row[1],  # فیلد دوم برای شناسایی
            defaults={
                'code_kala': row[3],
                'count': row[5],
                'mablagh_vahed': row[6],
                'mablagh_nahaee': row[29],
            }
        )

    existing_keys = set((detail.code_factor, detail.radif) for detail in FactorDetaile.objects.all())
    model_to_delete = existing_keys - existing_in_mahak
    for key in model_to_delete:
        FactorDetaile.objects.filter(code_factor=key[0], radif=key[1]).delete()

    print('update finish')

    existing_keys = set((detail.code_factor, detail.radif) for detail in FactorDetaile.objects.all())
    model_to_delete = existing_keys - existing_in_mahak
    print('model_to_delete')
    print(model_to_delete)

    for key in model_to_delete:
        FactorDetaile.objects.filter(code_factor=key[0], radif=key[1]).delete()
    print('delete finish')

    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" اتصال به دیتا بیس:{db_time:.2f} ثانیه")
    print(f" زمان آپدیت جدول:{update_time:.2f} ثانیه")

    # شمارش تعداد سطرها
    cursor.execute(f"SELECT COUNT(*) FROM Fact_Fo_Detail")
    row_count = cursor.fetchone()[0]
    ## شمارش تعداد ستون‌ها
    cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Fact_Fo_Detail'")
    column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='Fact_Fo_Detail').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    table.row_count = row_count
    table.cloumn_count = column_count
    table.save()

    return redirect('/updatedb')


def UpdateKala(request):
    t0 = time.time()
    print('شروع آپدیت')

    conn = connect_to_mahak()
    cursor = conn.cursor()
    t1 = time.time()

    cursor.execute("SELECT code, name FROM GoodInf")
    mahakt_data = cursor.fetchall()
    existing_in_mahak = {row[0] for row in mahakt_data}

    kalas_to_create = []
    kalas_to_update = []

    current_kalas = {kala.code: kala for kala in Kala.objects.all()}

    for row in mahakt_data:
        code = row[0]
        name = row[1]

        if code in current_kalas:
            if current_kalas[code].name != name:
                current_kalas[code].name = name
                kalas_to_update.append(current_kalas[code])
        else:
            kalas_to_create.append(Kala(code=code, name=name))

    # Bulk create new kalas
    Kala.objects.bulk_create(kalas_to_create)

    # Bulk update existing kalas
    Kala.objects.bulk_update(kalas_to_update, ['name'])

    # Delete obsolete kalas
    Kala.objects.exclude(code__in=existing_in_mahak).delete()

    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" اتصال به دیتا بیس:{db_time:.2f} ثانیه")
    print(f" زمان آپدیت جدول:{update_time:.2f} ثانیه")

    cursor.execute(f"SELECT COUNT(*) FROM GoodInf")
    row_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'GoodInf'")
    column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='GoodInf').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    table.row_count = row_count
    table.cloumn_count = column_count
    table.save()

    return redirect('/updatedb')


def UpdateKala1(request):
    t0 = time.time()
    print('شروع آپدیت')
    conn = connect_to_mahak()
    cursor = conn.cursor()
    print('cursor')
    print(cursor)
    t1 = time.time()
    #  ================================================== پر کردن جدول کالا ============
    cursor.execute("SELECT * FROM GoodInf")
    mahakt_data = cursor.fetchall()
    existing_in_mahak = {row[1] for row in mahakt_data}
    print('existing_in_mahak')
    print(existing_in_mahak)
    ii = 1
    for row in mahakt_data:
        print(ii, '-->', row[1])
        ii += 1
        Kala.objects.update_or_create(
            code=row[1],
            defaults={
                'name': row[2],
            }
        )
    print('update finish')
    model_to_delete = Kala.objects.exclude(code__in=existing_in_mahak)
    print('model_to_delete')
    print(model_to_delete)
    model_to_delete.delete()
    print('delete finish')
    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" اتصال به دیتا بیس:{db_time:.2f} ثانیه")
    print(f" زمان آپدیت جدول:{update_time:.2f} ثانیه")

    # شمارش تعداد سطرها
    cursor.execute(f"SELECT COUNT(*) FROM GoodInf")
    row_count = cursor.fetchone()[0]
    ## شمارش تعداد ستون‌ها
    cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'GoodInf'")
    column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='GoodInf').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    table.row_count = row_count
    table.cloumn_count = column_count
    table.save()

    return redirect('/updatedb')


def UpdateKala2(request):
    t0 = time.time()
    print('شروع آپدیت')
    # conn = connect_to_mahak()
    # cursor = conn.cursor()
    # print('cursor')
    # print(cursor)
    t1 = time.time()
    #  ================================================== پر کردن جدول کالا ============
    # cursor.execute("SELECT * FROM GoodInf")
    # mahakt_data = cursor.fetchall()
    # existing_in_mahak = {row[1] for row in mahakt_data}
    # print('existing_in_mahak')
    # print(existing_in_mahak)
    ii = 1

    import os
    import shutil

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # مسیر اصلی پروژه رو تنظیم کن
    db_path = os.path.join(BASE_DIR, 'db.sqlite3')
    db_path_copy = os.path.join(BASE_DIR, 'db2.sqlite3')

    # کپی کردن دیتابیس اصلی به فایل جدید
    shutil.copyfile(db_path, db_path_copy)

    # مطمئن شو فایل کپی‌شده وجود داره
    if os.path.exists(db_path_copy):
        print(f"Copy created at: {db_path_copy}")
    else:
        print("Failed to create a copy of the database.")

    conn_sqlite_copy = sqlite3.connect(db_path_copy)
    cursor_sqlite_copy = conn_sqlite_copy.cursor()



    conn_sql_server = pyodbc.connect('Driver={SQL Server};'
                                     'Server=TECH_MANAGER\\RKALANTARI;'
                                     'Database=mahak;'
                                     'Trusted_Connection=yes;')
    cursor_sql_server = conn_sql_server.cursor()
    cursor_sql_server.execute("SELECT * FROM GoodInf")
    mahakt_data = cursor_sql_server.fetchall()

    # به‌روز رسانی جداول SQLite با داده‌های SQL Server
    for row in mahakt_data:
        code = row[1]
        name = row[2]

        cursor_sqlite_copy.execute("SELECT code FROM mahakupdate_kala WHERE code=?", (code,))
        data = cursor_sqlite_copy.fetchone()

        if data:
            cursor_sqlite_copy.execute("UPDATE mahakupdate_kala SET name=? WHERE code=?", (name, code))
        else:
            cursor_sqlite_copy.execute("INSERT INTO mahakupdate_kala (code, name) VALUES (?, ?)", (code, name))

    # ابتدا همه کدهای موجود در SQL Server رو به‌دست بیار
    codes_in_sql_server = [row[1] for row in mahakt_data]

    # پیدا کردن و حذف رکوردهای اضافی در SQLite
    cursor_sqlite_copy.execute("SELECT code FROM mahakupdate_kala")
    codes_in_sqlite = cursor_sqlite_copy.fetchall()
    for code in codes_in_sqlite:
        if code[0] not in codes_in_sql_server:
            cursor_sqlite_copy.execute("DELETE FROM mahakupdate_kala WHERE code=?", (code[0],))

    conn_sqlite_copy.commit()

    conn_sqlite_copy.commit()

    conn_sqlite_copy.close()
    conn_sql_server.close()

    # جایگزین کردن فایل دیتابیس اصلی با دیتابیس کپی‌شده
    shutil.move(db_path_copy, db_path)

    # for row in mahakt_data:
    #     code = row[1]
    #     name = row[2]
    #
    #     cursor_sqlite.execute("SELECT * FROM kala WHERE code=?", (code,))
    #     data = cursor_sqlite.fetchone()
    #
    #     if data:
    #         cursor_sqlite.execute("UPDATE kala SET name=? WHERE code=?", (name, code))
    #     else:
    #         cursor_sqlite.execute("INSERT INTO kala (code, name) VALUES (?, ?)", (code, name))

    # conn_sqlite.commit()

    # print('update finish')
    # model_to_delete = Kala.objects.exclude(code__in=existing_in_mahak)
    # print('model_to_delete')
    # print(model_to_delete)
    # model_to_delete.delete()
    # print('delete finish')
    tend = time.time()
    # total_time = tend - t0
    # db_time = t1 - t0
    update_time = tend - t1
    #
    # print(f"زمان کل: {total_time:.2f} ثانیه")
    # print(f" اتصال به دیتا بیس:{db_time:.2f} ثانیه")
    # print(f" زمان آپدیت جدول:{update_time:.2f} ثانیه")
    #
    # شمارش تعداد سطرها
    # cursor.execute(f"SELECT COUNT(*) FROM GoodInf")
    # row_count = cursor.fetchone()[0]
    ## شمارش تعداد ستون‌ها
    # cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'GoodInf'")
    # column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='GoodInf').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    # table.row_count = row_count
    # table.cloumn_count = column_count
    table.save()

    return redirect('/updatedb')


def Update_from_mahak(request):
    t0 = time.time()
    print('شروع آپدیت')
    conn = connect_to_mahak()
    cursor = conn.cursor()
    print('cursor')
    print(cursor)

    t1 = time.time()

    # # شناسایی کل جاول موجود
    # cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    # tables = cursor.fetchall()
    # # خواندن نام جداول
    # for table in tables:
    #     try:
    #         table_name = table[0]
    #
    #         # شمارش تعداد سطرها
    #         cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    #         row_count = cursor.fetchone()[0]
    #
    #         # شمارش تعداد ستون‌ها
    #         cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'")
    #         column_count = cursor.fetchone()[0]
    #
    #         Mtables.objects.update_or_create(
    #             name=table_name,
    #             defaults={
    #                 'row_count': row_count,
    #                 'cloumn_count': column_count
    #             }
    #         )
    #         print('ok ok ok ok ok ok ok ok table_name',table_name)
    #
    #     except:
    #         print('error',table_name)
    #         try:
    #             cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    #             print('m1')
    #             cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    #             row_count = cursor.fetchone()[0]
    #             print('row_count', row_count)
    #             cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'")
    #             column_count = cursor.fetchone()[0]
    #             print('column_count', column_count)
    #         except:
    #             print('nononononoonon')

    t2 = time.time()

    #  ================================================== پر کردن جدول کالا ============
    # cursor.execute("SELECT * FROM GoodInf")
    # mahakt_data = cursor.fetchall()
    # existing_in_mahak = {row[1] for row in mahakt_data}
    # print('existing_in_mahak')
    # print(existing_in_mahak)
    # for row in mahakt_data:
    #     Kala.objects.update_or_create(
    #         code=row[1],
    #         defaults={
    #             'name': row[2],
    #         }
    #     )
    # print('update finish')
    # model_to_delete = Kala.objects.exclude(code__in=existing_in_mahak)
    # print('model_to_delete')
    # print(model_to_delete)
    # model_to_delete.delete()
    # print('delete finish')

    t3 = time.time()
    # ==============================================================# پر کردن جدول فاکتور
    # cursor.execute("SELECT * FROM Fact_Fo")  # یا نام همه ستون‌ها را به جا column4, column7, column11 وارد کنید
    # mahakt_data = cursor.fetchall()
    # existing_in_mahak = {row[0] for row in mahakt_data}  # مجموعه‌ای از کدهای موجود در Fact_Fo
    # print('existing_in_mahak')
    # print(existing_in_mahak)
    # for row in mahakt_data:
    #     Factor.objects.update_or_create(
    #         code=row[0],
    #         defaults={
    #             'pdate': row[4],
    #             'mablagh_factor': row[5],
    #             'takhfif': row[6],
    #             'create_time': row[38],
    #             'darsad_takhfif': row[44],
    #         }
    #     )
    # print('update finish')
    # model_to_delete = Factor.objects.exclude(code__in=existing_in_mahak)
    # print('model_to_delete')
    # print(model_to_delete)
    # model_to_delete.delete()
    # print('delete finish')

    t4 = time.time()
    # ==================================================================پر کردن جدول جزئیات فاکتور
    # cursor.execute("SELECT * FROM Fact_Fo_Detail")
    # mahakt_data = cursor.fetchall()
    # existing_in_mahak = set((row[0], row[1]) for row in mahakt_data)
    # for row in mahakt_data:
    #     print(row)
    #     # با استفاده از ترکیب چند فیلد
    #     FactorDetaile.objects.update_or_create(
    #         code_factor=row[0],  # فیلد اول برای شناسایی
    #         radif=row[1],  # فیلد دوم برای شناسایی
    #         defaults={
    #             'code_kala': row[3],
    #             'count': row[5],
    #             'mablagh_vahed': row[6],
    #             'mablagh_nahaee': row[29],
    #         }
    #     )
    #
    # existing_keys = set((detail.code_factor, detail.radif) for detail in FactorDetaile.objects.all())
    # model_to_delete = existing_keys - existing_in_mahak
    # for key in model_to_delete:
    #     FactorDetaile.objects.filter(code_factor=key[0], radif=key[1]).delete()

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # جدول کاردکس
    t5 = time.time()
    cursor.execute("SELECT * FROM PerInf")  # یا نام همه ستون‌ها را به جا column4, column7, column11 وارد کنید
    mahakt_data = cursor.fetchall()
    # existing_in_mahak = {row[0] for row in mahakt_data}  # مجموعه‌ای از کدهای موجود در Fact_Fo
    # print('existing_in_mahak')
    # print(existing_in_mahak)
    for row in mahakt_data:
        # if row[4] == 58692:
        print(row)
    #     ======.objects.update_or_create(
    #         code=row[0],
    #         defaults={
    #             'pdate': row[4],
    #             'mablagh_factor': row[5],
    #             'takhfif': row[6],
    #             'create_time': row[38],
    #             'darsad_takhfif': row[44],
    #         }
    #     )
    # print('update finish')
    # model_to_delete = Factor.objects.exclude(code__in=existing_in_mahak)
    # print('model_to_delete')
    # print(model_to_delete)
    # model_to_delete.delete()
    # print('delete finish')

    t6 = time.time()

    tend = time.time()

    total_time = tend - t0
    db_time = t1 - t0
    table_time = t2 - t1
    kala_time = t3 - t2
    factor_time = t4 - t3
    factor_detail_time = t5 - t4
    kardex_time = t6 - t5

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" اتصال به دیتا بیس:{db_time:.2f} ثانیه")
    print(f"شناسایی جداول:{table_time:.2f} ثانیه")
    print(f"شناسایی کالاها: {kala_time:.2f} ثانیه")
    print(f"فاکتورها {factor_time:.2f} ثانیه")
    print(f"جزئیات فاکتورها {factor_detail_time:.2f} ثانیه")
    print(f"جزئیات  {kardex_time:.2f} ثانیه")


def Kala_group(request):
    # دریافت کالاهای موجود در جزئیات فاکتور
    # WordCount.objects.all().delete()
    # factors = FactorDetaile.objects.values('kala').distinct()
    # kalas = Kala.objects.filter(id__in=[item['kala'] for item in factors])
    # kalas=Kala.objects.all()
    # all_words = []
    # for kala in kalas:
    #     words = kala.name.split()  # تقسیم نام به کلمات
    #     all_words.extend(words)  # افزودن کلمات به لیست
    # filtered_words = [word for word in all_words if len(word) > 3]
    # # شمارش تکرار کلمات
    # word_counts = Counter(filtered_words)
    # # ذخیره کلمات و تعداد تکرار آنها در مدل WordCount
    # for word, count in word_counts.items():
    #     if count>4:
    #         WordCount.objects.update_or_create(word=word, defaults={'count': count})

    words = WordCount.objects.all()
    context = {
        'title': 'گروه بندی کالاها',
        'words': words,
    }

    return render(request, 'kala_group.html', context)


def category_create_view(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_list')  # تغییر مسیر به لیست دسته‌بندی‌ها
    else:
        form = CategoryForm()
    return render(request, 'category_form.html', {'form': form})


def kala_create_view(request):
    if request.method == "POST":
        form = KalaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('kala_list')  # تغییر مسیر به لیست کالاها
    else:
        form = KalaForm()
    return render(request, 'kala_form.html', {'form': form})


# آپدیت گروه

# آپدیت افراد
def UpdatePerson(request):
    t0 = time.time()
    print('شروع آپدیت')
    conn = connect_to_mahak()
    cursor = conn.cursor()
    print('cursor')
    print(cursor)
    t1 = time.time()
    # ==============================================================# پر کردن جدول افراد
    cursor.execute("SELECT * FROM PerInf")  # یا نام همه ستون‌ها را به جا column4, column7, column11 وارد کنید
    mahakt_data = cursor.fetchall()
    existing_in_mahak = {row[0] for row in mahakt_data}  # مجموعه‌ای از کدهای موجود در Fact_Fo
    print('existing_in_mahak')
    print(existing_in_mahak)

    for row in mahakt_data:
        Person.objects.update_or_create(
            code=row[0],
            defaults={
                'grpcode': row[3],
                'name': row[1],
                'lname': row[2],
                'tel1': row[6],
                'tel2': row[7],
                'fax': row[8],
                'mobile': row[9],
                'address': row[10],
                'comment': row[12],
            }
        )
    print('update finish')
    model_to_delete = Person.objects.exclude(code__in=existing_in_mahak)
    print('model_to_delete')
    print(model_to_delete)
    model_to_delete.delete()
    print('delete finish')
    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" اتصال به دیتا بیس:{db_time:.2f} ثانیه")
    print(f" زمان آپدیت جدول:{update_time:.2f} ثانیه")

    # شمارش تعداد سطرها
    cursor.execute(f"SELECT COUNT(*) FROM PerInf")
    row_count = cursor.fetchone()[0]
    ## شمارش تعداد ستون‌ها
    cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'PerInf'")
    column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='PerInf').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    table.row_count = row_count
    table.cloumn_count = column_count
    table.save()

    return redirect('/updatedb')
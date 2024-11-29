from django.conf import settings
import pyodbc
from mahakupdate.models import WordCount, Person, KalaGroupinfo, Category
from django.shortcuts import render
from .forms import CategoryForm, KalaForm
from .models import FactorDetaile
import os
import pandas as pd
from .models import Factor, Kala, Storagek, Mtables
from django.utils import timezone
import jdatetime  # فرض بر این است که برای تبدیل تاریخ هجری شمسی به میلادی استفاده می‌شود
from django.db.models import Max, Q
from .models import Mojodi
from django.db.models import Q


# sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)


# Create your views here.
def connect_to_mahak():
    sn = os.getenv('COMPUTERNAME')
    print('sn')
    print(sn)

    connections = {
        'DESKTOP-ITU3EHV': ('DESKTOP-ITU3EHV\\MAHAK14', 'mahak'),
        'TECH_MANAGER': ('TECH_MANAGER\\RKALANTARI', 'mahak'),
        'DESKTOP-1ERPR1M': ('DESKTOP-1ERPR1M\\MAHAK', 'mahak'),
        'RP-MAHAK': ('Ac\\MAHAK', 'mahak')
    }

    if sn in connections:
        server, database = connections[sn]
        if sn == 'RP-MAHAK':
            conn = pyodbc.connect(
                f'Driver={{SQL Server}};Server={server};Database={database};UID=sa;PWD=6070582;Integrated Security=False;'
                # f'Driver={{SQL Server}};Server={server};Database={database};UID=ali;PWD=123456;Trusted_Connection=no;'

            )
        else:
            conn = pyodbc.connect(
                f'Driver={{SQL Server}};Server={server};Database={database};Trusted_Connection=yes;'
            )
        return conn
    else:
        raise EnvironmentError("The computer name does not match.")


# صفحه عملیات آپدیت
def Updatedb(request):
    tables = Mtables.objects.filter(in_use=True)
    url_mapping = {
        'Fact_Fo': 'update/factor',
        'GoodInf': 'update/kala',
        'Fact_Fo_Detail': 'update/factor-detail',
        'Kardex': 'update/kardex',
        'PerInf': 'update/person',
        'Stores': 'update/storage',

    }

    for t in tables:
        tsinse = (timezone.now() - t.last_update_time).total_seconds() / 60
        ratio = tsinse / t.update_period
        t.progress_bar_width = min(ratio, 1) * 100
        t.progress_class = (
            'skill2-bar bg-success' if ratio < 0.4 else
            'skill2-bar bg-warning' if ratio < 0.9 else
            'skill2-bar bg-danger'
        )
        t.url1 = url_mapping.get(t.name, '')

    context = {
        'title': 'صفحه آپدیت جداول',
        'tables': tables
    }

    return render(request, 'updatepage.html', context)


# آپدیت همه جدوال که موقع آن است
def Updateall(request):
    tables = Mtables.objects.filter(in_use=True).order_by('update_priority')
    view_map = {
        'Fact_Fo': UpdateFactor,
        'GoodInf': UpdateKala,
        'Fact_Fo_Detail': UpdateFactorDetail,
        'Kardex': UpdateKardex,
        'PerInf': UpdatePerson,
        'Stores': UpdateStorage,
    }

    responses = [
        view_map[t.name](request)
        for t in tables
        if (timezone.now() - t.last_update_time).total_seconds() / 60 / t.update_period > 0.0005
    ]

    combined_content = b'\n'.join([response.content for response in responses])
    return redirect('/updatedb')


# آپدیت فاکتور
def UpdateFactor(request):
    t0 = time.time()
    print('شروع آپدیت فاکتور--------------------------------------')

    conn = connect_to_mahak()
    cursor = conn.cursor()
    t1 = time.time()

    cursor.execute("SELECT * FROM Fact_Fo")
    mahakt_data = cursor.fetchall()
    existing_in_mahak = {row[0] for row in mahakt_data}

    factors_to_create = []
    factors_to_update = []

    current_factors = {factor.code: factor for factor in Factor.objects.iterator()}

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
            if any(getattr(factor, attr) != value for attr, value in defaults.items()):
                for attr, value in defaults.items():
                    setattr(factor, attr, value)
                factors_to_update.append(factor)
        else:
            factors_to_create.append(Factor(code=code, **defaults))

    with transaction.atomic():
        # Bulk create new factors
        if factors_to_create:
            Factor.objects.bulk_create(factors_to_create)

        # Bulk update existing factors
        if factors_to_update:
            Factor.objects.bulk_update(factors_to_update,
                                       ['pdate', 'mablagh_factor', 'takhfif', 'create_time', 'darsad_takhfif'])

        # Delete obsolete factors
        Factor.objects.exclude(code__in=existing_in_mahak).delete()

    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" اتصال به دیتابیس:{db_time:.2f} ثانیه")
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


# آپدیت کاردکس

from django.db import transaction
from django.shortcuts import redirect
import time

import time
from django.db import transaction
from django.utils import timezone
from .models import Kardex, Mtables, Factor, Kala, Storagek

import math

def UpdateKardex(request):
    t0 = time.time()
    print('شروع آپدیت کاردکس----------------------------------------')

    conn = connect_to_mahak()  # فرض بر این است که این تابع اتصال به دیتابیس را برقرار می‌کند.
    cursor = conn.cursor()
    t1 = time.time()

    # خواندن داده‌ها از جدول Kardex
    cursor.execute("SELECT * FROM Kardex")
    mahakt_data = cursor.fetchall()

    # مرحله به‌روزرسانی یا ایجاد رکوردها
    updates = []
    new_records = []

    # بارگذاری رکوردهای موجود در دیتابیس به یک دیکشنری
    existing_kardex = {
        (k.pdate, k.code_kala, k.stock, k.radif): k
        for k in Kardex.objects.all()
    }

    # مجموعه‌ای برای کلیدهای رکوردهای جدید
    new_keys = set()

    for row in mahakt_data:
        pdate = row[0]
        code_kala = row[4]
        stock = row[12]
        radif = row[14]
        defaults = {
            'code_factor': row[6],
            'percode': row[1],
            'warehousecode': row[2],
            'mablaghsanad': row[3],
            'count': row[7],
            'averageprice': row[11],
        }

        # ایجاد کلید برای رکورد جدید
        key = (pdate, code_kala, stock, radif)
        new_keys.add(key)

        if key in existing_kardex:
            kardex_instance = existing_kardex[key]
            # به‌روزرسانی رکورد موجود و تنظیم sync_mojodi به False
            updated = False
            for field, value in defaults.items():
                if isinstance(value, float):
                    # استفاده از math.isclose برای مقایسه عددی دقیق
                    if not math.isclose(getattr(kardex_instance, field), value, rel_tol=1e-9):
                        setattr(kardex_instance, field, value)
                        print('====================')
                        updated = True
                else:
                    if str(getattr(kardex_instance, field)) != str(value) and getattr(kardex_instance, field) != value:
                        setattr(kardex_instance, field, value)
                        print('+++++++++++++++++++++++')
                        print(getattr(kardex_instance, field) , value)
                        updated = True
            if updated:
                print(kardex_instance.code_kala, "---------------------------")
                kardex_instance.sync_mojodi = False
                updates.append(kardex_instance)
        else:
            # ایجاد رکورد جدید و تنظیم sync_mojodi به False
            new_records.append(Kardex(
                pdate=pdate,
                code_kala=code_kala,
                stock=stock,
                radif=radif,
                sync_mojodi=False,
                **defaults
            ))

    # ذخیره‌سازی دسته‌ای
    if updates or new_records:
        with transaction.atomic():
            Kardex.objects.bulk_update(updates, ['code_factor', 'percode', 'warehousecode', 'mablaghsanad', 'count',
                                                 'averageprice', 'sync_mojodi'])
            Kardex.objects.bulk_create(new_records)
            print(f"{len(updates) + len(new_records)} رکورد به‌روز رسانی یا ایجاد شد.")

    t2 = time.time()
    print('آپدیت انجام شد')

    # حذف رکوردهای اضافی
    existing_keys = set(existing_kardex.keys())
    keys_to_delete = existing_keys - new_keys

    if keys_to_delete:
        Kardex.objects.filter(
            pdate__in=[key[0] for key in keys_to_delete],
            code_kala__in=[key[1] for key in keys_to_delete],
            stock__in=[key[2] for key in keys_to_delete],
            radif__in=[key[3] for key in keys_to_delete]
        ).delete()
        print(f"{len(keys_to_delete)} رکورد اضافی حذف شد.")

    # اجرای حلقه جایگزین سیگنال‌ها
    kardex_instances = list(Kardex.objects.prefetch_related('factor', 'kala', 'storage').all())
    updates = []
    factors = {factor.code: factor for factor in
               Factor.objects.filter(code__in=[k.code_factor for k in kardex_instances])}
    kalas = {kala.code: kala for kala in Kala.objects.filter(code__in=[k.code_kala for k in kardex_instances])}
    storages = {storage.code: storage for storage in
                Storagek.objects.filter(code__in=[k.warehousecode for k in kardex_instances])}

    for kardex in kardex_instances:
        factor = factors.get(kardex.code_factor)
        kala = kalas.get(kardex.code_kala)
        storage = storages.get(kardex.warehousecode)

        # بررسی تغییرات قبل از به‌روزرسانی
        updated = False
        if kardex.factor != factor:
            kardex.factor = factor
            updated = True

        if kardex.kala != kala:
            kardex.kala = kala
            updated = True

        if kardex.storage != storage:
            kardex.storage = storage
            updated = True

        # بررسی تغییر تاریخ
        if kardex.pdate:
            jalali_date = jdatetime.date(*map(int, kardex.pdate.split('/')))
            new_date = jalali_date.togregorian()
            if kardex.date != new_date:
                kardex.date = new_date
                updated = True

        if updated:
            updates.append(kardex)

    # ذخیره‌سازی دسته‌ای
    if updates:
        with transaction.atomic():
            Kardex.objects.bulk_update(updates,
                                       ['factor', 'kala', 'storage', 'warehousecode', 'code_kala', 'code_factor',
                                        'date'])
            print(f"{len(updates)} رکورد به‌روز رسانی سیگنال‌ها انجام شد.")

    t3 = time.time()
    print('جایگزین سیگنال انجام شد')

    # ثبت زمان‌ها و اطلاعات آخرین بروزرسانی در مدل Mtables
    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    up_time = t2 - t1
    sig_time = t3 - t2

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f"اتصال به دیتابیس: {db_time:.2f} ثانیه")
    print(f"عملیات اصلی آپدیت: {up_time:.2f} ثانیه")
    print(f"جایگزین سیگنال: {sig_time:.2f} ثانیه")

    cursor.execute("SELECT COUNT(*) FROM Kardex")
    row_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Kardex'")
    column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='Kardex').last()
    table.last_update_time = timezone.now()
    table.update_duration = total_time
    table.row_count = row_count
    table.column_count = column_count
    table.save()

    return redirect('/updatedb')







def UpdateKardexdorost(request):
    t0 = time.time()
    print('شروع آپدیت کاردکس----------------------------------------')

    conn = connect_to_mahak()  # فرض بر این است که این تابع اتصال به دیتابیس را برقرار می‌کند.
    cursor = conn.cursor()
    t1 = time.time()

    # خواندن داده‌ها از جدول Kardex
    cursor.execute("SELECT * FROM Kardex")
    mahakt_data = cursor.fetchall()

    # مرحله به‌روزرسانی یا ایجاد رکوردها
    updates = []
    new_records = []

    # بارگذاری رکوردهای موجود در دیتابیس به یک دیکشنری
    existing_kardex = {
        (k.pdate, k.code_kala, k.stock, k.radif): k
        for k in Kardex.objects.all()
    }

    # مجموعه‌ای برای کلیدهای رکوردهای جدید
    new_keys = set()

    for row in mahakt_data:
        pdate = row[0]
        code_kala = row[4]
        stock = row[12]
        radif = row[14]
        defaults = {
            'code_factor': row[6],
            'percode': row[1],
            'warehousecode': row[2],
            'mablaghsanad': row[3],
            'count': row[7],
            'averageprice': row[11],
        }

        # ایجاد کلید برای رکورد جدید
        key = (pdate, code_kala, stock, radif)
        new_keys.add(key)

        if key in existing_kardex:
            kardex_instance = existing_kardex[key]
            # به‌روزرسانی رکورد موجود
            for field, value in defaults.items():
                setattr(kardex_instance, field, value)
            updates.append(kardex_instance)
        else:
            # ایجاد رکورد جدید
            new_records.append(Kardex(
                pdate=pdate,
                code_kala=code_kala,
                stock=stock,
                radif=radif,
                **defaults
            ))

    # ذخیره‌سازی دسته‌ای
    if updates or new_records:
        with transaction.atomic():
            Kardex.objects.bulk_update(updates, ['code_factor', 'percode', 'warehousecode', 'mablaghsanad', 'count',
                                                 'averageprice'])
            Kardex.objects.bulk_create(new_records)
            print(f"{len(updates) + len(new_records)} رکورد به‌روز رسانی یا ایجاد شد.")

    t2 = time.time()
    print('آپدیت انجام شد')

    # حذف رکوردهای اضافی
    existing_keys = set(existing_kardex.keys())
    keys_to_delete = existing_keys - new_keys

    if keys_to_delete:
        Kardex.objects.filter(
            pdate__in=[key[0] for key in keys_to_delete],
            code_kala__in=[key[1] for key in keys_to_delete],
            stock__in=[key[2] for key in keys_to_delete],
            radif__in=[key[3] for key in keys_to_delete]
        ).delete()
        print(f"{len(keys_to_delete)} رکورد اضافی حذف شد.")


    # اجرای حلقه جایگزین سیگنال‌ها
    kardex_instances = list(Kardex.objects.prefetch_related('factor', 'kala', 'storage').all())
    updates = []
    factors = {factor.code: factor for factor in
               Factor.objects.filter(code__in=[k.code_factor for k in kardex_instances])}
    kalas = {kala.code: kala for kala in Kala.objects.filter(code__in=[k.code_kala for k in kardex_instances])}
    storages = {storage.code: storage for storage in
                Storagek.objects.filter(code__in=[k.warehousecode for k in kardex_instances])}

    for kardex in kardex_instances:
        factor = factors.get(kardex.code_factor)
        kala = kalas.get(kardex.code_kala)
        storage = storages.get(kardex.warehousecode)

        # بررسی تغییرات قبل از به‌روزرسانی
        updated = False
        if kardex.factor != factor:
            kardex.factor = factor
            updated = True

        if kardex.kala != kala:
            kardex.kala = kala
            updated = True

        if kardex.storage != storage:
            kardex.storage = storage
            updated = True

        # بررسی تغییر تاریخ
        if kardex.pdate:
            jalali_date = jdatetime.date(*map(int, kardex.pdate.split('/')))
            new_date = jalali_date.togregorian()
            if kardex.date != new_date:
                kardex.date = new_date
                updated = True

        if updated:
            updates.append(kardex)

    # ذخیره‌سازی دسته‌ای
    if updates:
        with transaction.atomic():
            Kardex.objects.bulk_update(updates,
                                       ['factor', 'kala', 'storage', 'warehousecode', 'code_kala', 'code_factor',
                                        'date'])
            print(f"{len(updates)} رکورد به‌روز رسانی سیگنال‌ها انجام شد.")

    t3 = time.time()
    print('جایگزین سیگنال انجام شد')

    # ثبت زمان‌ها و اطلاعات آخرین بروزرسانی در مدل Mtables
    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    up_time = t2 - t1
    sig_time = t3 - t2

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f"اتصال به دیتابیس: {db_time:.2f} ثانیه")
    print(f"عملیات اصلی آپدیت: {up_time:.2f} ثانیه")
    print(f"جایگزین سیگنال: {sig_time:.2f} ثانیه")

    cursor.execute("SELECT COUNT(*) FROM Kardex")
    row_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Kardex'")
    column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='Kardex').last()
    table.last_update_time = timezone.now()
    table.update_duration = total_time
    table.row_count = row_count
    table.column_count = column_count
    table.save()

    return redirect('/updatedb')







def UpdateKardex1(request):
    t0 = time.time()
    print('شروع آپدیت کاردکس----------------------------------------')

    conn = connect_to_mahak()  # فرض بر این است که این تابع اتصال به دیتابیس را برقرار می‌کند.
    cursor = conn.cursor()
    t1 = time.time()

    # خواندن داده‌ها از جدول Kardex
    cursor.execute("SELECT * FROM Kardex")
    mahakt_data = cursor.fetchall()

    # مرحله به‌روزرسانی یا ایجاد رکوردها
    updates = []
    for row in mahakt_data:
        pdate = row[0]
        code_kala = row[4]
        stock = row[12]
        radif = row[14]
        defaults = {
            'code_factor': row[6],
            'percode': row[1],
            'warehousecode': row[2],
            'mablaghsanad': row[3],
            'count': row[7],
            'averageprice': row[11],
        }

        # به‌روزرسانی یا ایجاد رکورد در مدل Kardex
        kardex_instance, created = Kardex.objects.update_or_create(
            pdate=pdate,
            code_kala=code_kala,
            stock=stock,
            radif=radif,
            defaults=defaults
        )

    t2 = time.time()
    print('آپدیت انجام شد')

    # اجرای حلقه جایگزین سیگنال‌ها
    kardex_instances = list(Kardex.objects.prefetch_related('factor', 'kala', 'storage').all())
    updates = []
    factors = {factor.code: factor for factor in
               Factor.objects.filter(code__in=[k.code_factor for k in kardex_instances])}
    kalas = {kala.code: kala for kala in Kala.objects.filter(code__in=[k.code_kala for k in kardex_instances])}
    storages = {storage.code: storage for storage in
                Storagek.objects.filter(code__in=[k.warehousecode for k in kardex_instances])}

    for kardex in kardex_instances:
        factor = factors.get(kardex.code_factor)
        kala = kalas.get(kardex.code_kala)
        storage = storages.get(kardex.warehousecode)

        # بررسی تغییرات قبل از به‌روزرسانی
        updated = False
        if kardex.factor != factor:
            kardex.factor = factor
            updated = True

        if kardex.kala != kala:
            kardex.kala = kala
            updated = True

        if kardex.storage != storage:
            kardex.storage = storage
            updated = True

        # بررسی تغییر تاریخ
        if kardex.pdate:
            jalali_date = jdatetime.date(*map(int, kardex.pdate.split('/')))
            new_date = jalali_date.togregorian()
            if kardex.date != new_date:
                kardex.date = new_date
                updated = True

        if updated:
            updates.append(kardex)

    # ذخیره‌سازی دسته‌ای
    if updates:
        with transaction.atomic():
            Kardex.objects.bulk_update(updates,
                                       ['factor', 'kala', 'storage', 'warehousecode', 'code_kala', 'code_factor',
                                        'date'])
            print(f"{len(updates)} رکورد به‌روز رسانی سیگنال‌ها انجام شد.")

    t3 = time.time()
    print('جایگزین سیگنال انجام شد')

    # ثبت زمان‌ها و اطلاعات آخرین بروزرسانی در مدل Mtables
    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    up_time = t2 - t1
    sig_time = t3 - t2

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f"اتصال به دیتابیس: {db_time:.2f} ثانیه")
    print(f"عملیات اصلی آپدیت: {up_time:.2f} ثانیه")
    print(f"جایگزین سیگنال: {sig_time:.2f} ثانیه")

    cursor.execute("SELECT COUNT(*) FROM Kardex")
    row_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Kardex'")
    column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='Kardex').last()
    table.last_update_time = timezone.now()
    table.update_duration = total_time
    table.row_count = row_count
    table.column_count = column_count
    table.save()

    return redirect('/updatedb')


def UpdateKardex2(request):
    t0 = time.time()
    print('شروع آپدیت کاردکس----------------------------------------')

    conn = connect_to_mahak()  # فرض بر این است که این تابع اتصال به دیتابیس را برقرار می‌کند.
    cursor = conn.cursor()
    t1 = time.time()

    cursor.execute("SELECT * FROM Kardex")
    mahakt_data = cursor.fetchall()
    print('خواندن از دیتابیس انجام شد')

    existing_in_mahak = {(row[0], row[4], row[12], row[14]) for row in mahakt_data}

    kardex_to_create = []
    kardex_to_update = []

    current_kardex = {(kardex.pdate, kardex.code_kala, kardex.stock, kardex.radif): kardex for kardex in
                      Kardex.objects.all()}

    for row in mahakt_data:
        pdate = row[0]
        code_kala = row[4]
        stock = row[12]
        radif = row[14]
        defaults = {
            'code_factor': row[6],
            'percode': row[1],
            'warehousecode': row[2],
            'mablaghsanad': row[3],
            'count': row[7],
            'averageprice': row[11],
        }

        if (pdate, code_kala, stock, radif) in current_kardex:
            kardex = current_kardex[(pdate, code_kala, stock, radif)]
            if any(getattr(kardex, attr) != value for attr, value in defaults.items()):
                for attr, value in defaults.items():
                    setattr(kardex, attr, value)
                kardex_to_update.append(kardex)
        else:
            kardex_to_create.append(Kardex(pdate=pdate, code_kala=code_kala, stock=stock, radif=radif, **defaults))

    # Bulk Create New Kardex Records
    if kardex_to_create:
        with transaction.atomic():
            Kardex.objects.bulk_create(kardex_to_create)
            print(f"{len(kardex_to_create)} رکورد جدید اضافه شد.")

    # Bulk Update Existing Kardex Records
    if kardex_to_update:
        with transaction.atomic():
            Kardex.objects.bulk_update(kardex_to_update,
                                       ['code_factor', 'percode', 'warehousecode', 'mablaghsanad', 'count',
                                        'averageprice'])
            print(f"{len(kardex_to_update)} رکورد به‌روزرسانی شد.")

    # Delete Obsolete Kardex Records
    with transaction.atomic():
        existing_keys = list(existing_in_mahak)

        for i in range(0, len(existing_keys), 500):  # حذف رکوردها در دسته‌های 500 تایی
            batch = existing_keys[i:i + 500]
            obsolete_kardex = Kardex.objects.exclude(
                Q(pdate__in=[k[0] for k in batch]) &
                Q(code_kala__in=[k[1] for k in batch]) &
                Q(stock__in=[k[2] for k in batch]) &
                Q(radif__in=[k[3] for k in batch])
            )
            if obsolete_kardex.exists():
                obsolete_kardex.delete()
                print(f"{obsolete_kardex.count()} رکورد قدیمی حذف شد.")

    t2 = time.time()
    print('آپدیت انجام شد')

    # اجرای حلقه جایگزین سیگنال‌ها
    kardex_instances = list(Kardex.objects.prefetch_related('factor', 'kala', 'storage').all())
    updates = []
    factors = {factor.code: factor for factor in
               Factor.objects.filter(code__in=[k.code_factor for k in kardex_instances])}
    kalas = {kala.code: kala for kala in Kala.objects.filter(code__in=[k.code_kala for k in kardex_instances])}
    storages = {storage.code: storage for storage in
                Storagek.objects.filter(code__in=[k.warehousecode for k in kardex_instances])}

    for kardex in kardex_instances:
        factor = factors.get(kardex.code_factor)
        kala = kalas.get(kardex.code_kala)
        storage = storages.get(kardex.warehousecode)

        # بررسی تغییرات قبل از به‌روزرسانی
        updated = False
        if kardex.factor != factor:
            kardex.factor = factor
            updated = True

        if kardex.kala != kala:
            kardex.kala = kala
            updated = True

        if kardex.storage != storage:
            kardex.storage = storage
            updated = True

        # بررسی تغییر تاریخ
        if kardex.pdate:
            jalali_date = jdatetime.date(*map(int, kardex.pdate.split('/')))
            new_date = jalali_date.togregorian()
            if kardex.date != new_date:
                kardex.date = new_date
                updated = True

        if updated:
            updates.append(kardex)

    # ذخیره‌سازی دسته‌ای
    if updates:
        with transaction.atomic():
            Kardex.objects.bulk_update(updates,
                                       ['factor', 'kala', 'storage', 'warehousecode', 'code_kala', 'code_factor',
                                        'date'])
            print(f"{len(updates)} رکورد به‌روز رسانی سیگنال‌ها انجام شد.")

    t3 = time.time()
    print('جایگزین سیگنال انجام شد')

    # ثبت زمان‌ها و اطلاعات آخرین بروزرسانی در مدل Mtables
    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    up_time = t2 - t1
    sig_time = t3 - t2

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f"اتصال به دیتابیس: {db_time:.2f} ثانیه")
    print(f"عملیات اصلی آپدیت: {up_time:.2f} ثانیه")
    print(f"جایگزین سیگنال: {sig_time:.2f} ثانیه")

    cursor.execute(f"SELECT COUNT(*) FROM Kardex")
    row_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Kardex'")
    column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='Kardex').last()
    table.last_update_time = timezone.now()
    table.update_duration = total_time
    table.row_count = row_count
    table.cloumn_count = column_count
    table.save()

    return redirect('/updatedb')


def UpdateFactorDetail(request):
    t0 = time.time()
    print('شروع آپدیت جزئیات فاکتور-------------------------------------------------')

    conn = connect_to_mahak()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Fact_Fo_Detail")
    mahakt_data = cursor.fetchall()

    t1 = time.time()
    print('اتصال به دیتابیس انجام شد', t1 - t0)

    existing_in_mahak = set((row[0], row[1]) for row in mahakt_data)

    up_start_time = time.time()
    updates = []
    factors = {factor.code: factor for factor in Factor.objects.all()}
    kalas = {kala.code: kala for kala in Kala.objects.all()}

    for row in mahakt_data:
        code_factor = row[0]
        radif = row[1]
        defaults = {
            'code_kala': row[3],
            'count': row[5],
            'mablagh_vahed': row[6],
            'mablagh_nahaee': row[29],
        }

        # پیدا کردن عامل و کالا
        factor = factors.get(code_factor)
        kala = kalas.get(defaults['code_kala'])

        # بروزرسانی یا ایجاد رکورد
        factor_detail, created = FactorDetaile.objects.update_or_create(
            code_factor=code_factor,
            radif=radif,
            defaults=defaults
        )

        # اینجا منطق اصلی سیگنال را جایگزین می‌کنیم
        if factor_detail.factor != factor:
            factor_detail.factor = factor
            print("فاکتور جدید تنظیم شد:", factor)

        if factor_detail.kala != kala:
            factor_detail.kala = kala
            print("کالا جدید تنظیم شد:", kala)

        updates.append(factor_detail)

        # ذخیره تغییرات در صورت وجود آپدیت‌ها
    if updates:
        with transaction.atomic():
            FactorDetaile.objects.bulk_update(updates, ['factor', 'kala'])

            # حذف رکوردهای غیرضروری
    FactorDetaile.objects.exclude(
        code_factor__in=[k[0] for k in existing_in_mahak],
        radif__in=[k[1] for k in existing_in_mahak]
    ).delete()

    t2 = time.time()
    print('آپدیت انجام شد', t2 - t1)

    tend = time.time()

    total_time = tend - t0
    db_time = t1 - t0
    up_time = t2 - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" اتصال به دیتابیس: {db_time:.2f} ثانیه")
    print(f" عملیات اصلی آپدیت: {up_time:.2f} ثانیه")

    cursor.execute(f"SELECT COUNT(*) FROM Fact_Fo_Detail")
    row_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Fact_Fo_Detail'")
    column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='Fact_Fo_Detail').last()
    table.last_update_time = timezone.now()
    table.update_duration = total_time
    table.row_count = row_count
    table.cloumn_count = column_count
    table.save()

    return redirect('/updatedb')


def UpdateKala(request):
    t0 = time.time()
    print('شروع آپدیت کالا---------------------------------------------------')

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


def UpdatePerson(request):
    t0 = time.time()
    print('شروع آپدیت افراد--------------------------------------------')

    conn = connect_to_mahak()
    cursor = conn.cursor()
    t1 = time.time()

    cursor.execute("SELECT * FROM PerInf")  # یا نام همه ستون‌ها را به جا column4, column7, column11 وارد کنید
    mahakt_data = cursor.fetchall()
    existing_in_mahak = {row[0] for row in mahakt_data}

    persons_to_create = []
    persons_to_update = []

    current_persons = {person.code: person for person in Person.objects.iterator()}

    for row in mahakt_data:
        code = row[0]
        defaults = {
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

        if code in current_persons:
            person = current_persons[code]
            if any(getattr(person, attr) != value for attr, value in defaults.items()):
                for attr, value in defaults.items():
                    setattr(person, attr, value)
                persons_to_update.append(person)
        else:
            persons_to_create.append(Person(code=code, **defaults))

    with transaction.atomic():
        # Bulk create new persons
        if persons_to_create:
            Person.objects.bulk_create(persons_to_create)

        # Bulk update existing persons
        if persons_to_update:
            Person.objects.bulk_update(persons_to_update,
                                       ['grpcode', 'name', 'lname', 'tel1', 'tel2', 'fax', 'mobile', 'address',
                                        'comment'])

        # Delete obsolete persons
        Person.objects.exclude(code__in=existing_in_mahak).delete()

    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" اتصال به دیتابیس:{db_time:.2f} ثانیه")
    print(f" زمان آپدیت جدول:{update_time:.2f} ثانیه")

    cursor.execute(f"SELECT COUNT(*) FROM PerInf")
    row_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'PerInf'")
    column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='PerInf').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    table.row_count = row_count
    table.cloumn_count = column_count
    table.save()

    return redirect('/updatedb')


def UpdateStorage(request):
    t0 = time.time()
    print('شروع آپدیت کالا---------------------------------------------------')

    conn = connect_to_mahak()
    cursor = conn.cursor()
    t1 = time.time()

    cursor.execute("SELECT code, name FROM Stores")
    mahakt_data = cursor.fetchall()
    existing_in_mahak = {row[0] for row in mahakt_data}

    storage_to_create = []
    storage_to_update = []

    current_storage = {storg.code: storg for storg in Storagek.objects.all()}

    for row in mahakt_data:
        code = row[0]
        name = row[1]

        if code in current_storage:
            if current_storage[code].name != name:
                current_storage[code].name = name
                storage_to_update.append(current_storage[code])
        else:
            storage_to_create.append(Storagek(code=code, name=name))

    # Bulk create new kalas
    Storagek.objects.bulk_create(storage_to_create)

    # Bulk update existing kalas
    Storagek.objects.bulk_update(storage_to_update, ['name'])

    # Delete obsolete kalas
    Storagek.objects.exclude(code__in=existing_in_mahak).delete()

    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" اتصال به دیتا بیس:{db_time:.2f} ثانیه")
    print(f" زمان آپدیت جدول:{update_time:.2f} ثانیه")

    cursor.execute(f"SELECT COUNT(*) FROM Stores")
    row_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Stores'")
    column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='Stores').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    table.row_count = row_count
    table.cloumn_count = column_count
    table.save()

    return redirect('/updatedb')


def Update_from_mahak(request):
    t0 = time.time()
    print('شروع آپدیت---------------------------------------')
    conn = connect_to_mahak()
    cursor = conn.cursor()
    print('cursor')
    print(cursor)
    Mtables.objects.create(name='test', row_count=12, cloumn_count=10)

    t1 = time.time()

    # # شناسایی کل جاول موجود
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    tables = cursor.fetchall()
    # خواندن نام جداول
    for table in tables:
        try:
            table_name = table[0]

            # شمارش تعداد سطرها
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]

            # شمارش تعداد ستون‌ها
            cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'")
            column_count = cursor.fetchone()[0]
            print("تا اینجا میام")

            Mtables.objects.update_or_create(
                name=table_name,
                defaults={
                    'row_count': row_count,
                    'cloumn_count': column_count
                }
            )
            print('ok ok ok ok ok ok ok ok table_name', table_name)

        except:
            print('error', table_name)
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                print('m1')
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                print('row_count', row_count)
                cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'")
                column_count = cursor.fetchone()[0]
                print('column_count', column_count)
            except:
                print('nononononoonon')

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
    #     if count>2:
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


# آپدیت افراد


def UpdateKalaGroupinfo(request):
    # مسیر فایل اکسل
    file_path = os.path.join(settings.BASE_DIR, 'temp', 'kala_group.xlsx')  # خواندن فایل اکسل با Pandas
    df = pd.read_excel(file_path)

    # پردازش داده‌ها و به‌روزرسانی مدل
    for index, row in df.iterrows():
        code = row['code']
        cat1 = row['cat1']
        cat2 = row['cat2']
        cat3 = row['cat3']
        contain = row['contain']
        not_contain = row['not_contain']

        # به‌روزرسانی یا ایجاد رکورد جدید
        KalaGroupinfo.objects.update_or_create(
            code=code,
            defaults={
                'cat1': cat1,
                'cat2': cat2,
                'cat3': cat3,
                'contain': contain,
                'not_contain': not_contain
            }
        )

    return redirect('/updatedb')


def update_categories_from_kala_groupinfo():
    # استخراج دسته‌بندی‌های یکتا از ستون‌های cat1, cat2, cat3
    kala_groups = KalaGroupinfo.objects.all()
    categories = []

    for group in kala_groups:
        if group.cat1:
            categories.append((group.cat1, 1, None))  # سطح 1، والد ندارد
        if group.cat2:
            categories.append((group.cat2, 2, group.cat1))  # سطح 2، والد cat1
        if group.cat3:
            categories.append((group.cat3, 3, group.cat2))  # سطح 3، والد cat2

    # حذف دسته‌بندی‌های تکراری
    unique_categories = list(dict.fromkeys(categories))

    # ایجاد یا به‌روزرسانی رکوردهای مدل Category
    with transaction.atomic():
        for name, level, parent_name in unique_categories:
            parent = None
            if parent_name:
                parent = Category.objects.filter(name=parent_name).first()

            Category.objects.update_or_create(
                name=name,
                defaults={'level': level, 'parent': parent}
            )


def CreateKalaGroup(request):
    update_categories_from_kala_groupinfo()
    return redirect('/updatedb')


def update_kala_categories():
    # گرفتن دسته‌بندی پیش‌فرض "تعیین نشده ۳"
    default_category = Category.objects.filter(name='تعیین نشده 3', level=3).first()

    # گرفتن تمامی کالاها
    kalas = Kala.objects.all()
    updates = []

    # پیمایش کالاها و تعیین دسته‌بندی مناسب برای هر کالا
    for kala in kalas:
        group_infos = KalaGroupinfo.objects.all()
        category_found = False  # متغیری برای پیگیری پیدا شدن دسته‌بندی

        for group in group_infos:
            if (group.contain in kala.name) and (group.not_contain not in kala.name):
                # پیدا کردن دسته‌بندی سطح 3
                category = Category.objects.filter(name=group.cat3, level=3).first()
                if category:
                    # تنظیم دسته‌بندی کالا
                    kala.category = category
                    updates.append(kala)
                    category_found = True
                break

        # اگر دسته‌بندی مناسب پیدا نشد، استفاده از دسته‌بندی پیش‌فرض
        if not category_found:
            kala.category = default_category
            updates.append(kala)

    # به‌روزرسانی تمامی کالاها به صورت گروهی
    if updates:
        with transaction.atomic():
            Kala.objects.bulk_update(updates, ['category'])


def UpdateKalaGroup(request):
    update_kala_categories()
    return redirect('/updatedb')


from django.db import transaction
from django.shortcuts import redirect
from collections import defaultdict




from django.shortcuts import redirect
from collections import defaultdict

from django.shortcuts import redirect
from collections import defaultdict

from django.shortcuts import redirect
from collections import defaultdict

from django.shortcuts import redirect
from collections import defaultdict

import time
from collections import defaultdict
from django.shortcuts import redirect
from .models import Kardex, Mojodi

import time
from collections import defaultdict
from django.db import transaction, connections
from django.db.models import Max
from django.shortcuts import redirect
from .models import Kardex, Mojodi

from django.db.models import Sum
from django.db.models import Sum
from django.shortcuts import redirect

import time
from collections import defaultdict
from django.db import transaction, connections
from django.db.models import Max
from django.shortcuts import redirect
from .models import Kardex, Mojodi


from django.db.models import Sum

from django.db.models import Sum
from django.shortcuts import redirect
import logging

logger = logging.getLogger(__name__)


import time
from django.db.models import Sum
from .models import Kardex, Mojodi



from django.db.models import F  # اضافه کردن این خط

from django.db.models import F  # اضافه کردن این خط


from django.db.models import F


import time
from django.db.models import Sum
from .models import Kardex, Mojodi
import time
from django.db import transaction
from .models import Kardex, Mojodi

import time
from django.db import transaction
from .models import Kardex, Mojodi

import time
from django.db import transaction
from .models import Kardex, Mojodi


def UpdateMojodi(request):
    start_time = time.time()

    # بارگذاری همه رکوردهای Kardex به صورت لیستی از تاپل‌ها
    all_kardex_list = list(Kardex.objects.all().values_list('warehousecode', 'code_kala'))

    # بارگذاری کادرکس‌ها که sync_mojodi آنها False است
    kardex_list2 = Kardex.objects.filter(sync_mojodi=False).values('warehousecode', 'code_kala').distinct()
    print(len(kardex_list2))

    kardex_list = [dict(t) for t in {tuple(d.items()) for d in kardex_list2}]
    print(f'Unique kardex count: {len(kardex_list)}')

    processed_items = {}
    jj = 1

    # بارگذاری تمام رکوردهای Kardex که sync_mojodi آنها False است
    all_kardex = Kardex.objects.filter(sync_mojodi=False).order_by('date', 'radif')
    print('Sample Kardex records:', [(k.date, k.code_kala, k.warehousecode, k.count) for k in
                                     all_kardex[:5]])  # نمایش 5 رکورد اول با ویژگی‌های بیشتر

    kardex_dict = {}
    for k in all_kardex:
        key = (k.code_kala, k.warehousecode)
        if key not in kardex_dict:
            kardex_dict[key] = []
        kardex_dict[key].append(k)

    for k in kardex_list:
        warehousecode = k['warehousecode']
        code_kala = k['code_kala']
        if (code_kala, warehousecode) in kardex_dict:
            kardex_entries = kardex_dict[(code_kala, warehousecode)]
            print(f'Kardex entries for ({code_kala}, {warehousecode}):', kardex_entries)  # نمایش رکوردهای هر کلید

            last_kardex_entry = kardex_entries[-1]
            last_kardex_entry2 = Kardex.objects.filter(code_kala=code_kala).order_by('date', 'radif').last()

            if last_kardex_entry2:
                total_count = sum(k.count for k in kardex_entries)
                processed_items[(code_kala, warehousecode)] = {
                    'storage': last_kardex_entry.storage,
                    'kala': last_kardex_entry.kala,
                    'total_stock': last_kardex_entry2.stock,
                    'averageprice': last_kardex_entry2.averageprice,
                    'arzesh': total_count * last_kardex_entry2.averageprice,
                    'stock': total_count,
                }
                for k in kardex_entries:
                    k.sync_mojodi = True
                    k.save()

        print(f'Processed item: {jj}, warehousecode: {warehousecode}, code_kala: {code_kala}')
        jj += 1

    print('Processed items:', processed_items)  # نمایش محتوای processed_items

    # بارگذاری رکوردهای موجود در Mojodi
    mojodi_objects = Mojodi.objects.filter(
        code_kala__in=[code_kala for (code_kala, warehousecode) in processed_items.keys()],
        warehousecode__in=[warehousecode for (code_kala, warehousecode) in processed_items.keys()]
    )

    print('Existing Mojodi records:', mojodi_objects.count())  # تعداد رکوردهای موجود

    # به‌روزرسانی رکوردها
    for mojodi in mojodi_objects:
        key = (mojodi.code_kala, mojodi.warehousecode)
        if key in processed_items:
            data = processed_items[key]
            mojodi.storage = data['storage']
            mojodi.kala = data['kala']
            mojodi.total_stock = data['total_stock']
            mojodi.averageprice = data['averageprice']
            mojodi.arzesh = data['arzesh']
            mojodi.stock = data['stock']

    # انجام bulk_update برای رکوردهای موجود
    Mojodi.objects.bulk_update(mojodi_objects, ['storage', 'kala', 'total_stock', 'averageprice', 'arzesh', 'stock'],
                               batch_size=1000)

    # اضافه کردن رکوردهای جدید
    existing_keys = {(mojodi.code_kala, mojodi.warehousecode) for mojodi in mojodi_objects}
    new_objects = []

    for (code_kala, warehousecode), data in processed_items.items():
        if (code_kala, warehousecode) not in existing_keys:
            new_objects.append(Mojodi(
                code_kala=code_kala,
                warehousecode=warehousecode,
                storage=data['storage'],
                kala=data['kala'],
                total_stock=data['total_stock'],
                averageprice=data['averageprice'],
                arzesh=data['arzesh'],
                stock=data['stock']
            ))

    # ذخیره‌سازی رکوردهای جدید به صورت دسته‌ای
    if new_objects:
        Mojodi.objects.bulk_create(new_objects, batch_size=1000)

    # حذف ردیف‌های اضافی در Mojodi
    keys_to_keep = set((k['code_kala'], k['warehousecode']) for k in all_kardex_list)

    Mojodi.objects.exclude(
        id__in=Mojodi.objects.filter(code_kala__in=[key[0] for key in keys_to_keep],
                                     warehousecode__in=[key[1] for key in keys_to_keep]).values_list('id', flat=True)
    ).delete()

    print('Update completed successfully.')

    end_time = time.time()
    print(f'Execution time: {end_time - start_time} seconds')

    return redirect('/updatedb')


def UpdateMojodidorost1(request):
    start_time = time.time()

    # بارگذاری کادرکس‌ها
    kardex_list2 = Kardex.objects.filter(sync_mojodi=False).values('warehousecode', 'code_kala')
    print(len(kardex_list2))

    kardex_list = [dict(t) for t in {tuple(d.items()) for d in kardex_list2}]

    print(f'Unique kardex count: {len(kardex_list)}')

    processed_items = {}
    jj = 1

    # بارگذاری تمام رکوردهای Kardex
    all_kardex = Kardex.objects.filter(
        code_kala__in=[item['code_kala'] for item in kardex_list],
        warehousecode__in=[item['warehousecode'] for item in kardex_list]
    ).order_by('date', 'radif')

    print('Sample Kardex records:', [(k.date, k.code_kala, k.warehousecode, k.count) for k in all_kardex[:5]])  # نمایش 5 رکورد اول با ویژگی‌های بیشتر

    kardex_dict = {}
    for k in all_kardex:
        key = (k.code_kala, k.warehousecode)
        if key not in kardex_dict:
            kardex_dict[key] = []
        kardex_dict[key].append(k)

    for k in kardex_list:
        warehousecode = k['warehousecode']
        code_kala = k['code_kala']
        if (code_kala, warehousecode) in kardex_dict:
            kardex_entries = kardex_dict[(code_kala, warehousecode)]
            print(f'Kardex entries for ({code_kala}, {warehousecode}):', kardex_entries)  # نمایش رکوردهای هر کلید

            last_kardex_entry = kardex_entries[-1]
            last_kardex_entry2 = Kardex.objects.filter(code_kala=code_kala).order_by('date', 'radif').last()

            if last_kardex_entry2:
                total_count = sum(k.count for k in kardex_entries)
                processed_items[(code_kala, warehousecode)] = {
                    'storage': last_kardex_entry.storage,
                    'kala': last_kardex_entry.kala,
                    'total_stock': last_kardex_entry2.stock,
                    'averageprice': last_kardex_entry2.averageprice,
                    'arzesh': total_count * last_kardex_entry2.averageprice,
                    'stock': total_count,
                }
        print(f'Processed item: {jj}, warehousecode: {warehousecode}, code_kala: {code_kala}')
        jj += 1

    print('Processed items:', processed_items)  # نمایش محتوای processed_items

    # بارگذاری رکوردهای موجود در Mojodi
    mojodi_objects = Mojodi.objects.filter(
        code_kala__in=[code_kala for (code_kala, warehousecode) in processed_items.keys()],
        warehousecode__in=[warehousecode for (code_kala, warehousecode) in processed_items.keys()]
    )

    print('Existing Mojodi records:', mojodi_objects.count())  # تعداد رکوردهای موجود

    # به‌روزرسانی رکوردها
    for mojodi in mojodi_objects:
        key = (mojodi.code_kala, mojodi.warehousecode)
        if key in processed_items:
            data = processed_items[key]
            mojodi.storage = data['storage']
            mojodi.kala = data['kala']
            mojodi.total_stock = data['total_stock']
            mojodi.averageprice = data['averageprice']
            mojodi.arzesh = data['arzesh']
            mojodi.stock = data['stock']

    # انجام bulk_update برای رکوردهای موجود
    Mojodi.objects.bulk_update(mojodi_objects, ['storage', 'kala', 'total_stock', 'averageprice', 'arzesh', 'stock'], batch_size=1000)

    # اضافه کردن رکوردهای جدید
    existing_keys = {(mojodi.code_kala, mojodi.warehousecode) for mojodi in mojodi_objects}
    new_objects = []

    for (code_kala, warehousecode), data in processed_items.items():
        if (code_kala, warehousecode) not in existing_keys:
            new_objects.append(Mojodi(
                code_kala=code_kala,
                warehousecode=warehousecode,
                storage=data['storage'],
                kala=data['kala'],
                total_stock=data['total_stock'],
                averageprice=data['averageprice'],
                arzesh=data['arzesh'],
                stock=data['stock']
            ))

    # ذخیره‌سازی رکوردهای جدید به صورت دسته‌ای
    if new_objects:
        Mojodi.objects.bulk_create(new_objects, batch_size=1000)

    # حذف ردیف‌های اضافی در Mojodi
    keys_to_keep = set((code_kala, warehousecode) for (code_kala, warehousecode) in processed_items.keys())

    Mojodi.objects.exclude(
        id__in=[item.id for item in Mojodi.objects.all() if (item.code_kala, item.warehousecode) in keys_to_keep]
    ).delete()

    print('Update completed successfully.')

    end_time = time.time()
    print(f'Execution time: {end_time - start_time} seconds')

    return redirect('/updatedb')


def UpdateMojodidorost(request):
    start_time = time.time()

    # بارگذاری کادرکس‌ها
    kardex_list2 = Kardex.objects.select_related('warehousecode', 'code_kala').order_by('date', 'radif').values('warehousecode', 'code_kala').distinct()
    kardex_list = [dict(t) for t in {tuple(d.items()) for d in kardex_list2}]

    print(f'Unique kardex count: {len(kardex_list)}')  # تعداد منحصر به فرد

    processed_items = {}
    jj = 1

    for item in kardex_list:
        warehousecode = item['warehousecode']
        code_kala = item['code_kala']

        # بارگذاری رکوردهای Kardex مرتبط
        kardex = Kardex.objects.filter(code_kala=code_kala, warehousecode=warehousecode).order_by('date', 'radif')
        last_kardex_entry = kardex.last()

        if last_kardex_entry:
            # بارگذاری ورودی آخر برای کالای مشخص
            last_kardex_entry2 = Kardex.objects.filter(code_kala=code_kala).order_by('date', 'radif').last()

            if last_kardex_entry2:
                total_count = kardex.aggregate(Sum('count'))['count__sum'] or 0  # جلوگیری از None
                processed_items[(code_kala, warehousecode)] = {
                    'storage': last_kardex_entry.storage,
                    'kala': last_kardex_entry.kala,
                    'total_stock': last_kardex_entry2.stock,
                    'averageprice': last_kardex_entry2.averageprice,
                    'arzesh': last_kardex_entry2.stock * last_kardex_entry2.averageprice,
                    'stock': total_count,
                }
        print(f'Processed item: {jj}, warehousecode: {warehousecode}, code_kala: {code_kala}')
        jj += 1

    # بارگذاری رکوردهای موجود در Mojodi
    mojodi_objects = Mojodi.objects.filter(
        code_kala__in=[code_kala for (code_kala, warehousecode) in processed_items.keys()],
        warehousecode__in=[warehousecode for (code_kala, warehousecode) in processed_items.keys()]
    )

    # به‌روزرسانی رکوردها
    for mojodi in mojodi_objects:
        key = (mojodi.code_kala, mojodi.warehousecode)
        if key in processed_items:
            data = processed_items[key]
            mojodi.storage = data['storage']
            mojodi.kala = data['kala']
            mojodi.total_stock = data['total_stock']
            mojodi.averageprice = data['averageprice']
            mojodi.arzesh = data['arzesh']
            mojodi.stock = data['stock']

    # انجام bulk_update برای رکوردهای موجود
    Mojodi.objects.bulk_update(mojodi_objects, ['storage', 'kala', 'total_stock', 'averageprice', 'arzesh', 'stock'], batch_size=1000)

    # اضافه کردن رکوردهای جدید
    existing_keys = {(mojodi.code_kala, mojodi.warehousecode) for mojodi in mojodi_objects}
    new_objects = []

    for (code_kala, warehousecode), data in processed_items.items():
        if (code_kala, warehousecode) not in existing_keys:
            new_objects.append(Mojodi(
                code_kala=code_kala,
                warehousecode=warehousecode,
                storage=data['storage'],
                kala=data['kala'],
                total_stock=data['total_stock'],
                averageprice=data['averageprice'],
                arzesh=data['arzesh'],
                stock=data['stock']
            ))

    # ذخیره‌سازی رکوردهای جدید به صورت دسته‌ای
    if new_objects:
        Mojodi.objects.bulk_create(new_objects, batch_size=1000)

    # # حذف ردیف‌های اضافی در Mojodi
    # code_kala_list = [code_kala for (code_kala, warehousecode) in processed_items.keys()]
    # warehousecode_list = [warehousecode for (code_kala, warehousecode) in processed_items.keys()]
    #
    # Mojodi.objects.exclude(
    #     code_kala__in=code_kala_list,
    #     warehousecode__in=warehousecode_list
    # ).delete()

    # حذف ردیف‌های اضافی در Mojodi
    keys_to_keep = set((code_kala, warehousecode) for (code_kala, warehousecode) in processed_items.keys())

    Mojodi.objects.exclude(
        id__in=[item.id for item in Mojodi.objects.all() if (item.code_kala, item.warehousecode) in keys_to_keep]
    ).delete()

    print('Update completed successfully.')

    end_time = time.time()
    print(f'Execution time: {end_time - start_time} seconds')

    return redirect('/updatedb')



def UpdateMojodi222222(request):
    start_time = time.time()  # زمان شروع تابع
    kardex_list = Kardex.objects.order_by('date', 'radif').select_related('storage', 'kala').values_list('storage',
                                                                                                            'kala',
                                                                                                               flat=False)


    for i in kardex_list:
        kardex=Kardex.objects.order_by('date', 'radif').filter(kala=i[1],warehousecode=i[0])
        total_count = kardex.aggregate(Sum('count'))['count__sum']
        Mojodi.objects.update_or_create(
            code_kala=i[1],
            warehousecode=i[0],
            defaults={
                'storage':kardex.last().storage,
                'kala':kardex.last().kala,
                'total_stock':Kardex.objects.order_by('date', 'radif').filter(kala=i[1]).last().stock,
                'averageprice':Kardex.objects.order_by('date', 'radif').filter(kala=i[1]).last().averageprice,
                'arzesh':(Kardex.objects.order_by('date', 'radif').filter(kala=i[1]).last().stock)*(Kardex.objects.order_by('date', 'radif').filter(kala=i[1]).last().averageprice),
                'stock':total_count,
            }
        )
        print(i)
    return redirect('/updatedb')



def UpdateMojodi111111(request):
    start_time = time.time()  # زمان شروع تابع

    # اطمینان از برقراری اتصال به پایگاه داده
    db_conn = connections['default']
    db_conn.ensure_connection()
    db_conn.connection.execute('PRAGMA busy_timeout = 30000')

    try:
        with transaction.atomic():  # استفاده از تراکنش برای جلوگیری از مشکلات قفل شدن
            # حذف تمامی رکوردهای Mojodi
            Mojodi.objects.all().delete()

            # بارگذاری داده‌ها از مدل Kardex
            kardex_entries = Kardex.objects.order_by('date', 'radif').select_related('storage', 'kala')

            # دیکشنری برای جمع‌آوری اطلاعات
            mojodi_data = defaultdict(lambda: {
                'stock': 0,
                'averageprice': 0,
                'storage': None,
                'kala': None,
                'warehousecode': None,
            })

            # جمع‌آوری اطلاعات از رکوردهای Kardex
            for entry in kardex_entries:
                key = (entry.code_kala, entry.warehousecode)  # کلید شامل کد کالا و کد انبار

                # جمع‌آوری موجودی (`stock`) بر اساس انبار
                mojodi_data[key]['stock'] += entry.count

                # بروزرسانی میانگین قیمت و اطلاعات دیگر
                mojodi_data[key]['averageprice'] = entry.averageprice
                mojodi_data[key]['storage'] = entry.storage
                mojodi_data[key]['kala'] = entry.kala
                mojodi_data[key]['warehousecode'] = entry.warehousecode

            # ایجاد یا به‌روزرسانی رکوردهای Mojodi
            for (code_kala, warehousecode), data in mojodi_data.items():
                # محاسبه arzesh
                arzesh = data['stock'] * data['averageprice'] if data['averageprice'] else 0

                Mojodi.objects.update_or_create(
                    code_kala=code_kala,
                    warehousecode=warehousecode,  # برای تفکیک بین کدهای انبار مختلف
                    defaults={
                        'storage': data['storage'],
                        'kala': data['kala'],
                        'stock': data['stock'],
                        'averageprice': data['averageprice'],
                        'arzesh': arzesh,
                        'total_stock': data['stock'],  # استفاده از stock برای موجودی کل
                    }
                )

            # محاسبه و بروزرسانی total_stock
            for code_kala, group in Kardex.objects.values('code_kala').annotate(latest_stock=Max('stock')):
                Mojodi.objects.filter(code_kala=code_kala).update(total_stock=group['latest_stock'])

        total_time = time.time() - start_time  # محاسبه زمان اجرا
        # چاپ زمان
        print(f"زمان کل اجرای تابع: {total_time:.2f} ثانیه")

    except Exception as e:
        print(f"خطا در اجرای تابع: {e}")

    # ریدایرکت به صفحه /updatedb
    return redirect('/updatedb')


def UpdateMojodi000000(request):
    # بارگذاری داده‌ها از مدل Kardex
    # kardex_entries = Kardex.objects.all().select_related('storage', 'kala')
    kardex_entries = Kardex.objects.order_by('date','radif').select_related('storage', 'kala')

    # دیکشنری برای جمع‌آوری اطلاعات
    mojodi_data = defaultdict(lambda: {
        'stock': 0,
        'averageprice': 0,
        'latest_date': None,
        'storage': None,
        'kala': None,
    })

    # تجزیه و تحلیل داده‌ها
    for entry in kardex_entries:
        key = (entry.code_kala, entry.warehousecode)

        # جمع‌آوری موجودی (`stock`)
        mojodi_data[key]['stock'] += entry.count

        # بروزرسانی میانگین قیمت و تاریخ آخرین رکورد
        if mojodi_data[key]['latest_date'] is None or entry.date > mojodi_data[key]['latest_date']:
            mojodi_data[key]['averageprice'] = entry.averageprice
            mojodi_data[key]['latest_date'] = entry.date
            mojodi_data[key]['storage'] = entry.storage  # ذخیره‌سازی اطلاعات
            mojodi_data[key]['kala'] = entry.kala  # ذخیره‌سازی اطلاعات

    # ایجاد یا به‌روزرسانی رکوردهای موجودی
    mojodi_instances = []
    for (code_kala, warehousecode), data in mojodi_data.items():
        arzesh = data['stock'] * data['averageprice'] if data['averageprice'] else 0

        mojodi_instance, created = Mojodi.objects.update_or_create(
            code_kala=code_kala,
            warehousecode=warehousecode,
            defaults={
                'storage': data['storage'],
                'kala': data['kala'],
                'stock': data['stock'],
                'averageprice': data['averageprice'],
                'arzesh': arzesh,
            }
        )
        mojodi_instances.append(mojodi_instance)

    # حذف رکوردهای اضافی در Mojodi
    current_mojodi_codes = set(mojodi_data.keys())
    mojodi_to_delete = Mojodi.objects.exclude(
        Q(code_kala__in=[code_kala for code_kala, _ in current_mojodi_codes]) &
        Q(warehousecode__in=[warehousecode for _, warehousecode in current_mojodi_codes])
    )

    mojodi_to_delete.delete()  # حذف رکوردها به صورت دسته‌ای

    # ریدایرکت به صفحه مورد نظر
    return redirect('/updatedb')

def UpdateMojodi0(request):
    # ابتدا تمام رکوردهای کاردکس را بر اساس تاریخ مرتب می‌کنیم
    # Mojodi.objects.all().delete()
    kardex_entries = Kardex.objects.all().order_by('date', 'radif')

    # دیکشنری برای ذخیره موجودی کالاها بر اساس انبار و کد کالا
    generated_mojodi = {}

    with transaction.atomic():
        for entry in kardex_entries:
            key = (entry.warehousecode, entry.code_kala)

            # اگر کلید (انبار و کد کالا) جدید است، آن را ایجاد می‌کنیم
            if key not in generated_mojodi:
                generated_mojodi[key] = {
                    'pdate': entry.pdate,
                    'date': entry.date,  # جدیدترین تاریخ از کاردکس
                    'warehousecode': entry.warehousecode,
                    'storage': entry.storage,
                    'code_kala': entry.code_kala,
                    'averageprice': entry.averageprice,
                    'stock': 0,
                    'arzesh': 0,
                    'kala': entry.kala,
                }
            else:
                # در صورتی که تاریخ جدیدتر از مقدار موجود باشد، آن را به‌روزرسانی کنید
                if entry.date > generated_mojodi[key]['date']:
                    generated_mojodi[key]['date'] = entry.date
                    generated_mojodi[key]['pdate'] = entry.pdate  # برای آخرین تاریخ
                    generated_mojodi[key]['averageprice'] = entry.averageprice

            # افزایش مقدار موجودی
            generated_mojodi[key]['stock'] += entry.count
            generated_mojodi[key]['arzesh'] = generated_mojodi[key]['stock'] * generated_mojodi[key]['averageprice']

        # حذف رکوردهای تکراری در مدل Mojodi
        for key in generated_mojodi.keys():
            warehouse_code, code_kala = key
            Mojodi.objects.filter(warehousecode=warehouse_code, code_kala=code_kala).exclude(
                pk__in=Mojodi.objects.filter(warehousecode=warehouse_code, code_kala=code_kala).values('pk')[
                       :1]).delete()

        # حالا دیکشنری را در مدل موجودی پر می‌کنیم
        for key, value in generated_mojodi.items():
            Mojodi.objects.update_or_create(
                warehousecode=value['warehousecode'],
                code_kala=value['code_kala'],
                defaults={
                    'pdate': value['pdate'],
                    'date': value['date'],
                    'storage': value['storage'],
                    'averageprice': value['averageprice'],
                    'stock': value['stock'],
                    'arzesh': value['arzesh'],
                    'kala': value['kala'],
                }
            )

    return redirect('/updatedb')


def UpdateMojodi1(request):
    # دریافت آخرین رکوردها بر مبنای ترکیب کالا و انبار
    latest_mojodi = (
        Kardex.objects
        .values('code_kala', 'warehousecode')
        .annotate(latest_date=Max('date'), highest_radif=Max('radif'))
    )

    # لیستی برای ذخیره رکوردهایی که باید به روزرسانی شوند
    updated_mojodis = []

    # ایجاد کوئری برای هر کالا و انبار به طور مستقل
    for record in latest_mojodi:
        kardex_records = Kardex.objects.filter(
            code_kala=record['code_kala'],
            warehousecode=record['warehousecode'],
            date=record['latest_date'],
            radif=record['highest_radif'],
            stock__gt=0  # فقط مواردی که موجودی بیشتر از صفر دارند
        ).select_related('kala')  # برای افزایش سرعت با پیش‌بارگذاری 'kala'

        for record in kardex_records:
            updated_mojodis.append(
                Mojodi(
                    code_kala=record.code_kala,
                    warehousecode=record.warehousecode,
                    pdate=record.pdate,
                    date=record.date,
                    storage=record.storage,
                    kala=record.kala,
                    averageprice=record.averageprice,
                    stock=record.stock,
                    arzesh=record.stock * record.averageprice
                )
            )

    with transaction.atomic():
        # استفاده از bulk_create برای افزودن رکوردها به پایگاه داده
        Mojodi.objects.bulk_create(updated_mojodis)

        # حذف رکوردهای غیرضروری
        updated_mojodi_ids = [mojodi.id for mojodi in updated_mojodis]
        Mojodi.objects.exclude(id__in=updated_mojodi_ids).delete()

    return redirect('/updatedb')


def UpdateMojodi2(request):
    # دریافت آخرین موجودی‌ها بر اساس کالا و انبار
    latest_mojodi = Kardex.objects.values('code_kala', 'warehousecode').annotate(
        latest_id=Max('id')
    ).values_list('latest_id', flat=True)

    # دریافت رکوردهای مربوط به آخرین موجودی و حذف موجودی‌های صفر
    kardex_records = Kardex.objects.order_by('-date', 'radif').filter(
        id__in=latest_mojodi,
        stock__gt=0
    ).select_related('kala')

    # لیستی برای شناسه‌های موجودی به‌روزرسانی شده
    updated_mojodi_ids = []

    # با استفاده از transaction برای بهینه‌سازی و جلوگیری از مشکلات همزمانی
    with transaction.atomic():
        for record in kardex_records:
            # به‌روزرسانی یا ایجاد رکورد جدید و افزودن شناسه رکورد به لیست
            mojodi, created = Mojodi.objects.update_or_create(
                code_kala=record.code_kala,
                warehousecode=record.warehousecode,
                defaults={
                    'pdate': record.pdate,
                    'date': record.date,
                    'storage': record.storage,
                    'kala': record.kala,
                    'averageprice': record.averageprice,
                    'stock': record.stock,
                    'arzesh': record.stock * record.averageprice
                }
            )
            updated_mojodi_ids.append(mojodi.id)

        # حذف رکوردهای اضافی که در لیست به‌روزرسانی نیستند
        Mojodi.objects.exclude(id__in=updated_mojodi_ids).delete()

    return redirect('/updatedb')





from django.shortcuts import HttpResponse
from .models import Kardex
def temp_compare_kardex_view(request):
    # اتصال به دیتابیس
    conn = connect_to_mahak()
    cursor = conn.cursor()

    # خواندن تمام رکوردها از دیتابیس
    cursor.execute("SELECT * FROM Kardex")
    db_records = cursor.fetchall()

    # بارگذاری رکوردهای موجود در مدل Kardex
    model_records = Kardex.objects.all()

    # بارگذاری کدهای کالا و تاریخ ها از رکوردهای مدل
    existing_kardex = {(k.code_kala, k.pdate): k for k in model_records}

    # متغیر برای ذخیره رکوردهای موجود در دیتابیس که در مدل نیستند
    missing_in_model = []

    # بررسی رکوردهای دیتابیس
    for row in db_records:
        # استفاده از ترکیب کد کالا و تاریخ به عنوان کلید
        key = (row[4], row[0])  # فرض بر این که index 0 تاریخ و index 4 کد کالا باشد

        if key not in existing_kardex:
            defaults = {
                'code_factor': row[6],
                'percode': row[1],
                'warehousecode': row[2],
                'mablaghsanad': row[3],
                'count': row[7],
                'averageprice': row[11],
            }
            missing_in_model.append((row, defaults))

            # بستن cursor و connection
    cursor.close()
    conn.close()

    # نمایش نتایج با استفاده از print
    print(f"تعداد رکوردهای موجود در دیتابیس: {len(db_records)}")
    print(f"تعداد رکوردهای یافت شده که در مدل Kardex ذخیره نشده‌اند: {len(missing_in_model)}\n")

    if missing_in_model:
        print("رکوردهای موجود در دیتابیس که در مدل Kardex ذخیره نشده‌اند:")
        for record, defaults in missing_in_model:
            print(f"pdate: {record[0]}, code_kala: {record[4]}, stock: {record[12]}, radif: {record[14]}")
            print(f"اطلاعات اضافی: {defaults}\n")
    else:
        print("هیچ رکوردی یافت نشد که در مدل ذخیره نشده باشد.")

    return HttpResponse("نتایج در ترمینال پرینت شد.", content_type="text/plain")
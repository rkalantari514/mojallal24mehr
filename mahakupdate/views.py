from django.conf import settings
from accounting.models import BedehiMoshtari
from custom_login.models import UserLog
from dashboard.models import MasterInfo
from dashboard.views import CreateReport, CreateMonthlyReport
from mahakupdate.models import WordCount, Person, KalaGroupinfo, Category, Sanad, SanadDetail, AccCoding, ChequesPay, \
    Bank, Loan, LoanDetil
from .models import FactorDetaile
import pandas as pd
from django.contrib.auth.decorators import login_required
from .models import Kala, Storagek
from .models import Factor
from .sendtogap import send_to_admin
import logging
logger = logging.getLogger(__name__)
from .models import Kardex, Mojodi
from datetime import timedelta
from django.shortcuts import HttpResponse
from .models import Kardex
from datetime import datetime
from django.utils import timezone
from decimal import Decimal, InvalidOperation
import jdatetime
from .models import ChequesRecieve, Mtables
from .models import MyCondition, SanadDetail
import time
from django.shortcuts import redirect
from django.db import transaction
from django.db.models import Sum
import pyodbc
from django.http import JsonResponse
from django.shortcuts import render
import os

# sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)


def connect_to_mahak():
    sn = os.getenv('COMPUTERNAME')
    print('sn')
    print(sn)
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year

    if acc_year==1403:
        connections = {
            'DESKTOP-ITU3EHV': ('DESKTOP-ITU3EHV\\MAHAK14', 'mahak'),
            'TECH_MANAGER': ('TECH_MANAGER\\RKALANTARI', 'mahak'),
            'DESKTOP-1ERPR1M': ('DESKTOP-1ERPR1M\\MAHAK', 'mahak'),
            # 'RP-MAHAK': ('Ac\\MAHAK', 'mahak'),
            'RP-MAHAK': ('Ac\\MAHAK', 'mahak_FY_1403')
        }

    if acc_year==1404:
        connections = {
            'DESKTOP-ITU3EHV': ('DESKTOP-ITU3EHV\\MAHAK14', 'mahak'),
            'TECH_MANAGER': ('TECH_MANAGER\\RKALANTARI', 'mahak'),
            'DESKTOP-1ERPR1M': ('DESKTOP-1ERPR1M\\MAHAK', 'mahak'),
            'RP-MAHAK': ('Ac\\MAHAK', 'mahak'),
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


def get_databases(request):
    try:
        conn = connect_to_mahak()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sys.databases WHERE state_desc = 'ONLINE'")

        databases = [row[0] for row in cursor.fetchall()]

        # برای حذف پایگاه داده 'mahak' از لیست
        databases = [db for db in databases if db != 'mahak']

        cursor.close()
        conn.close()

        return JsonResponse({'databases': databases})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    # صفحه عملیات آپدیت


@login_required(login_url='/login')
def Updatedb(request):
    tables = Mtables.objects.filter(in_use=True)
    url_mapping = {
        'Fact_Fo': 'update/factor',
        'GoodInf': 'update/kala',
        'Fact_Fo_Detail': 'update/factor-detail',
        'Kardex': 'update/kardex',
        'PerInf': 'update/person',
        'Stores': 'update/storage',
        'Sanad': 'update/sanad',
        'Sanad_detail': 'update/sanaddetail',
        'AccTotals': 'update/acccoding',
        'Cheques_Recieve': 'update/chequesrecieve',
        'Cheque_Pay': 'update/chequepay',
        'Bank': 'update/bank',
        'Loan': 'update/loan',
        'LoanDetail': 'update/loandetail',

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


def Updateall(request):
    now = datetime.now()
    work_time = [8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21]

    print(now.hour)
    print(now.weekday())
    # بررسی اینکه آیا ساعت بین 1 تا 2 بامداد است
    if now.hour in work_time:
        print(f' ساعت کاری: {now.hour}')
        send_to_admin(f' ساعت کاری: {now.hour}')
    # send_to_admin(f' لغو: {now.hour}')
        return redirect('/updatedb')

    else:
        print(f' ساعت غیر  کاری: {now.hour}')
        send_to_admin(f' ساعت غیر کاری: {now.hour}')

    if now.hour == 1:
        # بررسی اینکه آیا امروز دوشنبه است (0: دوشنبه، 6: یکشنبه)
        if now.weekday() == 1:
            send_to_admin('شروع آپدیت کل با ریست کاردکس')
            Kardex.objects.all().update(sync_mojodi=False)

    t0 = time.time()
    send_to_admin('شروع آپدیت کل')
    tables = Mtables.objects.filter(in_use=True).order_by('update_priority')

    # نگاشت نام جدول‌ها به توابع مربوطه
    view_map = {
        'Fact_Fo': UpdateFactor,
        'GoodInf': UpdateKala,
        'Fact_Fo_Detail': UpdateFactorDetail,
        'Kardex': UpdateKardex,
        'PerInf': UpdatePerson,
        'Stores': UpdateStorage,
        'Sanad': UpdateSanad,
        'Sanad_detail': UpdateSanadDetail,
        'AccTotals': UpdateAccCoding,
        'Cheques_Recieve': Cheques_Recieve,
        'Cheque_Pay': Cheque_Pay,
        'Bank': UpdateBank,
        'Loan': UpdateLoan,
        'LoanDetail': UpdateLoanDetail,
    }

    responses = []

    # پردازش بر اساس جداول
    for t in tables:
        if (timezone.now() - t.last_update_time).total_seconds() / 60 / t.update_period > 0.0005:
            response = view_map[t.name](request)
            responses.append(response.content)

            # آدرس‌های استاتیک
    static_urls = [
        '/update/updatekalagroupinfo',
        '/update/createkalagroup',
        '/update/updatekalagroup',
        '/update/mojodi',
        '/update/updatsmratio',
        '/update/updatesanadconditions',
        '/update/updatemycondition',
        '/createreport',
        '/create_monthly_report',
        'update/bedehimoshtari',
        'update/compleloan',
    ]
    # نگاشت آدرس‌های استاتیک به توابع
    static_view_map = {
        '/update/updatekalagroupinfo': UpdateKalaGroupinfo,
        '/update/createkalagroup': CreateKalaGroup,
        '/update/updatekalagroup': UpdateKalaGroup,
        '/update/mojodi': UpdateMojodi,
        '/update/updatsmratio': Update_Sales_Mojodi_Ratio,
        '/update/updatemycondition': UpdateMyCondition,
        '/update/updatesanadconditions': UpdateSanadConditions,
        '/createreport': CreateReport,
        '/create_monthly_report': CreateMonthlyReport,
        'update/bedehimoshtari': UpdateBedehiMoshtari,
        'update/compleloan': CompleLoan,
    }
    # چاپ تزئینی برای عیب یابی
    print(f"Request path: {request.path}")
    # پردازش آدرس‌های استاتیک
    for static_url in static_urls:
        # if request.path == static_url:
        response = static_view_map[static_url](request)
        responses.append(response.content)
        # اگر هیچ آدرس استاتیکی پردازش نشود
    if not responses:
        print("No static URLs were processed.")
        # بازگشت به /updatedb

    send_to_admin('پایان آپدیت کل')
    tend = time.time()
    total_time = tend - t0

    userlogcount = UserLog.objects.all().count()
    send_to_admin(f' مجموع تعداد بازدیدها: {userlogcount}')
    data1 = (f"زمان کل: {total_time:.2f} ثانیه")
    send_to_admin(data1)
    masterinfo = MasterInfo.objects.filter(is_active=True).last()
    masterinfo.last_update_time = timezone.now()
    masterinfo.save()
    return redirect('/updatedb')


# آپدیت فاکتور
def UpdateFactor(request):
    t0 = time.time()
    print('شروع آپدیت فاکتور--------------------------------------')
    conn = connect_to_mahak()  # تابع تخمینی برای اتصال به پایگاه داده Mahak
    cursor = conn.cursor()
    t1 = time.time()

    cursor.execute("SELECT * FROM Fact_Fo")
    mahakt_data = cursor.fetchall()
    existing_in_mahak = {row[0] for row in mahakt_data}

    factors_to_create = []
    factors_to_update = []

    # دریافت سال مالی فعال
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
    # فیلتر فاکتورها بر اساس سال مالی
    current_factors = {(factor.code, factor.acc_year): factor for factor in
                       Factor.objects.filter(acc_year=acc_year).iterator()}

    for row in mahakt_data:
        code = row[0]
        defaults = {
            'pdate': row[4],
            'mablagh_factor': Decimal(row[5]),
            'takhfif': Decimal(row[6]),
            'create_time': row[38],
            'darsad_takhfif': Decimal(row[44]),
            'acc_year': acc_year,  # سال مالی به اطلاعات پیش‌فرض اضافه می‌شود
        }

        # کلید ترکیبی شامل کد و سال مالی
        key = (code, acc_year)

        if key in current_factors:
            factor = current_factors[key]
            if any(
                    (isinstance(getattr(factor, attr), (int, float, Decimal)) and
                     Decimal(getattr(factor, attr)).quantize(Decimal('0.00')) != Decimal(value).quantize(
                                Decimal('0.00'))) or
                    (isinstance(getattr(factor, attr), str) and getattr(factor, attr) != str(value))
                    for attr, value in defaults.items()
            ):
                # پرینت مقادیر برای شناسایی
                for attr, value in defaults.items():
                    current_value = getattr(factor, attr)
                    print(f"Comparing {attr}: current_value={current_value}, new_value={value}")
                    if isinstance(current_value, (int, float, Decimal)):
                        print(
                            f"Rounded current_value={Decimal(current_value).quantize(Decimal('0.00'))}, new_value={Decimal(value).quantize(Decimal('0.00'))}")
                    else:
                        print(f"String comparison: current_value={current_value}, new_value={value}")

                for attr, value in defaults.items():
                    setattr(factor, attr, value)
                print('update.append')
                factors_to_update.append(factor)
        else:
            factors_to_create.append(Factor(code=code, **defaults))

    with transaction.atomic():
        if factors_to_create:
            Factor.objects.bulk_create(factors_to_create)
        if factors_to_update:
            Factor.objects.bulk_update(factors_to_update,
                                       ['pdate', 'mablagh_factor', 'takhfif', 'create_time', 'darsad_takhfif',
                                        'acc_year'])

            # پاکسازی فاکتورهایی که در پایگاه داده Mahak وجود ندارند
        Factor.objects.exclude(code__in=existing_in_mahak).filter(acc_year=acc_year).delete()

    tend = time.time()
    print(f"زمان کل: {tend - t0:.2f} ثانیه")
    print(f" اتصال به دیتابیس: {t1 - t0:.2f} ثانیه")
    print(f" زمان آپدیت جدول: {tend - t1:.2f} ثانیه")

    cursor.execute(f"SELECT COUNT(*) FROM Fact_Fo")
    row_count = cursor.fetchone()[0]
    cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Fact_Fo'")
    column_count = cursor.fetchone()[0]

    table = Mtables.objects.filter(name='Fact_Fo').last()
    table.last_update_time = timezone.now()
    table.update_duration = tend - t1
    table.row_count = row_count
    table.column_count = column_count
    table.save()

    return redirect('/updatedb')

# آپدیت کاردکس
def UpdateKardex(request):
    t0 = time.time()
    print('شروع آپدیت کاردکس----------------------------------------')
    conn = connect_to_mahak()
    cursor = conn.cursor()
    t1 = time.time()

    cursor.execute("SELECT * FROM Kardex")
    mahakt_data = cursor.fetchall()

    updates = []
    new_records = []

    # دریافت سال مالی فعال
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year

    existing_kardex = {
        (k.pdate, k.code_kala, k.stock, k.radif): k
        for k in Kardex.objects.filter(acc_year=acc_year)  # فقط رکوردهای سال مالی جاری
    }

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
            'ktype': row[5],
            'averageprice': row[11],
            'acc_year': acc_year,  # اضافه کردن سال مالی به اطلاعات پیش‌فرض
        }

        key = (pdate, code_kala, stock, radif)
        new_keys.add(key)

        if key in existing_kardex:
            kardex_instance = existing_kardex[key]
            updated = False
            for field, value in defaults.items():
                field_value = getattr(kardex_instance, field)

                if field_value is None or value is None:
                    continue

                if float(field_value) != float(value):
                    setattr(kardex_instance, field, value)
                    updated = True
            if updated:
                kardex_instance.sync_mojodi = False
                updates.append(kardex_instance)
        else:
            new_records.append(Kardex(
                pdate=pdate,
                code_kala=code_kala,
                stock=stock,
                radif=radif,
                sync_mojodi=False,
                **defaults
            ))

    # ذخیره رکوردهای به‌روزرسانی و جدید
    if updates or new_records:
        with transaction.atomic():
            Kardex.objects.bulk_update(
                updates,
                ['code_factor', 'percode', 'warehousecode', 'mablaghsanad', 'count',
                 'ktype', 'averageprice', 'sync_mojodi']  # سال مالی به صورت خودکار در پیش‌فرض‌ها لحاظ شده است
            )
            Kardex.objects.bulk_create(new_records)
            print(f"{len(updates) + len(new_records)} رکورد به‌روز رسانی یا ایجاد شد.")
            send_to_admin(f"{len(updates)} به روز رسانی کاردکس")
            send_to_admin(f"{len(new_records)} کاردکس جدید")

    t2 = time.time()
    print('آپدیت انجام شد')

    existing_keys = set(existing_kardex.keys())
    keys_to_delete = existing_keys - new_keys

    if keys_to_delete:
        for i in range(0, len(keys_to_delete), 900):  # تقسیم به دسته‌های حداکثر 900 عددی
            batch_keys = list(keys_to_delete)[i:i + 900]
            Kardex.objects.filter(
                pdate__in=[key[0] for key in batch_keys],
                code_kala__in=[key[1] for key in batch_keys],
                stock__in=[key[2] for key in batch_keys],
                radif__in=[key[3] for key in batch_keys],
                acc_year=acc_year  # فقط رکوردهای مربوط به سال مالی جاری را حذف کنید
            ).delete()
            print(f"{len(batch_keys)} رکورد اضافی حذف شد.")
            send_to_admin(f"{len(batch_keys)} کاردکس حذف")

    kardex_instances = list(Kardex.objects.prefetch_related('factor', 'kala', 'storage').filter(acc_year=acc_year))  # فقط رکوردهای سال مالی جاری
    updates = []


    # تقسیم کدها به دسته‌های کوچک‌تر
    factor_codes = [k.code_factor for k in kardex_instances]
    factors = {}

    for i in range(0, len(factor_codes), 900):
        batch_factor_codes = factor_codes[i:i + 900]
        factors.update({factor.code: factor for factor in Factor.objects.filter(code__in=batch_factor_codes)})

    kalas = {kala.code: kala for kala in Kala.objects.filter(code__in=[k.code_kala for k in kardex_instances])}
    storages = {storage.code: storage for storage in Storagek.objects.filter(code__in=[k.warehousecode for k in kardex_instances])}

    for kardex in kardex_instances:
        factor = factors.get(kardex.code_factor)
        kala = kalas.get(kardex.code_kala)
        storage = storages.get(kardex.warehousecode)

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

        if kardex.pdate:
            jalali_date = jdatetime.date(*map(int, kardex.pdate.split('/')))
            new_date = jalali_date.togregorian()
            if kardex.date != new_date:
                kardex.date = new_date
                updated = True

        if updated:
            updates.append(kardex)

    if updates:
        with transaction.atomic():
            Kardex.objects.bulk_update(
                updates,
                ['factor', 'kala', 'storage', 'warehousecode', 'code_kala', 'code_factor', 'date']
            )
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

    kardex_falt = Kardex.objects.filter(date='2107-09-01').last()
    if kardex_falt:
        kardex_falt.date = datetime.strptime('2024-08-31', '%Y-%m-%d').date()
        kardex_falt.pdate = '1403/06/10'
        kardex_falt.save()

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

    # دریافت سال مالی فعال
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
    up_start_time = time.time()
    updates = []

    # بارگذاری فاکتورها و کالاها
    factors = {factor.code: factor for factor in Factor.objects.filter(acc_year=acc_year)}
    kalas = {kala.code: kala for kala in Kala.objects.all()}

    for row in mahakt_data:
        code_factor = row[0]
        radif = row[1]
        defaults = {
            'code_kala': row[3],
            'count': row[5],
            'mablagh_vahed': row[6],
            'mablagh_nahaee': row[29],
            'acc_year': acc_year,  # سال مالی به اطلاعات پیش‌فرض اضافه می‌شود
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
    (FactorDetaile.objects.exclude(
        code_factor__in=[k[0] for k in existing_in_mahak],
        radif__in=[k[1] for k in existing_in_mahak],
        # acc_year=acc_year  # فقط رکوردهای مربوط به سال مالی جاری را حذف کنید
    ).filter(acc_year=acc_year).delete())

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
    send_to_admin('شروع آپدیت افراد')
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




def UpdateKalaGroupinfo(request):
    print('def UpdateKalaGroupinfo=========================================')
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
    print('def CreateKalaGroup==========================')
    update_categories_from_kala_groupinfo()
    return redirect('/updatedb')


def update_kala_categories():
    # گرفتن دسته‌بندی پیش‌فرض "تعیین نشده ۳"
    default_category = Category.objects.filter(name='تعیین نشده', level=3).first()
    # Kala.objects.update(category=None)
    # گرفتن تمامی کالاها
    kalas = Kala.objects.all()
    updates = []

    # پیمایش کالاها و تعیین دسته‌بندی مناسب برای هر کالا
    for kala in kalas:
        group_infos = KalaGroupinfo.objects.order_by('-id').all()
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
    print('def UpdateKalaGroup(request):================')
    update_kala_categories()
    return redirect('/updatedb')


def UpdateMojodi(request):
    # Kardex.objects.all().update(sync_mojodi=False)
    # return redirect('/updatedb')
    start_time = time.time()

    # دریافت لیست کد کالاهایی که sync_mojodi=False هستند
    false_kardex_list = list(Kardex.objects.filter(sync_mojodi=False).values_list('code_kala', flat=True))

    # بارگذاری رکوردهای Kardex مورد نظر فقط یک بار
    kardex_to_update = Kardex.objects.filter(code_kala__in=false_kardex_list)
    # kardex_to_update = Kardex.objects.filter(code_kala=70179)

    # بارگذاری کادرکس‌ها که sync_mojodi آنها True است
    kardex_list = kardex_to_update.values('warehousecode', 'code_kala').distinct()
    kardex_list = [dict(t) for t in {tuple(d.items()) for d in kardex_list}]

    processed_items = {}
    jj = 1

    # بارگذاری تمام رکوردهای Kardex که sync_mojodi آنها True است
    all_kardex = kardex_to_update.order_by('date', 'radif')

    # ایجاد دیکشنری برای تسهیل دسترسی
    kardex_dict = {}
    for k in all_kardex:
        key = (k.code_kala, k.warehousecode)
        if key not in kardex_dict:
            kardex_dict[key] = []
        kardex_dict[key].append(k)

        # محاسبه mojodi_roz و به روز رسانی موجودی Mojodi
    mojodi_updates = {}
    mojodi_updates_arzesh = {}
    for k in kardex_list:
        warehousecode = k['warehousecode']
        code_kala = k['code_kala']
        if (code_kala, warehousecode) in kardex_dict:
            kardex_entries = kardex_dict[(code_kala, warehousecode)]
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

                # محاسبه mojodi_roz

            last_stock = 0

            # تعیین تاریخ شروع و پایان

            try:
                kardex_entries = Kardex.objects.filter(code_kala=code_kala).order_by('date', 'radif')
                first_date = kardex_entries.first().date
                last_date = kardex_entries.last().date
                date_range = [first_date + timedelta(days=i) for i in range((last_date - first_date).days + 1)]
            except Exception as e:
                print(f"Error: {e}")
                continue

            mojodi_roz = 0
            mojodi_roz_arzesh = 0
            # ایجاد دیکشنری برای ذخیره ورودی‌های کاردکس بر اساس تاریخ
            daily_kardex_dict = {entry.date: entry for entry in kardex_entries}

            for single_date in date_range:
                daily_kardex_entry = daily_kardex_dict.get(single_date)

                if daily_kardex_entry:
                    last_stock = daily_kardex_entry.stock
                    last_averageprice = daily_kardex_entry.averageprice
                mojodi_roz += last_stock
                mojodi_roz_arzesh += last_stock * last_averageprice
                print(single_date, last_stock, mojodi_roz, mojodi_roz_arzesh)
                print('---------------')

            mojodi_updates[code_kala] = mojodi_roz
            mojodi_updates_arzesh[code_kala] = mojodi_roz_arzesh

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

            # به‌روزرسانی mojodi_roz
            if mojodi.code_kala in mojodi_updates:
                mojodi.mojodi_roz = mojodi_updates[mojodi.code_kala]
                mojodi.mojodi_roz_arzesh = mojodi_updates_arzesh[mojodi.code_kala]

                # انجام bulk_update برای رکوردهای موجود
    Mojodi.objects.bulk_update(mojodi_objects,
                               ['storage', 'kala', 'total_stock', 'averageprice', 'arzesh', 'stock', 'mojodi_roz',
                                'mojodi_roz_arzesh'],
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
                stock=data['stock'],
                mojodi_roz=mojodi_updates.get(code_kala, 0),  # Adding mojodi_roz for new records
                mojodi_roz_arzesh=mojodi_updates_arzesh.get(code_kala, 0)  # Adding mojodi_roz for new records
            ))

            # ذخیره‌سازی رکوردهای جدید به صورت دسته‌ای
    if new_objects:
        Mojodi.objects.bulk_create(new_objects, batch_size=1000)

        # حذف ردیف‌های اضافی در Mojodi
    keys_to_keep = set((k[1], k[0]) for k in Kardex.objects.values_list('warehousecode', 'code_kala'))

    Mojodi.objects.exclude(
        id__in=Mojodi.objects.filter(code_kala__in=[key[0] for key in keys_to_keep],
                                     warehousecode__in=[key[1] for key in keys_to_keep]).values_list('id', flat=True)
    ).delete()

    # به روز رسانی sync_mojodi به True
    kardex_to_update.update(sync_mojodi=True)

    print('Update completed successfully.')

    end_time = time.time()
    print(f'Execution time: {end_time - start_time} seconds')

    return redirect('/updatedb')


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


def Update_Sales_Mojodi_Ratio(request):
    start_time = time.time()  # زمان شروع تابع
    current_date = datetime.now().date()

    # دریافت یک لیست یکتا از کد کالاهای موجود در Kardex
    kala_code_in_kardex = Kardex.objects.values_list('code_kala', flat=True).distinct()

    # بارگذاری کالاها و موجودی‌ها به صورت دسته‌ای
    kalas = Kala.objects.filter(code__in=kala_code_in_kardex).prefetch_related('mojodi_set')

    print(f'کالاهای قابل پردازش: {kalas.count()}')

    # جمع آوری اطلاعات فروش به صورت دسته‌ای
    total_sales_data = (
        Kardex.objects.filter(code_kala__in=kalas.values_list('code', flat=True), ktype=1)
        .values('code_kala')
        .annotate(total=Sum('count'))
    )

    sales_dict = {item['code_kala']: -item['total'] for item in total_sales_data}

    # به‌روزرسانی فیلدهای مربوطه در مدل Kala
    for kala in kalas:
        print('------------------------')

        m_roz = kala.mojodi_set.last().mojodi_roz if kala.mojodi_set.exists() else 0
        total_sales = sales_dict.get(kala.code, 0)

        # محاسبه نسبت فروش به میانگین موجودی
        ratio = total_sales / m_roz * 100 if m_roz != 0 else 0

        # به‌روزرسانی نسبت فروش و کل فروش
        kala.s_m_ratio = ratio
        kala.total_sale = total_sales

        # ذخیره‌سازی به صورت دسته‌ای
    Kala.objects.bulk_update(kalas, ['s_m_ratio', 'total_sale'])

    total_time = time.time() - start_time  # محاسبه زمان اجرا
    print(f"زمان کل اجرای تابع: {total_time:.2f} ثانیه")

    return redirect('/updatedb')


def UpdateSanad(request):
    t0 = time.time()
    print('شروع آپدیت سند---------------------------------------------------')
    conn = connect_to_mahak()
    cursor = conn.cursor()
    t1 = time.time()

    cursor.execute("SELECT code, tarikh, sharh, SanadID FROM Sanad")
    mahakt_data = cursor.fetchall()
    existing_in_mahak = {int(row[0]) for row in mahakt_data}
    print('len(existing_in_mahak)')
    print(len(existing_in_mahak))
    # return redirect('/updatedb')
    sanads_to_create = []
    sanads_to_update = []

    # دریافت سال مالی جاری
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year

    # فقط رکوردهای سال مالی جاری را دریافت کنید
    current_sanads = {sanad.code: sanad for sanad in Sanad.objects.filter(acc_year=acc_year)}

    BATCH_SIZE = 1000  # تعیین اندازه دسته‌ها

    # پردازش داده‌های جدید
    for row in mahakt_data:
        code = int(row[0])
        print('code=',code)
        tarikh = row[1]
        sharh = row[2] if row[2] is not None else ''
        sanadid = row[3]

        if code in current_sanads:
            print('code in current_sanads')
            sanad = current_sanads[code]
            if sanad.tarikh != tarikh or sanad.sharh != sharh or sanad.sanadid != sanadid:
                sanad.tarikh = tarikh
                sanad.sharh = sharh
                sanad.sanadid = sanadid
                sanads_to_update.append(sanad)
        else:
            print('else')
            sanads_to_create.append(Sanad(code=code, tarikh=tarikh, sharh=sharh, sanadid=sanadid, acc_year=acc_year))

    print('to create',len(sanads_to_create))
    print('to update',len(sanads_to_update))
    # return redirect('/updatedb')

    # Bulk create new sanads
    Sanad.objects.bulk_create(sanads_to_create, batch_size=BATCH_SIZE)

    # Bulk update existing sanads
    Sanad.objects.bulk_update(sanads_to_update, ['tarikh', 'sharh', 'sanadid'], batch_size=BATCH_SIZE)

    # حذف رکوردهای اضافی
    sanads_to_delete = []

    # ابتدا شناسه‌های رکوردهای موجود را دریافت کنید
    current_sanad_codes = set(Sanad.objects.filter(acc_year=acc_year).values_list('code', flat=True))

    # حالا شروع به مقایسه با existing_in_mahak کنید
    for code in current_sanad_codes:
        if code not in existing_in_mahak:
            # استفاده از filter به جای get
            duplicate_records = Sanad.objects.filter(code=code, acc_year=acc_year)  # فیلتر بر اساس سال مالی
            if duplicate_records.exists():
                sanads_to_delete.append(duplicate_records.first().id)  # فقط اولین رکورد را نگه دارید

    # حذف به صورت دسته‌ای
    if sanads_to_delete:
        for i in range(0, len(sanads_to_delete), BATCH_SIZE):
            batch = sanads_to_delete[i:i + BATCH_SIZE]
            print(f"حذف شناسه‌ها: {batch}")  # برای بررسی، شناسه‌های حذف را چاپ کنید
            Sanad.objects.filter(id__in=batch).delete()
    else:
        print("هیچ رکوردی برای حذف وجود ندارد.")

    # محاسبه زمان اجرای کل
    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f"اتصال به دیتا بیس: {db_time:.2f} ثانیه")
    print(f"زمان آپدیت جدول: {update_time:.2f} ثانیه")

    cursor.execute("SELECT COUNT(*) FROM Sanad")  # محاسبه تعداد کل رکوردها
    row_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Sanad'")  # محاسبه تعداد ستون‌ها
    column_count = cursor.fetchone()[0]

    # به‌روزرسانی اطلاعات در جدول Mtables
    table = Mtables.objects.filter(name='Sanad').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    table.row_count = row_count
    table.column_count = column_count
    table.save()

    return redirect('/updatedb')


def UpdateSanadDetail(request):
    t0 = time.time()
    print('شروع آپدیت جزئیات سند---------------------------------------------------')
    # BATCH_SIZE = 1000  # تعیین اندازه دسته‌ها

    # # حذف رکوردها به صورت دسته‌ای
    # while True:
    #     # دریافت دسته‌ای از رکوردها
    #     queryset = SanadDetail.objects.filter(acc_year=1404)[:BATCH_SIZE]
    #
    #     # اگر هیچ رکوردی موجود نباشد، حلقه را ترک کنید
    #     if not queryset:
    #         break
    #
    #         # حذف رکوردها
    #     for sanad in queryset[:BATCH_SIZE]:
    #         sanad.delete()
    # return redirect('/updatedb')


    conn = connect_to_mahak()
    cursor = conn.cursor()
    t1 = time.time()

    # دریافت داده‌ها از دیتابیس خارجی
    cursor.execute(
        "SELECT code, radif, kol, moin, tafzili, sharh, bed, bes, Sanad_Code, Sanad_Type, "
        "Meghdar, SysComment, CurrAmount, UserCreated, VoucherDate FROM Sanad_detail")
    mahakt_data = cursor.fetchall()

    existing_in_mahak = {(int(row[0]), int(row[1])) for row in mahakt_data}
    print('تعداد رکوردهای موجود در Mahak:', len(existing_in_mahak))
    send_to_admin(f'sanad detile {len(existing_in_mahak)}')

    sanads_to_create = []
    sanads_to_update = []

    # دریافت سال مالی جاری
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year

    # فقط رکوردهای سال مالی جاری را دریافت کنید
    current_sanads = {(sanad.code, sanad.radif): sanad for sanad in SanadDetail.objects.filter(acc_year=acc_year)}

    BATCH_SIZE = 1000  # تعیین اندازه دسته‌ها

    # پردازش داده‌های جدید
    counter = 1
    for row in mahakt_data:
        print(counter)
        counter += 1
        code = int(row[0])
        radif = int(row[1])
        try:
            kol = int(row[2]) if row[2] is not None else 0
            moin = int(row[3]) if row[3] is not None else 0
            tafzili = int(row[4]) if row[4] is not None else 0
            sharh = row[5] if row[5] is not None else ''
            bed = Decimal(row[6]) if row[6] is not None else Decimal('0.0000000000')
            bes = Decimal(row[7]) if row[7] is not None else Decimal('0.0000000000')
            sanad_code = int(row[8]) if row[8] is not None else None
            sanad_type = int(row[9]) if row[9] is not None else None
            meghdar = Decimal(row[10]) if row[10] is not None else Decimal('0.0000000000')
            syscomment = row[11] if row[11] is not None else ''
            curramount = Decimal(row[12]) if row[12] is not None else Decimal('0.0000000000')
            usercreated = row[13] if row[13] is not None else ''
            voucher_date = row[14]  # تاریخ وچر از دیتابیس

        except (ValueError, InvalidOperation) as e:
            print(f"خطا در پردازش رکورد {row}: {e}. گذر از این رکورد.")
            continue  # این رکورد را بگذرانید

        # استفاده از ترکیب جدید برای کلید
        key = (code, radif)

        # بررسی رکوردهای فعلی با ترکیب جدید
        if key in current_sanads:
            sanad = current_sanads[key]
            print("------------------------------------")
            # بررسی کد مقایسه
            # if sanad.kol != kol:
            #     print(f'kol mismatch: {sanad.kol} != {kol}')
            # if sanad.moin != moin:
            #     print(f'moin mismatch: {sanad.moin} != {moin}')
            # if sanad.tafzili != tafzili:
            #     print(f'tafzili mismatch: {sanad.moin} ++ {sanad.tafzili} != {tafzili}')
            # if sanad.sharh != sharh:
            #     print(f'sharh mismatch: {sanad.sharh} != {sharh}')
            # if sanad.bed != bed:
            #     print(f'bed mismatch: {sanad.bed} != {bed}')
            # if sanad.bes != bes:
            #     print(f'bes mismatch: {sanad.bes} != {bes}')
            # if sanad.sanad_code != sanad_code:
            #     print(f'sanad_code mismatch: {sanad.sanad_code} != {sanad_code}')
            # if sanad.sanad_type != sanad_type:
            #     print(f'sanad_type mismatch: {sanad.sanad_type} != {sanad_type}')
            # if sanad.meghdar != meghdar:
            #     print(f'meghdar mismatch: {sanad.meghdar} != {meghdar}')
            # if sanad.syscomment != syscomment:
            #     print(f'syscomment mismatch: {sanad.syscomment} != {syscomment}')
            # if sanad.curramount != curramount:
            #     print(f'curramount mismatch: {sanad.curramount} != {curramount}')
            # if sanad.usercreated != usercreated:
            #     print(f'usercreated mismatch: {sanad.usercreated} != {usercreated}')
            # if sanad.tarikh != voucher_date:
            #     print(f'tarikh mismatch: {sanad.tarikh} != {voucher_date}')

            # حالا شرط اصلی
            # بررسی و بروزرسانی فیلدها
            if (sanad.kol != kol or sanad.moin != moin or
                    # sanad.tafzili != tafzili or
                    sanad.sharh != sharh or sanad.bed != bed or sanad.bes != bes or
                    sanad.sanad_code != sanad_code or sanad.sanad_type != sanad_type or
                    sanad.meghdar != meghdar or sanad.syscomment != syscomment or
                    sanad.curramount != curramount or sanad.usercreated != usercreated or
                    sanad.tarikh != voucher_date):
                sanad.kol = kol
                sanad.moin = moin
                sanad.tafzili = tafzili
                sanad.sharh = sharh
                sanad.bed = bed
                sanad.bes = bes
                sanad.sanad_code = sanad_code
                sanad.sanad_type = sanad_type
                sanad.meghdar = meghdar
                sanad.syscomment = syscomment
                sanad.curramount = curramount
                sanad.usercreated = usercreated
                sanad.tarikh = voucher_date  # بروزرسانی تاریخ شمسی
                sanad.is_analiz = False  # تنظیم is_analiz به False
                sanads_to_update.append(sanad)
        else:
            sanads_to_create.append(SanadDetail(
                code=code, radif=radif, kol=kol, moin=moin, tafzili=tafzili,
                sharh=sharh, bed=bed, bes=bes, sanad_code=sanad_code,
                sanad_type=sanad_type, meghdar=meghdar, syscomment=syscomment,
                curramount=curramount, usercreated=usercreated,
                tarikh=voucher_date,  # ذخیره تاریخ شمسی
                is_analiz=False,  # تنظیم is_analiz به False
                acc_year=acc_year  # اضافه کردن سال مالی
            ))

            # Bulk create new sanad details
    if sanads_to_create:
        print('شروع به ساخت')
        SanadDetail.objects.bulk_create(sanads_to_create, batch_size=BATCH_SIZE)


    # Bulk update existing sanad details
    if sanads_to_update:
        print('تعداد اسناد که آپدیت می‌شوند:', len(sanads_to_update))
        print('شروع به آپدیت')
    SanadDetail.objects.bulk_update(
        sanads_to_update,
        ['kol', 'moin', 'tafzili', 'sharh', 'bed', 'bes',
         'sanad_code', 'sanad_type', 'meghdar',
         'syscomment', 'curramount', 'usercreated', 'tarikh', 'is_analiz'],
        batch_size=BATCH_SIZE
    )



        # پس از بخش پردازش ثبت‌نام
    print('بررسی تاریخ')
    counter2 = 1


    # بارگذاری تمامی اسناد با تاریخ میلادی خالی
    empty_date_sanads = SanadDetail.objects.filter(date__isnull=True, acc_year=acc_year)

    # بروزرسانی تاریخ برای اسناد با تاریخ میلادی خالی
    for sanad in empty_date_sanads:
        if sanad.tarikh:  # فرض بر این است که tarikh مقداری دارد
            # تبدیل تاریخ شمسی به میلادی
            voucher_date = sanad.tarikh
            try:
                year, month, day = map(int, voucher_date.split('/'))
                gregorian_date = jdatetime.date(year, month, day).togregorian()
                miladi_date = gregorian_date.strftime('%Y-%m-%d')
                # پر کردن تاریخ میلادی
                sanad.date = miladi_date
            except Exception as e:
                print(f"خطا در تبدیل تاریخ برای {sanad.code}, {sanad.radif}: {e}")

    # پردازش اسناد جدید و پر کردن تاریخ میلادی
    for sanad in sanads_to_create:
        if sanad.tarikh:  # فرض بر این است که tarikh مقداری دارد
            try:
                year, month, day = map(int, sanad.tarikh.split('/'))
                gregorian_date = jdatetime.date(year, month, day).togregorian()
                miladi_date = gregorian_date.strftime('%Y-%m-%d')
                sanad.date = miladi_date  # پر کردن تاریخ میلادی برای اسناد جدید
            except Exception as e:
                print(f"خطا در تبدیل تاریخ برای سند جدید {sanad.code}, {sanad.radif}: {e}")

    # بروزرسانی تاریخ‌های میلادی در صورت نیاز
    if empty_date_sanads or sanads_to_create:
        print('شروع به آپدیت تاریخ‌های میلادی')
        SanadDetail.objects.bulk_update(list(empty_date_sanads) + sanads_to_create, ['date'], batch_size=BATCH_SIZE)

    # # حذف رکوردهای اضافی
    # sanads_to_delete = []
    # current_sanad_keys = {(sd.code, sd.radif) for sd in SanadDetail.objects.filter(acc_year=acc_year)}
    #
    # for key in current_sanad_keys:
    #     if key not in existing_in_mahak:
    #         sanads_to_delete.append(SanadDetail.objects.get(code=key[0], radif=key[1]).id)
    #
    # # حذف به صورت دسته‌ای
    # if sanads_to_delete:
    #     print('شروع به حذف')
    #     for i in range(0, len(sanads_to_delete), BATCH_SIZE):
    #         batch = sanads_to_delete[i:i + BATCH_SIZE]
    #         print(f"حذف شناسه‌ها: {batch}")  # برای بررسی، شناسه‌های حذف را چاپ کنید
    #         SanadDetail.objects.filter(id__in=batch).delete()
    # else:
    #     print("هیچ رکوردی برای حذف وجود ندارد.")
    #

    # حذف رکوردهای اضافی
    sanads_to_delete = []
    current_sanad_keys = {(sd.code, sd.radif) for sd in SanadDetail.objects.filter(acc_year=acc_year)}

    for key in current_sanad_keys:
        if key not in existing_in_mahak:
            sanads = SanadDetail.objects.filter(code=key[0], radif=key[1])
            if sanads.exists():
                sanads_to_delete.extend(sanad.id for sanad in sanads)

    # حذف به صورت دسته‌ای
    if sanads_to_delete:
        print('شروع به حذف')
        for i in range(0, len(sanads_to_delete), BATCH_SIZE):
            batch = sanads_to_delete[i:i + BATCH_SIZE]
            print(f"حذف شناسه‌ها: {batch}")  # برای بررسی، شناسه‌های حذف را چاپ کنید
            SanadDetail.objects.filter(id__in=batch).delete()
    else:
        print("هیچ رکوردی برای حذف وجود ندارد.")

    import re

    # بررسی اسناد دریافتنی
    # پر کردن cheque_id و به‌روزرسانی is_analiz
    to_analiz = SanadDetail.objects.filter(kol=101, is_analiz=False)

    # الگوی یافتن شناسه چک
    cheque_pattern = r'(چک\s*دريافتي\s*اول\s*دوره|چک\s*دريافتي|چک\s*خرج\s*شده|چک\s*درجريان\s*وصول|چک).*?\(([\d/]+)\)'

    # ایجاد یک لیست برای ذخیره تغییرات
    updates = []

    for t in to_analiz:
        syscomment = t.syscomment
        cheque_id = None  # مقدار پیش‌فرض برای cheque_id

        if syscomment:  # بررسی وجود مقدار در syscomment
            match = re.search(cheque_pattern, syscomment)
            if match:
                cheque_id = match.group(2)  # ذخیره شناسه چک

        # به‌روزرسانی ویژگی‌ها
        t.cheque_id = cheque_id
        t.is_analiz = cheque_id is not None  # اگر شناسه چک پیدا شده باشد، is_analiz را به True تغییر دهید

        # افزودن به لیست تغییرات
        updates.append(t)

    # ذخیره تغییرات در دیتابیس
    if updates:
        SanadDetail.objects.bulk_update(updates, ['cheque_id', 'is_analiz'], batch_size=BATCH_SIZE)

    # بررسی اسناد پرداختنی
    # پر کردن cheque_id و به‌روزرسانی is_analiz
    to_analiz = SanadDetail.objects.filter(kol=200, is_analiz=False)

    # الگوی یافتن شناسه چک
    cheque_pattern = r'(چک\s*|چک\s*پرداختي\s*اول\s*دوره|چک\s*پرداختي|عودت\s*چک\s*پرداختي).*?\((\d+)\)'
    updates = []

    for t in to_analiz:
        syscomment = t.syscomment
        cheque_id = None  # مقدار پیش‌فرض برای cheque_id

        if syscomment:  # بررسی وجود مقدار در syscomment
            match = re.search(cheque_pattern, syscomment)
            if match:
                cheque_id = match.group(2)  # ذخیره شناسه چک

        # به‌روزرسانی ویژگی‌ها
        t.cheque_id = cheque_id
        t.is_analiz = cheque_id is not None  # اگر شناسه چک پیدا شده باشد، is_analiz را به True تغییر دهید

        # افزودن به لیست تغییرات
        updates.append(t)

    # ذخیره تغییرات در دیتابیس
    if updates:
        SanadDetail.objects.bulk_update(updates, ['cheque_id', 'is_analiz'], batch_size=BATCH_SIZE)

    # محاسبه زمان اجرای کل
    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" زمان اتصال به دیتا بیس: {db_time:.2f} ثانیه")
    print(f" زمان آپدیت جدول: {update_time:.2f} ثانیه")

    cursor.execute("SELECT COUNT(*) FROM Sanad_detail")  # محاسبه تعداد کل رکوردها
    row_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Sanad_detail'")  # محاسبه تعداد ستون‌ها
    column_count = cursor.fetchone()[0]

    # به‌روزرسانی اطلاعات در جدول Mtables
    table = Mtables.objects.filter(name='Sanad_detail').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    table.row_count = row_count
    table.column_count = column_count
    table.save()

    return redirect('/updatedb')









def UpdateSanadDetail1403(request):
    t0 = time.time()
    print('شروع آپدیت جزئیات سند---------------------------------------------------')
    conn = connect_to_mahak()
    cursor = conn.cursor()
    t1 = time.time()

    # دریافت داده‌ها از دیتابیس خارجی
    cursor.execute(
        "SELECT code, radif, kol, moin, tafzili, sharh, bed, bes, Sanad_Code, Sanad_Type, "
        "Meghdar, SysComment, CurrAmount, UserCreated, VoucherDate FROM Sanad_detail")
    mahakt_data = cursor.fetchall()

    existing_in_mahak = {(int(row[0]), int(row[1])) for row in mahakt_data}
    print('تعداد رکوردهای موجود در Mahak:', len(existing_in_mahak))
    send_to_admin(f'sanad detile {len(existing_in_mahak)}')

    sanads_to_create = []
    sanads_to_update = []
    current_sanads = {(sanad.code, sanad.radif): sanad for sanad in SanadDetail.objects.all()}
    BATCH_SIZE = 1000  # تعیین اندازه دسته‌ها

    # پردازش داده‌های جدید
    counter = 1
    for row in mahakt_data:
        print(counter)
        counter += 1
        code = int(row[0])
        radif = int(row[1])
        try:
            kol = int(row[2]) if row[2] is not None else 0
            moin = int(row[3]) if row[3] is not None else 0
            tafzili = int(row[4]) if row[4] is not None else 0
            sharh = row[5] if row[5] is not None else ''
            bed = Decimal(row[6]) if row[6] is not None else Decimal('0.0000000000')
            bes = Decimal(row[7]) if row[7] is not None else Decimal('0.0000000000')
            sanad_code = int(row[8]) if row[8] is not None else None
            sanad_type = int(row[9]) if row[9] is not None else None
            meghdar = Decimal(row[10]) if row[10] is not None else Decimal('0.0000000000')
            syscomment = row[11] if row[11] is not None else ''
            curramount = Decimal(row[12]) if row[12] is not None else Decimal('0.0000000000')
            usercreated = row[13] if row[13] is not None else ''
            voucher_date = row[14]  # تاریخ وچر از دیتابیس

        except (ValueError, InvalidOperation) as e:
            print(f"خطا در پردازش رکورد {row}: {e}. گذر از این رکورد.")
            continue  # این رکورد را بگذرانید

        key = (code, radif)

        if key in current_sanads:
            sanad = current_sanads[key]
            # بررسی و بروزرسانی فیلدها
            if (sanad.kol != kol or sanad.moin != moin or sanad.tafzili != tafzili or
                    sanad.sharh != sharh or sanad.bed != bed or sanad.bes != bes or
                    sanad.sanad_code != sanad_code or sanad.sanad_type != sanad_type or
                    sanad.meghdar != meghdar or sanad.syscomment != syscomment or
                    sanad.curramount != curramount or sanad.usercreated != usercreated or
                    sanad.tarikh != voucher_date):
                sanad.kol = kol
                sanad.moin = moin
                sanad.tafzili = tafzili
                sanad.sharh = sharh
                sanad.bed = bed
                sanad.bes = bes
                sanad.sanad_code = sanad_code
                sanad.sanad_type = sanad_type
                sanad.meghdar = meghdar
                sanad.syscomment = syscomment
                sanad.curramount = curramount
                sanad.usercreated = usercreated
                sanad.tarikh = voucher_date  # بروزرسانی تاریخ شمسی
                sanad.is_analiz = False  # تنظیم is_analiz به False
                sanads_to_update.append(sanad)
        else:
            sanads_to_create.append(SanadDetail(
                code=code, radif=radif, kol=kol, moin=moin, tafzili=tafzili,
                sharh=sharh, bed=bed, bes=bes, sanad_code=sanad_code,
                sanad_type=sanad_type, meghdar=meghdar, syscomment=syscomment,
                curramount=curramount, usercreated=usercreated,
                tarikh=voucher_date,  # ذخیره تاریخ شمسی
                is_analiz=False  # تنظیم is_analiz به False
            ))

    # Bulk create new sanad details
    if sanads_to_create:
        print('شروع به ساخت')
        SanadDetail.objects.bulk_create(sanads_to_create, batch_size=BATCH_SIZE)

    # Bulk update existing sanad details
    if sanads_to_update:
        print('شروع به آپدیت')
        SanadDetail.objects.bulk_update(
            sanads_to_update,
            ['kol', 'moin', 'tafzili', 'sharh', 'bed', 'bes',
             'sanad_code', 'sanad_type', 'meghdar',
             'syscomment', 'curramount', 'usercreated', 'tarikh', 'is_analiz'],
            batch_size=BATCH_SIZE
        )

    # پس از بخش پردازش ثبت‌نام
    print('بررسی تاریخ')
    counter2 = 1

    print('تعداد اسناد که آپدیت می‌شوند:', len(sanads_to_update))
    # بارگذاری تمامی اسناد با تاریخ میلادی خالی
    empty_date_sanads = SanadDetail.objects.filter(date__isnull=True)

    # بروزرسانی تاریخ برای اسناد با تاریخ میلادی خالی
    for sanad in empty_date_sanads:
        if sanad.tarikh:  # فرض بر این است که tarikh مقداری دارد
            # تبدیل تاریخ شمسی به میلادی
            voucher_date = sanad.tarikh
            try:
                year, month, day = map(int, voucher_date.split('/'))
                gregorian_date = jdatetime.date(year, month, day).togregorian()
                miladi_date = gregorian_date.strftime('%Y-%m-%d')

                # پر کردن تاریخ میلادی
                sanad.date = miladi_date
            except Exception as e:
                print(f"خطا در تبدیل تاریخ برای {sanad.code}, {sanad.radif}: {e}")

    # پردازش اسناد جدید و پر کردن تاریخ میلادی
    for sanad in sanads_to_create:
        if sanad.tarikh:  # فرض بر این است که tarikh مقداری دارد
            try:
                year, month, day = map(int, sanad.tarikh.split('/'))
                gregorian_date = jdatetime.date(year, month, day).togregorian()
                miladi_date = gregorian_date.strftime('%Y-%m-%d')
                sanad.date = miladi_date  # پر کردن تاریخ میلادی برای اسناد جدید
            except Exception as e:
                print(f"خطا در تبدیل تاریخ برای سند جدید {sanad.code}, {sanad.radif}: {e}")

    # بروزرسانی تاریخ‌های میلادی در صورت نیاز
    if empty_date_sanads or sanads_to_create:
        print('شروع به آپدیت تاریخ‌های میلادی')
        SanadDetail.objects.bulk_update(list(empty_date_sanads) + sanads_to_create, ['date'], batch_size=BATCH_SIZE)

    # حذف رکوردهای اضافی
    sanads_to_delete = []
    current_sanad_keys = {(sd.code, sd.radif) for sd in SanadDetail.objects.all()}

    for key in current_sanad_keys:
        if key not in existing_in_mahak:
            sanads_to_delete.append(SanadDetail.objects.get(code=key[0], radif=key[1]).id)

    # حذف به صورت دسته‌ای
    if sanads_to_delete:
        print('شروع به حذف')
        for i in range(0, len(sanads_to_delete), BATCH_SIZE):
            batch = sanads_to_delete[i:i + BATCH_SIZE]
            print(f"حذف شناسه‌ها: {batch}")  # برای بررسی، شناسه‌های حذف را چاپ کنید
            SanadDetail.objects.filter(id__in=batch).delete()
    else:
        print("هیچ رکوردی برای حذف وجود ندارد.")

    import re

    # بررسی اسناد دریافتنی
    # پر کردن cheque_id و به‌روزرسانی is_analiz
    to_analiz = SanadDetail.objects.filter(kol=101, is_analiz=False)
    # to_analiz = SanadDetail.objects.filter(kol=101)

    # الگوی یافتن شناسه چک
    cheque_pattern = r'(چک\s*دريافتي\s*اول\s*دوره|چک\s*دريافتي|چک\s*خرج\s*شده|چک\s*درجريان\s*وصول|چک).*?\(([\d/]+)\)'

    # ایجاد یک لیست برای ذخیره تغییرات
    updates = []

    for t in to_analiz:
        syscomment = t.syscomment
        cheque_id = None  # مقدار پیش‌فرض برای cheque_id

        if syscomment:  # بررسی وجود مقدار در syscomment
            match = re.search(cheque_pattern, syscomment)
            if match:
                cheque_id = match.group(2)  # ذخیره شناسه چک

        # به‌روزرسانی ویژگی‌ها
        t.cheque_id = cheque_id
        t.is_analiz = cheque_id is not None  # اگر شناسه چک پیدا شده باشد، is_analiz را به True تغییر دهید

        # افزودن به لیست تغییرات
        updates.append(t)

        # ذخیره تغییرات در دیتابیس
    if updates:
        SanadDetail.objects.bulk_update(updates, ['cheque_id', 'is_analiz'], batch_size=BATCH_SIZE)

    # بررسی اسناد پرداختنی
    # پر کردن cheque_id و به‌روزرسانی is_analiz
    to_analiz = SanadDetail.objects.filter(kol=200, is_analiz=False)
    # to_analiz = SanadDetail.objects.filter(kol=101)

    # الگوی یافتن شناسه چک
    cheque_pattern = r'(چک\s*|چک\s*پرداختي\s*اول\s*دوره|چک\s*پرداختي|عودت\s*چک\s*پرداختي).*?\((\d+)\)'
    # ایجاد یک لیست برای ذخیره تغییرات
    updates = []

    for t in to_analiz:
        syscomment = t.syscomment
        cheque_id = None  # مقدار پیش‌فرض برای cheque_id

        if syscomment:  # بررسی وجود مقدار در syscomment
            match = re.search(cheque_pattern, syscomment)
            if match:
                cheque_id = match.group(2)  # ذخیره شناسه چک

        # به‌روزرسانی ویژگی‌ها
        t.cheque_id = cheque_id
        t.is_analiz = cheque_id is not None  # اگر شناسه چک پیدا شده باشد، is_analiz را به True تغییر دهید

        # افزودن به لیست تغییرات
        updates.append(t)

        # ذخیره تغییرات در دیتابیس
    if updates:
        SanadDetail.objects.bulk_update(updates, ['cheque_id', 'is_analiz'], batch_size=BATCH_SIZE)

    # محاسبه زمان اجرای کل
    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" زمان اتصال به دیتا بیس: {db_time:.2f} ثانیه")
    print(f" زمان آپدیت جدول: {update_time:.2f} ثانیه")

    cursor.execute("SELECT COUNT(*) FROM Sanad_detail")  # محاسبه تعداد کل رکوردها
    row_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Sanad_detail'")  # محاسبه تعداد ستون‌ها
    column_count = cursor.fetchone()[0]

    # به‌روزرسانی اطلاعات در جدول Mtables
    table = Mtables.objects.filter(name='Sanad_detail').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    table.row_count = row_count
    table.column_count = column_count
    table.save()

    return redirect('/updatedb')


def UpdateSanadDetail1(request):
    t0 = time.time()
    print('شروع آپدیت جزئیات سند---------------------------------------------------')
    conn = connect_to_mahak()
    cursor = conn.cursor()
    t1 = time.time()
    # دریافت داده‌ها از دیتابیس خارجی
    cursor.execute(
        "SELECT code, radif, kol, moin, tafzili, sharh, bed, bes, Sanad_Code, Sanad_Type, Meghdar, SysComment, CurrAmount, UserCreated FROM Sanad_detail")
    mahakt_data = cursor.fetchall()
    existing_in_mahak = {(int(row[0]), int(row[1])) for row in mahakt_data}
    print('تعداد رکوردهای موجود در Mahak:', len(existing_in_mahak))
    sanads_to_create = []
    sanads_to_update = []
    current_sanads = {(sanad.code, sanad.radif): sanad for sanad in SanadDetail.objects.all()}
    BATCH_SIZE = 1000  # تعیین اندازه دسته‌ها
    # پردازش داده‌های جدید
    for row in mahakt_data:
        code = int(row[0])
        radif = int(row[1])
        try:
            kol = int(row[2]) if row[2] is not None else 0
            moin = int(row[3]) if row[3] is not None else 0
            tafzili = int(row[4]) if row[4] is not None else 0
            sharh = row[5] if row[5] is not None else ''
            # اضافه کردن مدیریت بهتر بر روی Decimal
            try:
                bed = Decimal(row[6]) if row[6] is not None else Decimal('0.0000000000')
                bes = Decimal(row[7]) if row[7] is not None else Decimal('0.0000000000')
                sanad_code = int(row[8]) if row[8] is not None else None
                sanad_type = int(row[9]) if row[9] is not None else None
                meghdar = Decimal(row[10]) if row[10] is not None else Decimal('0.0000000000')
                syscomment = row[11] if row[11] is not None else ''
                curramount = Decimal(row[12]) if row[12] is not None else Decimal('0.0000000000')
                usercreated = row[13] if row[13] is not None else ''
            except (InvalidOperation, ValueError) as e:
                print(f"خطا در مقدارهای اعشاری برای رکورد {row}: {e}")
                continue  # این رکورد را بگذرانید

            # چاپ مقادیر برای بررسی
            # print(f"مقادیر پردازش شده: (code={code}, radif={radif}, kol={kol}, moin={moin}, tafzili={tafzili}, "
            #       f"sharh={sharh}, bed={bed}, bes={bes}, sanad_code={sanad_code}, "
            #       f"sanad_type={sanad_type}, meghdar={meghdar}, syscomment={syscomment}, "
            #       f"curramount={curramount}, usercreated={usercreated})")

        except (ValueError, InvalidOperation) as e:
            print(f"خطا در پردازش رکورد {row}: {e}. گذر از این رکورد.")
            continue  # این رکورد را بگذرانید

        key = (code, radif)

        if key in current_sanads:
            sanad = current_sanads[key]
            # بررسی و بروزرسانی فیلدها
            if (sanad.kol != kol or sanad.moin != moin or sanad.tafzili != tafzili or
                    sanad.sharh != sharh or sanad.bed != bed or sanad.bes != bes or
                    sanad.sanad_code != sanad_code or sanad.sanad_type != sanad_type or
                    sanad.meghdar != meghdar or sanad.syscomment != syscomment or
                    sanad.curramount != curramount or sanad.usercreated != usercreated):
                sanad.kol = kol
                sanad.moin = moin
                sanad.tafzili = tafzili
                sanad.sharh = sharh
                sanad.bed = bed
                sanad.bes = bes
                sanad.sanad_code = sanad_code
                sanad.sanad_type = sanad_type
                sanad.meghdar = meghdar
                sanad.syscomment = syscomment
                sanad.curramount = curramount
                sanad.usercreated = usercreated
                sanads_to_update.append(sanad)
        else:
            sanads_to_create.append(SanadDetail(
                code=code, radif=radif, kol=kol, moin=moin, tafzili=tafzili,
                sharh=sharh, bed=bed, bes=bes, sanad_code=sanad_code,
                sanad_type=sanad_type, meghdar=meghdar, syscomment=syscomment,
                curramount=curramount, usercreated=usercreated
            ))

            # Bulk create new sanad details
    if sanads_to_create:
        SanadDetail.objects.bulk_create(sanads_to_create, batch_size=BATCH_SIZE)

        # Bulk update existing sanad details
    if sanads_to_update:
        SanadDetail.objects.bulk_update(sanads_to_update,
                                        ['kol', 'moin', 'tafzili', 'sharh', 'bed', 'bes',
                                         'sanad_code', 'sanad_type', 'meghdar',
                                         'syscomment', 'curramount', 'usercreated'],
                                        batch_size=BATCH_SIZE)

        # حذف رکوردهای اضافی
    sanads_to_delete = []

    # ابتدا شناسه‌های رکوردهای موجود را دریافت کنید
    current_sanad_keys = {(sd.code, sd.radif) for sd in SanadDetail.objects.all()}

    # حالا شروع به مقایسه با existing_in_mahak کنید
    for key in current_sanad_keys:
        if key not in existing_in_mahak:
            sanads_to_delete.append(SanadDetail.objects.get(code=key[0], radif=key[1]).id)

            # حذف به صورت دسته‌ای
    if sanads_to_delete:
        for i in range(0, len(sanads_to_delete), BATCH_SIZE):
            batch = sanads_to_delete[i:i + BATCH_SIZE]
            print(f"حذف شناسه‌ها: {batch}")  # برای بررسی، شناسه‌های حذف را چاپ کنید
            SanadDetail.objects.filter(id__in=batch).delete()
    else:
        print("هیچ رکوردی برای حذف وجود ندارد.")

        # محاسبه زمان اجرای کل
    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" زمان اتصال به دیتا بیس: {db_time:.2f} ثانیه")
    print(f" زمان آپدیت جدول: {update_time:.2f} ثانیه")

    cursor.execute("SELECT COUNT(*) FROM Sanad_detail")  # محاسبه تعداد کل رکوردها
    row_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Sanad_detail'")  # محاسبه تعداد ستون‌ها
    column_count = cursor.fetchone()[0]

    # به‌روزرسانی اطلاعات در جدول Mtables
    table = Mtables.objects.filter(name='Sanad_detail').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    table.row_count = row_count
    table.column_count = column_count
    table.save()

    return redirect('/updatedb')



def UpdateAccCoding(request):
    t0 = time.time()
    print('شروع آپدیت کدینگ حسابداری (سطح کل) -----------------------')

    # اتصال به دیتابیس خارجی و خواندن داده‌های سطح 1 (کل)
    conn = connect_to_mahak()
    cursor = conn.cursor()
    t1 = time.time()

    cursor.execute("SELECT Code, Title FROM AccTotals WHERE Code IS NOT NULL AND Title IS NOT NULL")
    mahak_data = cursor.fetchall()
    existing_in_mahak = {int(row[0]) for row in mahak_data}
    print(f"تعداد رکوردهای موجود در دیتابیس خارجی: {len(existing_in_mahak)}")

    current_acc_codings = {acc.code: acc for acc in AccCoding.objects.filter(level=1)}

    acc_codings_to_create = []
    acc_codings_to_update = []
    acc_codings_to_delete = []

    BATCH_SIZE = 1000

    for row in mahak_data:
        code = int(row[0])
        name = row[1] if row[1] is not None else ''

        if code in current_acc_codings:
            acc_coding = current_acc_codings[code]
            if acc_coding.name != name:
                acc_coding.name = name
                acc_codings_to_update.append(acc_coding)
        else:
            acc_codings_to_create.append(AccCoding(code=code, name=name, level=1))

    AccCoding.objects.bulk_create(acc_codings_to_create, batch_size=BATCH_SIZE)
    AccCoding.objects.bulk_update(acc_codings_to_update, ['name'], batch_size=BATCH_SIZE)

    current_acc_coding_codes = set(AccCoding.objects.filter(level=1).values_list('code', flat=True))
    for code in current_acc_coding_codes:
        if code not in existing_in_mahak:
            acc_codings_to_delete.append(AccCoding.objects.get(code=code, level=1).id)

    if acc_codings_to_delete:
        for i in range(0, len(acc_codings_to_delete), BATCH_SIZE):
            batch = acc_codings_to_delete[i:i + BATCH_SIZE]
            print(f"حذف شناسه‌ها: {batch}")
            AccCoding.objects.filter(id__in=batch).delete()
    else:
        print("هیچ رکوردی برای حذف وجود ندارد.")

    print('شروع آپدیت کدینگ حسابداری (سطح معین) -----------------------')

    file_path = os.path.join(settings.BASE_DIR, 'temp', 'moin.xlsx')
    df = pd.read_excel(file_path)

    with transaction.atomic():
        for index, row in df.iterrows():
            kol = int(row['kol'])
            moin_code = int(row['moin_code'])
            moin_name = row['moin_name']
            # moin_name = 'ohgd'

            try:
                parent_acc = AccCoding.objects.get(code=kol, level=1)
                acc_coding, created = AccCoding.objects.update_or_create(
                    code=moin_code,
                    level=2,
                    parent=parent_acc,
                    defaults={'name': moin_name}
                )
                if created:
                    print(f"رکورد جدید {moin_name} با کد {moin_code} برای والد {kol} ایجاد شد.")
                else:
                    print(f"رکورد {moin_code} از قبل وجود دارد و به‌روزرسانی نمی‌شود.")
            except AccCoding.DoesNotExist:
                print(f"رکورد والد با کد {kol} یافت نشد.")
            except Exception as e:
                print(f"خطا در وارد کردن کد {moin_code}: {e}")

    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f"اتصال به دیتابیس: {db_time:.2f} ثانیه")
    print(f"زمان آپدیت جدول: {update_time:.2f} ثانیه")

    table = Mtables.objects.filter(name='AccTotals').last()
    if table:
        table.last_update_time = timezone.now()
        table.update_duration = update_time
        table.row_count = AccCoding.objects.count()
        table.column_count = 4
        table.save()
    else:
        print("جدول Mtables برای AccCoding یافت نشد.")

    return redirect('/updatedb')







def safe_int(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0  # یا هر مقدار پیش‌فرض دیگری که مناسب باشد.



def UpdateBank(request):
    t0 = time.time()
    print('شروع آپدیت بانک‌ها---------------------------------------------------')
    conn = connect_to_mahak()
    cursor = conn.cursor()
    t1 = time.time()

    # گرفتن تمامی داده‌ها از دیتابیس خارجی
    cursor.execute(
        "SELECT [Code], [Name], [shobe], [sh_h], [type], [mogodi], [FirstAmount] FROM Bank"
    )
    mahak_data = cursor.fetchall()

    existing_in_mahak = {int(row[0]) for row in mahak_data}
    print('تعداد رکوردهای موجود در Mahak:', len(existing_in_mahak))

    banks_to_create = []
    banks_to_update = []
    current_banks = {bank.code: bank for bank in Bank.objects.all()}
    BATCH_SIZE = 1000  # تعیین اندازه دسته‌ها

    for counter, row in enumerate(mahak_data, start=1):
        print(counter)

        code = int(row[0])
        name = row[1] or ''
        shobe = row[2] or ''
        sh_h = row[3] or ''
        type_h = row[4] or ''
        mogodi = Decimal(row[5] or '0.00')
        firstamount = Decimal(row[6] or '0.00')

        if code in current_banks:
            bank = current_banks[code]
            if any([
                bank.name != name,
                bank.shobe != shobe,
                bank.sh_h != sh_h,
                bank.type_h != type_h,
                bank.mogodi != mogodi,
                bank.firstamount != firstamount
            ]):
                bank.name = name
                bank.shobe = shobe
                bank.sh_h = sh_h
                bank.type_h = type_h
                bank.mogodi = mogodi
                bank.firstamount = firstamount
                banks_to_update.append(bank)
        else:
            banks_to_create.append(Bank(
                code=code, name=name, shobe=shobe,
                sh_h=sh_h, type_h=type_h, mogodi=mogodi,
                firstamount=firstamount
            ))

    if banks_to_create:
        print('شروع به ساخت بانک‌های جدید')
        Bank.objects.bulk_create(banks_to_create, batch_size=BATCH_SIZE)

    if banks_to_update:
        print('شروع به آپدیت بانک‌های موجود')
        Bank.objects.bulk_update(
            banks_to_update,
            ['name', 'shobe', 'sh_h', 'type_h', 'mogodi', 'firstamount'],
            batch_size=BATCH_SIZE
        )

    ids_in_external_db = {int(row[0]) for row in mahak_data}
    ids_in_django_db = {bank.code for bank in current_banks.values()}
    ids_to_delete = ids_in_django_db - ids_in_external_db

    if ids_to_delete:
        Bank.objects.filter(code__in=ids_to_delete).delete()
        print(f"رکوردهای حذف‌شده: {len(ids_to_delete)} رکورد حذف شد.")

    # تعریف نگاشت نام‌های فارسی به انگلیسی
    bank_names_mapping = {
        'ملل': 'melal.png',
        'مهر': 'mehr.png',
        'تجارت': 'tejarat.png',
        'رفاه': 'refah.png',
        'صادرات': 'saderat.png',
        'ملت': 'melat.png',
        'ملي': 'melli.png',
        'انصار': 'ansar.png',
        'عسکريه': 'askariye.png',
        'سپه': 'sepah.png',
        'شهر': 'shahr.png',
        'متين': 'matin.png',
        'مسکن': 'maskan.png',
        'نور': 'noor.png',
        'پارسيان': 'parsian.png',
        'پست': 'post.png'
    }

    iran_banks = (
        'ملل', 'مهر', 'تجارت', 'رفاه', 'صادرات', 'ملت', 'ملي', 'انصار',
        'عسکريه', 'سپه', 'شهر', 'متين', 'مسکن', 'نور', 'پارسيان', 'پست'
    )

    banks_to_update_bank_name = []
    for bank in Bank.objects.all():
        bank_found = False
        for n in iran_banks:
            if n in bank.name:
                bank.bank_name = n
                bank.bank_logo = bank_names_mapping.get(n, "unknown")
                banks_to_update_bank_name.append(bank)
                bank_found = True
                break
        if not bank_found:
            if bank.bank_name != "نامعلوم":
                bank.bank_name = "نامعلوم"
                bank.bank_logo = "unknown.png"
                banks_to_update_bank_name.append(bank)

    if banks_to_update_bank_name:
        Bank.objects.bulk_update(banks_to_update_bank_name, ['bank_name', 'bank_logo'], batch_size=BATCH_SIZE)

    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    table = Mtables.objects.filter(name='Bank').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    cursor.execute("SELECT COUNT(*) FROM Bank")
    row_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Bank'")
    column_count = cursor.fetchone()[0]
    table.row_count = row_count
    table.column_count = column_count
    table.save()

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f"زمان اتصال به دیتابیس: {db_time:.2f} ثانیه")
    print(f"زمان آپدیت جدول: {update_time:.2f} ثانیه")

    return redirect('/updatedb')


def Cheques_Recieve(request):
    t0 = time.time()
    print('شروع آپدیت چک‌ها---------------------------------------------------')
    conn = connect_to_mahak()
    cursor = conn.cursor()
    t1 = time.time()

    # گرفتن داده‌ها از دیتابیس خارجی
    cursor.execute(
        "SELECT [ID], [ChequeID], [ChequeRow], [IssuanceDate], [ChequeDate], "
        "[Cost], [BankName], [BankBranch], [AccountID], [Description], [Status], [PerCode] "
        "FROM Cheques_Recieve"
    )
    mahak_data = cursor.fetchall()

    existing_in_mahak = {int(row[0]) for row in mahak_data}
    print('تعداد رکوردهای موجود در Mahak:', len(existing_in_mahak))

    cheques_to_create = []
    cheques_to_update = []
    current_cheques = {cheque.id_mahak: cheque for cheque in ChequesRecieve.objects.all()}
    BATCH_SIZE = 1000  # تعیین اندازه دسته‌ها

    # تعریف نگاشت نام‌های فارسی به انگلیسی
    bank_names_mapping = {
        'آينده': 'ayandeh.png',
        'اقتصاد نوين': 'eghtesad-novin.png',
        'ايران زمين': 'iran-zamin.png',
        'اينده': 'ayandeh.png',
        'تجارت': 'tejarat.png',
        'توسعه تعاون': 'tosee-taavon.png',
        'توسعه صادرات': 'tosee-saderat.png',
        'توسعه و تعاون': 'tosee-va-taavon.png',
        'دي': 'day.png',
        'رسالت': 'resalat.png',
        'رفاه': 'refah.png',
        'سامان': 'saman.png',
        'سرمايه': 'sarmayeh.png',
        'سينا': 'sina.png',
        'سپه': 'sepah.png',
        'شهر': 'shahr.png',
        'صادرات': 'saderat.png',
        'مسکن': 'maskan.png',
        'ملت': 'melat.png',
        'ملل': 'melal.png',
        'ملي': 'melli.png',
        'مهر': 'mehr.png',
        'پارسيان': 'parsian.png',
        'پاسارگاد': 'pasargad.png',
        'پست': 'post.png',
        'کشاورزي': 'keshavarzi.png',
        'گردشگري': 'gardeshgari.png'
    }
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
    # بارگذاری SanadDetail ها به یک دیکشنری
    sanad_details = SanadDetail.objects.filter(cheque_id__in=[row[1] for row in mahak_data], kol=101,
                                               is_active=True,acc_year=acc_year).order_by('date', 'code', 'radif')
    sanad_dict = {}
    for sd in sanad_details:
        if sd.cheque_id not in sanad_dict:
            sanad_dict[sd.cheque_id] = []
        sanad_dict[sd.cheque_id].append(sd)

    for counter, row in enumerate(mahak_data, start=1):
        print(counter)
        id_mahak = int(row[0])
        cheque_id_str = row[1]
        cheque_row = int(row[2])
        issuance_tarik = row[3]
        cheque_tarik = row[4]
        cost = Decimal(row[5] or '0.00')
        bank_name = (row[6] or '').strip()  # حذف اسپیس‌های اضافی
        bank_branch = row[7] or ''
        account_id = safe_int(row[8])  # استفاده از تابع کمکی برای تبدیل عدد
        description = row[9] or ''
        status = row[10] or '0'
        per_code = row[11] or '0'

        # تبدیل تاریخ
        try:
            issuance_date = jdatetime.date(
                *map(int, issuance_tarik.split('/'))).togregorian() if issuance_tarik else None
            cheque_date = jdatetime.date(*map(int, cheque_tarik.split('/'))).togregorian() if cheque_tarik else None
        except Exception as e:
            print(f"خطا در تعیین تاریخ: {e}")
            continue

        # محاسبه مانده کل چک
        total_bes = sum(sd.bes for sd in sanad_dict.get(cheque_id_str, []))
        total_bed = sum(sd.bed for sd in sanad_dict.get(cheque_id_str, []))
        total_mandeh = total_bes - total_bed

        # دریافت آخرین جزئیات سند
        last_sanad = sanad_dict.get(cheque_id_str, [])[-1] if sanad_dict.get(cheque_id_str) else None

        # تنظیم bank_logo با استفاده از جستجو در دیکشنری
        bank_logo = "unknown.png"
        for key, value in bank_names_mapping.items():
            if key in bank_name:
                bank_logo = value
                break

        if id_mahak in current_cheques:
            cheque = current_cheques[id_mahak]
            if (cheque.cheque_id != cheque_id_str or cheque.cheque_row != cheque_row or
                    cheque.issuance_tarik != issuance_tarik or cheque.issuance_date != issuance_date or
                    cheque.cheque_tarik != cheque_tarik or cheque.cheque_date != cheque_date or
                    cheque.cost != cost or cheque.bank_name != bank_name or
                    cheque.bank_branch != bank_branch or cheque.account_id != account_id or
                    cheque.description != description or cheque.status != status or
                    cheque.per_code != per_code or cheque.total_mandeh != total_mandeh or
                    cheque.last_sanad_detaile != last_sanad or cheque.bank_logo != bank_logo):
                cheque.cheque_id = cheque_id_str
                cheque.cheque_row = cheque_row
                cheque.issuance_tarik = issuance_tarik
                cheque.issuance_date = issuance_date
                cheque.cheque_tarik = cheque_tarik
                cheque.cheque_date = cheque_date
                cheque.cost = cost
                cheque.bank_name = bank_name
                cheque.bank_branch = bank_branch
                cheque.account_id = account_id
                cheque.description = description
                cheque.status = status
                cheque.per_code = per_code
                cheque.total_mandeh = total_mandeh
                cheque.last_sanad_detaile = last_sanad
                cheque.bank_logo = bank_logo
                cheques_to_update.append(cheque)
        else:
            cheques_to_create.append(ChequesRecieve(
                id_mahak=id_mahak, cheque_id=cheque_id_str, cheque_row=cheque_row,
                issuance_tarik=issuance_tarik, issuance_date=issuance_date,
                cheque_tarik=cheque_tarik, cheque_date=cheque_date, cost=cost,
                bank_name=bank_name, bank_branch=bank_branch, account_id=account_id,
                description=description, status=status, per_code=per_code,
                total_mandeh=total_mandeh, last_sanad_detaile=last_sanad, bank_logo=bank_logo
            ))

    # Bulk create new cheque details
    if cheques_to_create:
        print('شروع به ساخت')
        ChequesRecieve.objects.bulk_create(cheques_to_create, batch_size=BATCH_SIZE)

    # Bulk update existing cheque details
    if cheques_to_update:
        print('شروع به آپدیت')
        ChequesRecieve.objects.bulk_update(
            cheques_to_update,
            ['cheque_id', 'cheque_row', 'issuance_tarik', 'issuance_date',
             'cheque_tarik', 'cheque_date', 'cost', 'bank_name',
             'bank_branch', 'account_id', 'description', 'status', 'per_code',
             'total_mandeh', 'last_sanad_detaile', 'bank_logo'],
            batch_size=BATCH_SIZE
        )

    # شناسایی رکوردهای حذف‌شده
    ids_in_external_db = {int(row[0]) for row in mahak_data}
    ids_in_django_db = {cheque.id_mahak for cheque in current_cheques.values()}
    ids_to_delete = ids_in_django_db - ids_in_external_db

    # حذف رکوردهای شناسایی‌شده
    if ids_to_delete:
        ChequesRecieve.objects.filter(id_mahak__in=ids_to_delete).delete()
        print(f"رکوردهای حذف‌شده: {len(ids_to_delete)} رکورد حذف شد.")

    # محاسبه زمان اجرای کل
    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    cursor.execute("SELECT COUNT(*) FROM Cheques_Recieve")
    row_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Cheques_Recieve'")
    column_count = cursor.fetchone()[0]

    # به‌روزرسانی اطلاعات در جدول Mtables
    table = Mtables.objects.filter(name='Cheques_Recieve').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    table.row_count = row_count
    table.column_count = column_count
    table.save()

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f"زمان اتصال به دیتابیس: {db_time:.2f} ثانیه")
    print(f"زمان آپدیت جدول: {update_time:.2f} ثانیه")

    return redirect('/updatedb')





def Cheque_Pay(request):
    t0 = time.time()
    print('شروع آپدیت چک‌های پرداختی---------------------------------------------------')
    conn = connect_to_mahak()
    cursor = conn.cursor()
    t1 = time.time()

    # گرفتن تمامی داده‌ها از دیتابیس خارجی
    cursor.execute(
        "SELECT [ID], [ChequeID], [ChequeRow], [IssuanceDate], [ChequeDate], "
        "[Cost], [BankCode], [Description], [status], [FirstPeriod], "
        "[ChequeIDCounter], [PerCode], [RecieveStatus] "
        "FROM Cheque_Pay"
    )
    mahak_data = cursor.fetchall()

    existing_in_mahak = {int(row[0]) for row in mahak_data}
    print('تعداد رکوردهای موجود در Mahak:', len(existing_in_mahak))

    cheques_to_create = []
    cheques_to_update = []
    current_cheques = {cheque.id_mahak: cheque for cheque in ChequesPay.objects.all()}
    BATCH_SIZE = 1000  # تعیین اندازه دسته‌ها
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year

    sanad_details = SanadDetail.objects.filter(cheque_id__in=[row[1] for row in mahak_data], kol=200,
                                               is_active=True,acc_year=acc_year).order_by('date', 'code',
                                                                        'radif')
    sanad_dict = {}
    for sd in sanad_details:
        if sd.cheque_id not in sanad_dict:
            sanad_dict[sd.cheque_id] = []
        sanad_dict[sd.cheque_id].append(sd)

    # ایجاد دیکشنری از بانک‌ها برای استفاده سریعتر
    bank_dict = {bank.code: bank for bank in Bank.objects.all()}

    for counter, row in enumerate(mahak_data, start=1):
        print(counter)

        id_mahak = int(row[0])
        cheque_id_str = row[1]
        cheque_row = int(row[2])

        # گرفتن تاریخ شمسی از دیتای خارجی
        issuance_date_str = row[3]
        cheque_date_str = row[4]

        # تبدیل تاریخ شمسی به میلادی
        issuance_date = (
            jdatetime.datetime.strptime(issuance_date_str, "%Y/%m/%d").togregorian().date() if issuance_date_str else None
        )
        cheque_date = (
            jdatetime.datetime.strptime(cheque_date_str, "%Y/%m/%d").togregorian().date() if cheque_date_str else None
        )

        # تاریخ شمسی برای ذخیره در fields
        issuance_tarik = issuance_date_str  # ذخیره تاریخ شمسی
        cheque_tarik = cheque_date_str  # ذخیره تاریخ شمسی

        cost = Decimal(row[5] or '0.00')
        bank_code = int(row[6])  # فرض بر این است که این مقدار عددی است
        description = row[7] or ''
        status = row[8] or '0'

        # first_period = fp  # استفاده از مقدار واقعی
        first_period = row[9]  # استفاده از مقدار واقعی
        print(first_period, '===============')
        cheque_id_counter = int(row[10])  # فرض بر این است که این مقدار عددی است
        per_code = row[11] or '0'
        recieve_status = int(row[12])  # فرض بر این است که این مقدار عددی است

        # محاسبه مانده کل چک
        total_bes = sum(sd.bes for sd in sanad_dict.get(cheque_id_str, []))
        total_bed = sum(sd.bed for sd in sanad_dict.get(cheque_id_str, []))
        total_mandeh = total_bes - total_bed

        # دریافت آخرین جزئیات سند
        last_sanad = sanad_dict.get(cheque_id_str, [])[-1] if sanad_dict.get(cheque_id_str) else None

        # یافتن بانک مرتبط با استفاده از bank_code
        bank = bank_dict.get(bank_code, None)

        # بررسی وجود چک در پایگاه داده Django
        if id_mahak in current_cheques:
            cheque = current_cheques[id_mahak]
            # بررسی تغییرات
            if (cheque.cheque_id != cheque_id_str or cheque.cheque_row != cheque_row or
                    cheque.issuance_tarik != issuance_tarik or cheque.cheque_tarik != cheque_tarik or
                    cheque.cost != cost or cheque.bank_code != bank_code or
                    cheque.description != description or cheque.status != status or
                    cheque.firstperiod != first_period or cheque.cheque_id_counter != cheque_id_counter or
                    cheque.total_mandeh != total_mandeh or cheque.last_sanad_detaile != last_sanad or
                    cheque.per_code != per_code or cheque.recieve_status != recieve_status or cheque.bank != bank):
                cheque.cheque_id = cheque_id_str
                cheque.cheque_row = cheque_row
                cheque.issuance_tarik = issuance_tarik  # نگهداری تاریخ شمسی
                cheque.cheque_tarik = cheque_tarik  # نگهداری تاریخ شمسی
                cheque.cost = cost
                cheque.bank_code = bank_code
                cheque.bank = bank  # تنظیم بانک مرتبط
                cheque.description = description
                cheque.status = status
                cheque.firstperiod = first_period
                cheque.cheque_id_counter = cheque_id_counter
                cheque.total_mandeh = total_mandeh
                cheque.last_sanad_detaile = last_sanad
                cheque.per_code = per_code
                cheque.recieve_status = recieve_status
                cheques_to_update.append(cheque)
        else:
            # ایجاد چک جدید
            cheques_to_create.append(ChequesPay(
                id_mahak=id_mahak, cheque_id=cheque_id_str, cheque_row=cheque_row,
                issuance_tarik=issuance_tarik, cheque_tarik=cheque_tarik,
                issuance_date=issuance_date, cheque_date=cheque_date,
                cost=cost, bank_code=bank_code, bank=bank, description=description,
                status=status, firstperiod=first_period,
                cheque_id_counter=cheque_id_counter,
                per_code=per_code, recieve_status=recieve_status,
                total_mandeh=total_mandeh, last_sanad_detaile=last_sanad
            ))

    # Bulk create new cheque details
    if cheques_to_create:
        print('شروع به ساخت چک‌های جدید')
        ChequesPay.objects.bulk_create(cheques_to_create, batch_size=BATCH_SIZE)

    # Bulk update existing cheque details
    if cheques_to_update:
        print('شروع به آپدیت چک‌های موجود')
        ChequesPay.objects.bulk_update(
            cheques_to_update,
            ['cheque_id', 'cheque_row', 'issuance_tarik', 'cheque_tarik',
             'cost', 'bank_code', 'bank', 'description', 'status', 'firstperiod',
             'cheque_id_counter', 'per_code', 'recieve_status',
             'total_mandeh', 'last_sanad_detaile'],
            batch_size=BATCH_SIZE
        )

    # شناسایی رکوردهای حذف‌شده
    ids_in_external_db = {int(row[0]) for row in mahak_data}
    ids_in_django_db = {cheque.id_mahak for cheque in current_cheques.values()}
    ids_to_delete = ids_in_django_db - ids_in_external_db

    # حذف رکوردهای شناسایی‌شده
    if ids_to_delete:
        ChequesPay.objects.filter(id_mahak__in=ids_to_delete).delete()
        print(f"رکوردهای حذف‌شده: {len(ids_to_delete)} رکورد حذف شد.")

    # محاسبه زمان اجرای کل
    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    # به‌روزرسانی اطلاعات در جدول Mtables
    table = Mtables.objects.filter(name='Cheque_Pay').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    cursor.execute("SELECT COUNT(*) FROM Cheque_Pay")
    row_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Cheque_Pay'")
    column_count = cursor.fetchone()[0]
    table.row_count = row_count
    table.column_count = column_count
    table.save()

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f"زمان اتصال به دیتابیس: {db_time:.2f} ثانیه")
    print(f"زمان آپدیت جدول: {update_time:.2f} ثانیه")

    return redirect('/updatedb')




def UpdateLoan(request):
    t0 = time.time()
    print('شروع آپدیت وام‌ها---------------------------------------------------')

    conn = connect_to_mahak()  # فرض بر این است که این تابع به پایگاه داده خارجی متصل می‌شود
    cursor = conn.cursor()
    t1 = time.time()

    # گرفتن تمامی داده‌ها از دیتابیس خارجی
    cursor.execute(
        "SELECT [Code], [NameCode], [Date], [Number], [Distance], [Cost] "
        "FROM Loan"
    )
    mahak_data = cursor.fetchall()

    existing_in_mahak = {int(row[0]) for row in mahak_data}
    print('تعداد رکوردهای موجود در Mahak:', len(existing_in_mahak))

    loans_to_create = []
    loans_to_update = []
    current_loans = {loan.code: loan for loan in Loan.objects.all()}
    BATCH_SIZE = 1000  # تعیین اندازه دسته‌ها

    for counter, row in enumerate(mahak_data, start=1):
        print(counter)

        code = int(row[0])
        name_code = int(row[1])
        tarikh_shamsi = row[2]  # تاریخ شمسی
        number = int(row[3]) if row[3] is not None else 0
        distance = int(row[4]) if row[4] is not None else 0
        cost = Decimal(row[5] or '0.00')*number

        # تبدیل تاریخ شمسی به میلادی
        date = (
            jdatetime.datetime.strptime(tarikh_shamsi, "%Y/%m/%d").togregorian().date()
            if tarikh_shamsi else None
        )

        # پیدا کردن شخص متناظر با name_code
        person = Person.objects.filter(code=name_code).first()

        # بررسی وجود وام در پایگاه داده Django
        if code in current_loans:
            loan = current_loans[code]
            # بررسی تغییرات
            if (loan.name_code != name_code or loan.number != number or
                    loan.distance != distance or loan.cost != cost or
                    loan.date != date or loan.person != person or loan.tarikh != tarikh_shamsi):
                loan.name_code = name_code
                loan.number = number
                loan.distance = distance
                loan.cost = cost
                loan.date = date
                loan.person = person
                loan.tarikh = tarikh_shamsi
                loans_to_update.append(loan)
        else:
            # ایجاد وام جدید
            loans_to_create.append(Loan(
                code=code, name_code=name_code, number=number,
                distance=distance, cost=cost, date=date, person=person, tarikh=tarikh_shamsi
            ))

            # Bulk create new loans
    if loans_to_create:
        print('شروع به ساخت وام‌های جدید')
        Loan.objects.bulk_create(loans_to_create, batch_size=BATCH_SIZE)

        # Bulk update existing loans
    if loans_to_update:
        print('شروع به آپدیت وام‌های موجود')
        Loan.objects.bulk_update(
            loans_to_update,
            ['name_code', 'number', 'distance', 'cost', 'date', 'person', 'tarikh'],
            batch_size=BATCH_SIZE
        )

        # شناسایی رکوردهای حذف‌شده
    ids_in_external_db = {int(row[0]) for row in mahak_data}
    ids_in_django_db = {loan.code for loan in current_loans.values()}
    ids_to_delete = ids_in_django_db - ids_in_external_db

    # حذف رکوردهای شناسایی‌شده
    if ids_to_delete:
        Loan.objects.filter(code__in=ids_to_delete).delete()
        print(f"رکوردهای حذف‌شده: {len(ids_to_delete)} رکورد حذف شد.")

        # محاسبه زمان اجرای کل
    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f"زمان اتصال به دیتابیس: {db_time:.2f} ثانیه")
    print(f"زمان آپدیت جدول: {update_time:.2f} ثانیه")

    # به‌روزرسانی اطلاعات در جدول Mtables
    table = Mtables.objects.filter(name='Loan').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    cursor.execute("SELECT COUNT(*) FROM Loan")
    row_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Loan'")
    column_count = cursor.fetchone()[0]
    table.row_count = row_count
    table.column_count = column_count
    table.save()

    return redirect('/updatedb')





def UpdateLoanDetail(request):
    # LoanDetil.objects.all().delete()
    t0 = time.time()
    print('شروع آپدیت جزئیات وام-----------------------------------')

    conn = connect_to_mahak()  # فرض بر این است که این تابع به پایگاه داده خارجی متصل می‌شود
    cursor = conn.cursor()
    t1 = time.time()

    # گرفتن تمامی داده‌ها از دیتابیس خارجی
    cursor.execute(
        "SELECT [ID], [LoanCode], [Row], [Date], [RecieveDate], [Delay], [Cost], [Comment] "
        "FROM LoanDetail"
    )
    mahak_data = cursor.fetchall()

    existing_in_mahak = {int(row[0]) for row in mahak_data}
    print('تعداد رکوردهای موجود در Mahak:', len(existing_in_mahak))

    loan_detils_to_create = []
    loan_detils_to_update = []
    current_loan_detils = {detail.code: detail for detail in LoanDetil.objects.all()}
    BATCH_SIZE = 1000  # تعیین اندازه دسته‌ها

    for counter, row in enumerate(mahak_data, start=1):
        print(counter)
        code = int(row[0])  # ID به کد در مدل نگاشته می‌شود
        loan_code = int(row[1])
        row_number = int(row[2]) if row[2] is not None else None
        tarikh_shamsi = row[3]  # تاریخ فضایی شمسی
        recive_tarikh_shamsi = row[4]  # تاریخ دریافت شمسی
        delay = Decimal(row[5] or '0.00')
        cost = Decimal(row[6] or '0.00')
        comment = row[7] or ''

        # تبدیل تاریخ شمسی به میلادی
        date = (
            jdatetime.datetime.strptime(tarikh_shamsi, "%Y/%m/%d").togregorian().date()
            if tarikh_shamsi and tarikh_shamsi.strip() else None
        )
        recive_date = (
            jdatetime.datetime.strptime(recive_tarikh_shamsi, "%Y/%m/%d").togregorian().date()
            if recive_tarikh_shamsi and recive_tarikh_shamsi.strip() else None
        )


        # پیدا کردن وام متناظر با loan_code
        loan = Loan.objects.filter(code=loan_code).first()

        # بررسی وجود جزئیات وام در پایگاه داده Django
        if code in current_loan_detils:
            loan_detil = current_loan_detils[code]
            # بررسی تغییرات
            if (loan_detil.loan_code != loan_code or loan_detil.row != row_number or
                    loan_detil.date != date or loan_detil.recive_date != recive_date or
                    loan_detil.delay != delay or loan_detil.cost != cost or
                    loan_detil.comment != comment or loan_detil.loan != loan or loan_detil.tarikh != tarikh_shamsi or
                    loan_detil.recive_tarikh != recive_tarikh_shamsi):
                loan_detil.loan_code = loan_code
                loan_detil.row = row_number
                loan_detil.date = date
                loan_detil.recive_date = recive_date
                loan_detil.delay = delay
                loan_detil.cost = cost
                loan_detil.comment = comment
                loan_detil.loan = loan
                loan_detil.tarikh = tarikh_shamsi
                loan_detil.recive_tarikh = recive_tarikh_shamsi
                loan_detils_to_update.append(loan_detil)


        else:

            # ایجاد جزئیات وام جدید
            loan_detils_to_create.append(LoanDetil(
                code=code, loan_code=loan_code, row=row_number,
                tarikh=tarikh_shamsi, date=date,
                recive_tarikh=recive_tarikh_shamsi, recive_date=recive_date,
                delay=delay, cost=cost, comment=comment, loan=loan
            ))

                # Bulk create new loan details
    if loan_detils_to_create:
        print('شروع به ساخت جزئیات وام‌های جدید')
        LoanDetil.objects.bulk_create(loan_detils_to_create, batch_size=BATCH_SIZE)
        print('loan_detils_to_create')
        print(len(loan_detils_to_create))
    # Bulk update existing loan details
    if loan_detils_to_update:
        print('شروع به آپدیت جزئیات وام‌های موجود')
        print('loan_detils_to_update')
        print(len(loan_detils_to_update))
        LoanDetil.objects.bulk_update(
            loan_detils_to_update,
            ['loan_code', 'row', 'date', 'recive_date', 'delay',
             'cost', 'comment', 'loan', 'tarikh', 'recive_tarikh'],
            batch_size=BATCH_SIZE
        )

    # شناسایی رکوردهای حذف‌شده
    ids_in_external_db = {int(row[0]) for row in mahak_data}
    ids_in_django_db = {detail.code for detail in current_loan_detils.values()}
    ids_to_delete = ids_in_django_db - ids_in_external_db

    print('IDs in external DB:', ids_in_external_db)
    print('IDs in Django DB:', ids_in_django_db)
    print('IDs to delete:', ids_to_delete)


    # حذف رکوردهای شناسایی‌شده
    if ids_to_delete:
        LoanDetil.objects.filter(code__in=ids_to_delete).delete()
        print(f"رکوردهای حذف‌شده: {len(ids_to_delete)} رکورد حذف شد.")
    else:
        print("هیچ رکوردی برای حذف یافت نشد.")
    for i in LoanDetil.objects.all():
        if i.recive_tarikh is None:
            print(f"None: {i.id}")
        elif i.recive_tarikh.strip() == "":
            print(f"Empty String: {i.id}")
        else:
            print(f"Value: {i.recive_tarikh} (ID: {i.id})")

    loan_to_update = []
    for lo in Loan.objects.all():
        print('+++++++++++++++++++++++')
        for l in LoanDetil.objects.filter(loan=lo, recive_date__isnull=True):
            print(l.loan_code,l.tarikh,l.recive_tarikh,l.cost)
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        for l in LoanDetil.objects.filter(loan=lo):
            print(l.loan_code, l.tarikh, l.recive_tarikh, l.cost)



        loan_mandeh = LoanDetil.objects.filter(loan=lo, recive_date__isnull=True).aggregate(total_cost=Sum('cost'))['total_cost'] or 0


        print(loan_mandeh)
        if lo.loan_mandeh != loan_mandeh:
            lo.loan_mandeh = loan_mandeh
            loan_to_update.append(lo)

    if loan_to_update:
        print('شروع به آپدیت مانده وام‌های موجود')
        print('loan_to_update')
        print(len(loan_to_update))
        Loan.objects.bulk_update(
            loan_to_update,
            ['loan_mandeh'],
            batch_size=BATCH_SIZE
        )

    # محاسبه زمان اجرای کل
    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    update_time = tend - t1

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f"زمان اتصال به دیتابیس: {db_time:.2f} ثانیه")
    print(f"زمان آپدیت جدول: {update_time:.2f} ثانیه")

    # به‌روزرسانی اطلاعات در جدول Mtables
    table = Mtables.objects.filter(name='LoanDetail').last()
    table.last_update_time = timezone.now()
    table.update_duration = update_time
    cursor.execute("SELECT COUNT(*) FROM LoanDetail")
    row_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'LoanDetail'")
    column_count = cursor.fetchone()[0]
    table.row_count = row_count
    table.column_count = column_count
    table.save()


    return redirect('/updatedb')



def UpdateSanadConditions(request):
    t0 = time.time()
    print('شروع آپدیت شرایط اسناد---------------------------------------')

    # فعال کردن همه اسناد
    SanadDetail.objects.filter(is_active=False).update(is_active=True)

    # گرفتن تمامی شرایط فعال
    # conditions = MyCondition.objects.filter(is_active=True,is_new=True)
    conditions = MyCondition.objects.filter(is_active=True)
    to_update = []
    print('شروع بررسی')
    for condition in conditions:

        # بررسی مقادیر
        print(f"acc_year: {condition.acc_year},kol: {condition.kol}, moin: {condition.moin}, tafzili: {condition.tafzili}")

        # فیلتر کردن اسناد بر اساس kol، moin و tafzili
        sanad_details = SanadDetail.objects.all()

        if condition.acc_year is not None and condition.acc_year != 0:
            sanad_details = sanad_details.filter(acc_year=condition.acc_year)
        if condition.kol is not None and condition.kol != 0:
            sanad_details = sanad_details.filter(kol=condition.kol)
        if condition.moin is not None and condition.moin != 0:
            sanad_details = sanad_details.filter(moin=condition.moin)
        if condition.tafzili is not None and condition.tafzili != 0:
            sanad_details = sanad_details.filter(tafzili=condition.tafzili)

        if not condition.contain and not condition.equal_to:
            to_update.extend(sanad_details)
            for sanad in sanad_details:
                sanad.is_active = False  # غیرفعال کردن فقط در صورت نیاز
        else:
            for sanad in sanad_details:
                if (condition.contain and condition.contain in sanad.sharh) or \
                        (sanad.sharh == condition.equal_to):
                    sanad.is_active = False
                    to_update.append(sanad)

                # به‌روزرسانی دسته‌ای اسناد

        # condition.is_new = False
        # condition.save()

    if to_update:
        with transaction.atomic():
            SanadDetail.objects.bulk_update(to_update, ['is_active'])

            # محاسبه زمان اجرای کل
    tend = time.time()
    total_time = tend - t0
    print(f"زمان کل: {total_time:.2f} ثانیه")

    return redirect('/updatedb')



def UpdateBedehiMoshtari(request):
    BedehiMoshtari.objects.all().delete()
    t0 = time.time()
    print('شروع آپدیت بدهی مشتری-------------------------------')
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
    try:
        with transaction.atomic():
            # محاسبه مجموع curramount بر اساس tafzili و moin
            tafzili_sums = SanadDetail.objects.filter(moin=1, kol=103,is_active=True,acc_year=acc_year).values('tafzili', 'moin').annotate(total_curramount=Sum('curramount'))

            # جمع‌آوری داده‌ها برای به‌روزرسانی
            data_to_create = []
            data_to_update = []
            existing_entries = {entry.tafzili: entry for entry in BedehiMoshtari.objects.all()}

            for tafzili_sum in tafzili_sums:
                tafzili_code = tafzili_sum['tafzili']
                moin_code = tafzili_sum['moin']
                total_curramount = tafzili_sum['total_curramount']

                # پیدا کردن فرد مربوط به tafzili_code
                if str(tafzili_code).startswith("10000"):
                    tafzili_code2 = int(str(tafzili_code)[5:])
                elif str(tafzili_code).startswith("1000"):
                    tafzili_code2 = int(str(tafzili_code)[4:])
                elif str(tafzili_code).startswith("100"):
                    tafzili_code2 = int(str(tafzili_code)[3:])
                elif str(tafzili_code).startswith("10"):
                    tafzili_code2 = int(str(tafzili_code)[2:])
                else:
                    tafzili_code2 = int(str(tafzili_code)[1:])
                print(tafzili_code,tafzili_code2)
                person = Person.objects.filter(code=tafzili_code2).first()
                loans = []
                loans_total = 0
                total_with_loans = 0

                if person:
                    # پیدا کردن وام‌های شخص
                    loans = Loan.objects.filter(person=person)
                    print('len(loans)',len(loans))
                    loans_total = loans.aggregate(total_cost=Sum('cost'))['total_cost'] or 0
                    total_with_loans = loans_total + total_curramount
                else:
                    print('no person')

                if tafzili_code in existing_entries:
                    entry = existing_entries[tafzili_code]
                    entry.person = person
                    entry.total_mandeh = total_curramount
                    entry.total_with_loans = total_with_loans
                    entry.loans_total = loans_total
                    entry.moin = moin_code
                    data_to_update.append(entry)
                else:
                    entry = BedehiMoshtari(
                        tafzili=tafzili_code,
                        person=person,
                        total_mandeh=total_curramount,
                        total_with_loans=total_with_loans,
                        loans_total=loans_total,
                        moin=moin_code
                    )
                    entry.save()
                    entry.loans.set(loans)  # تنظیم وام‌ها
                    data_to_create.append(entry)

            # Bulk update existing entries
            if data_to_update:
                BedehiMoshtari.objects.bulk_update(data_to_update, ['person', 'total_mandeh', 'total_with_loans', 'loans_total', 'moin'])

            # شناسایی رکوردهای حذف‌شده
            ids_in_external_db = {entry.tafzili for entry in data_to_create + data_to_update}
            ids_in_django_db = set(existing_entries.keys())
            ids_to_delete = ids_in_django_db - ids_in_external_db

            # حذف رکوردهای شناسایی‌شده
            if ids_to_delete:
                BedehiMoshtari.objects.filter(tafzili__in=ids_to_delete).delete()
                print(f"رکوردهای حذف‌شده: {len(ids_to_delete)} رکورد حذف شد.")
            else:
                print("هیچ رکوردی برای حذف یافت نشد.")
    except Exception as e:
        print(f"خطا در به‌روزرسانی بدهی مشتری: {e}")

    # محاسبه زمان اجرای کل
    tend = time.time()
    total_time = tend - t0
    print(f"زمان کل: {total_time:.2f} ثانیه")

    return redirect('/updatedb')


from django.db.models import Sum
from django.shortcuts import redirect
import time

from django.db.models import Sum
from django.shortcuts import redirect
import time
from django.shortcuts import render, redirect
from django.db.models import F, Sum, ExpressionWrapper, FloatField

from django.db.models import Sum
from django.shortcuts import redirect
import time

def CompleLoan3(request):
    t0 = time.time()
    print('وام ای پرداخت شده---------------------')

    # به روز رسانی اقساطی که تاریخ دریافت آن‌ها مشخص است
    LoanDetil.objects.filter(recive_date__isnull=False).update(complete_percent=1)

    # دریافت مشتریانی که بدهی کل منفی و وام‌های مثبت دارند
    bedehkaran_vamdar = BedehiMoshtari.objects.filter(total_mandeh__lt=0, loans_total__gt=0)

    for bedehkar in bedehkaran_vamdar:
        per = bedehkar.person
        lo_detail = LoanDetil.objects.filter(loan__person=per, recive_date__isnull=True).order_by('date')  # مرتب‌سازی بر اساس تاریخ
        sum_lo_detail = lo_detail.aggregate(total_cost=Sum('cost'))['total_cost'] or 0
        if -bedehkar.total_mandeh >= sum_lo_detail:
            lo_detail.update(complete_percent=0)
        else:
            sum_completed_loan = 0
            not_completed = 0
            updated_loans = []  # لیستی برای ذخیره اقساط به روز شده

            for lo in lo_detail:
                if sum_completed_loan + lo.cost <= -bedehkar.total_mandeh:
                    sum_completed_loan += lo.cost
                    lo.complete_percent = 1  # اقساط کامل پرداخت شده
                else:
                    # محاسبه نسبت برای اقساط ناقص
                    remaining = -bedehkar.total_mandeh - sum_completed_loan
                    if remaining > 0 and lo.cost > 0:  # اطمینان از غیرصفر بودن هزینه
                        lo.complete_percent = max(0, min(1, remaining / lo.cost))  # محدود کردن درصد در بازه ۰ تا ۱
                        print(lo.id, lo.complete_percent)  # پرینت برای بررسی
                    else:
                        lo.complete_percent = 0  # اگر هیچ پرداختی نشده باشد

                    break  # پس از پیدا کردن قسط ناقص، از حلقه خارج می‌شویم

                updated_loans.append(lo)  # اضافه کردن قسط به لیست به روز شده

            # به روز رسانی همه اقساط به صورت همزمان
            LoanDetil.objects.bulk_update(updated_loans, ['complete_percent'])



    # محاسبه زمان اجرای کل
    tend = time.time()
    total_time = tend - t0
    print(f"زمان کل: {total_time:.2f} ثانیه")
    print('ppppppppppppppppppppppppppppppppppppp')
    for i in LoanDetil.objects.filter(complete_percent__gt=0,complete_percent__lt=1):
        print(i.id,i.complete_percent)



    return redirect('/updatedb')


def CompleLoan(request):
    t0 = time.time()
    print('وام های پرداخت شده---------------------')

    # به روز رسانی اقساطی که تاریخ دریافت آن‌ها مشخص است
    LoanDetil.objects.filter(recive_date__isnull=False).update(complete_percent=1)
    bestankar_vamdar_list = BedehiMoshtari.objects.filter(total_mandeh__gte=0, loans_total__gt=0).values('tafzili')
    LoanDetil.objects.filter(loan__name_code__in=bestankar_vamdar_list).update(complete_percent=1)


    # دریافت مشتریانی که بدهی کل منفی و وام‌های مثبت دارند
    bedehkaran_vamdar = BedehiMoshtari.objects.filter(total_mandeh__lt=0, loans_total__gt=0)

    for bedehkar in bedehkaran_vamdar:
        per = bedehkar.person
        lo_detail = LoanDetil.objects.filter(loan__person=per, recive_date__isnull=True).order_by(
            'date')  # مرتب‌سازی بر اساس تاریخ
        sum_lo_detail = lo_detail.aggregate(total_cost=Sum('cost'))['total_cost'] or 0
        if -bedehkar.total_mandeh >= sum_lo_detail:
            lo_detail.update(complete_percent=0)
        else:
            sum_completed_loan = 0
            not_completed = 0
            updated_loans = []  # لیستی برای ذخیره اقساط به روز شده
            skip_remaining = False  # متغیر برای دور زدن اقساط باقی‌مانده

            for lo in lo_detail:
                if skip_remaining:
                    lo.complete_percent = 0
                else:
                    if sum_completed_loan + lo.cost <= sum_lo_detail+bedehkar.total_mandeh:
                        sum_completed_loan += lo.cost
                        lo.complete_percent = 1  # اقساط کامل پرداخت شده
                    else:
                        # محاسبه نسبت برای اقساط ناقص
                        remaining = sum_lo_detail+bedehkar.total_mandeh - sum_completed_loan
                        if remaining > 0 and lo.cost > 0:  # اطمینان از غیرصفر بودن هزینه
                            lo.complete_percent = max(0, min(1, remaining / lo.cost))  # محدود کردن درصد در بازه ۰ تا ۱
                            print(lo.id, lo.complete_percent)  # پرینت برای بررسی
                        else:
                            lo.complete_percent = 0  # اگر هیچ پرداختی نشده باشد

                        # تنظیم skip_remaining به True برای تنظیم اقساط باقی‌مانده به 0
                        skip_remaining = True

                # اضافه کردن قسط به لیست به روز شده
                updated_loans.append(lo)

            # به روز رسانی همه اقساط به صورت همزمان
            LoanDetil.objects.bulk_update(updated_loans, ['complete_percent'])

    # مانده واقعی وام ها
    # # دریافت تمام وام‌ها
    # loans = Loan.objects.all()
    # # لیست برای نگهداری وام‌هایی که نیاز به به‌روزرسانی دارند
    # loans_to_update = []
    #
    # for loan in loans:
    #     # محاسبه مقدار جدید actual_loan_mandeh به صورت مستقیم در ویو
    #     remaining_installments_amount = loan.loandetil_set.filter(complete_percent__lt=1).annotate(
    #         remaining_amount=ExpressionWrapper(
    #             (1 - F('complete_percent')) * F('cost'),
    #             output_field=FloatField()
    #         )
    #     ).aggregate(total_remaining=Sum('remaining_amount'))['total_remaining'] or 0
    #
    #     new_actual_loan_mandeh = remaining_installments_amount
    #
    #     # بررسی اگر نیاز به به‌روزرسانی است
    #     if loan.actual_loan_mandeh != new_actual_loan_mandeh:
    #         loan.actual_loan_mandeh = new_actual_loan_mandeh
    #         loans_to_update.append(loan)
    #
    #         # به‌روزرسانی دسته‌ای وام‌ها
    # Loan.objects.bulk_update(loans_to_update, ['actual_loan_mandeh'])

    # دریافت تمام وام‌ها
    loans = Loan.objects.all()

    # لیست برای نگهداری وام‌هایی که نیاز به به‌روزرسانی دارند
    loans_to_update = []

    today = timezone.now().date()  # تاریخ امروز

    for loan in loans:
        # محاسبه مقدار جدید actual_loan_mandeh
        remaining_installments_amount = loan.loandetil_set.filter(complete_percent__lt=1).annotate(
            remaining_amount=ExpressionWrapper(
                (1 - F('complete_percent')) * F('cost'),
                output_field=FloatField()
            )
        ).aggregate(total_remaining=Sum('remaining_amount'))['total_remaining'] or 0

        new_actual_loan_mandeh = remaining_installments_amount

        # محاسبه مقدار جدید delayed_loan (مانده وام معوق)
        delayed_installments_amount = loan.loandetil_set.filter(
            date__lt=today,  # فیلتر کردن اقساط با تاریخ قبل از امروز
            complete_percent__lt=1  # فیلتر کردن اقساط ناقص
        ).annotate(
            remaining_amount=ExpressionWrapper(
                (1 - F('complete_percent')) * F('cost'),
                output_field=FloatField()
            )
        ).aggregate(total_remaining=Sum('remaining_amount'))['total_remaining'] or 0

        new_delayed_loan = delayed_installments_amount

        # بررسی اگر نیاز به به‌روزرسانی است
        if loan.actual_loan_mandeh != new_actual_loan_mandeh or loan.delayed_loan != new_delayed_loan:
            loan.actual_loan_mandeh = new_actual_loan_mandeh
            loan.delayed_loan = new_delayed_loan
            loans_to_update.append(loan)

            # به‌روزرسانی دسته‌ای وام‌ها
    Loan.objects.bulk_update(loans_to_update, ['actual_loan_mandeh', 'delayed_loan'])

            # محاسبه زمان اجرای کل
    tend = time.time()
    total_time = tend - t0
    print(f"زمان کل: {total_time:.2f} ثانیه")
    return redirect('/updatedb')


import os
import pandas as pd
from django.shortcuts import redirect
from django.conf import settings

import os
import pandas as pd
from django.shortcuts import redirect
from django.conf import settings
from .models import MyCondition  # فرض بر این است که مدل در یک فایل به نام models.py تعریف شده است


def UpdateMyCondition(request):
    print('def UpdateMyCondition=========================================')

    # مسیر فایل اکسل
    file_path = os.path.join(settings.BASE_DIR, 'temp', 'mycondition.xlsx')

    # خواندن فایل اکسل با Pandas
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        print(f"فایل اکسل {file_path} یافت نشد.")
        # می توانید یک پیام خطا به کاربر نمایش دهید یا یک مسیر پیش فرض را استفاده کنید
        return redirect('/error_page')  # فرضاً یک صفحه خطا دارید

    # تبدیل مقادیر 1 و 0 به True و False
    df['is_active'] = df['is_active'].astype(bool)
    df['is_new'] = df['is_new'].astype(bool)

    # لیست شناسه های موجود در فایل اکسل
    excel_ids = df.index.tolist()  # Assuming you want to use the index from the excel file

    # واکشی تمام رکوردهای موجود در پایگاه داده
    db_records = MyCondition.objects.all()
    db_ids = [record.pk for record in db_records]  # Assuming you want to use the pk from the model

    # شناسایی شناسه هایی که در اکسل نیستند و باید حذف شوند
    ids_to_delete = list(set(db_ids) - set(excel_ids))

    # حذف رکوردهایی که در اکسل وجود ندارند
    MyCondition.objects.filter(pk__in=ids_to_delete).delete()

    # پردازش داده‌ها و به‌روزرسانی/ایجاد مدل
    for index, row in df.iterrows():
        # دریافت مقادیر از ستون ها
        acc_year = row['acc_year']
        kol = row['kol']
        moin = row['moin']
        tafzili = row['tafzili']

        # بررسی خالی بودن سلول و قرار دادن None بجای آن
        contain = row['contain'] if pd.notna(row['contain']) else None
        equal_to = row['equal_to'] if pd.notna(row['equal_to']) else None

        is_active = row['is_active']
        is_new = row['is_new']

        # آپدیت یا ایجاد رکورد جدید
        MyCondition.objects.update_or_create(
            pk=index,  # استفاده از pk (شناسه) فایل اکسل برای آپدیت. فرض بر این است که شناسه در فایل اکسل موجود است
            defaults={
                'acc_year': acc_year,
                'kol': kol,
                'moin': moin,
                'tafzili': tafzili,
                'contain': contain,
                'equal_to': equal_to,
                'is_active': is_active,
                'is_new': is_new
            }
        )

    return redirect('/updatedb')  # یا هر آدرسی که می‌خواهید بعد از به‌روزرسانی به آن منتقل شوید
from collections import Counter

import jdatetime
import pyodbc
import os
from mahakupdate.models import WordCount, Kardex, Person
import sys
from django.shortcuts import render, redirect
from .forms import CategoryForm, KalaForm
from django.utils import timezone
from django.db import transaction
import time
from .models import FactorDetaile, Factor, Kala, Mtables

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)


# Create your views here.
def connect_to_mahak():
    sn = os.getenv('COMPUTERNAME')
    print('sn')
    print(sn)

    connections = {
        'DESKTOP-ITU3EHV': ('DESKTOP-ITU3EHV\\MAHAK14', 'mahak'),
        'TECH_MANAGER': ('TECH_MANAGER\\RKALANTARI', 'mahak'),
        'DESKTOP-1ERPR1M': ('DESKTOP-1ERPR1M\\MAHAK', 'mahak'),
        'sadegh': ('SADEGH\\INSTANCE', 'mahak')
    }

    if sn in connections:
        server, database = connections[sn]
        if sn == 'sadegh':
            conn = pyodbc.connect(
                f'Driver={{SQL Server}};Server={server};Database={database};UID=ali;PWD=123456;Integrated Security=False;'
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
    import time
    from django.db import transaction

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
            Factor.objects.bulk_update(factors_to_update, ['pdate', 'mablagh_factor', 'takhfif', 'create_time', 'darsad_takhfif'])

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
def UpdateKardex(request):
    import time
    from django.db import transaction
    from django.db.models import Q

    t0 = time.time()
    print('شروع آپدیت کاردکس----------------------------------------')

    conn = connect_to_mahak()
    cursor = conn.cursor()
    t1 = time.time()

    cursor.execute("SELECT * FROM Kardex")
    mahakt_data = cursor.fetchall()
    print('خواندن از دیتابیس انجام شد')

    existing_in_mahak = {(row[0], row[4], row[12]) for row in mahakt_data}

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

    # Bulk create new kardex records
    if kardex_to_create:
        with transaction.atomic():
            Kardex.objects.bulk_create(kardex_to_create)

    # Bulk update existing kardex records
    if kardex_to_update:
        with transaction.atomic():
            Kardex.objects.bulk_update(kardex_to_update, ['code_factor', 'percode', 'warehousecode', 'mablaghsanad', 'count', 'averageprice', 'radif'])

    # Delete obsolete kardex records
    with transaction.atomic():
        obsolete_kardex = Kardex.objects.exclude(Q(pdate__in=[k[0] for k in existing_in_mahak]) &
                                                Q(code_kala__in=[k[1] for k in existing_in_mahak]) &
                                                Q(stock__in=[k[2] for k in existing_in_mahak]))
        if obsolete_kardex.exists():
            obsolete_kardex.delete()

    t2 = time.time()
    print('آپدیت انجام شد')

    # اجرای حلقه جایگزین سیگنال‌ها در بخش‌های کوچک‌تر
    # اجرای حلقه جایگزین سیگنال‌ها
    kardex_instances = list(Kardex.objects.prefetch_related('factor', 'kala').all())
    batch_size = 1000
    updates = []
    factors = {factor.code: factor for factor in
               Factor.objects.filter(code__in=[k.code_factor for k in kardex_instances])}
    kalas = {kala.code: kala for kala in Kala.objects.filter(code__in=[k.code_kala for k in kardex_instances])}

    for kardex in kardex_instances:
        factor = factors.get(kardex.code_factor)
        kala = kalas.get(kardex.code_kala)

        # بررسی تغییرات قبل از به‌روزرسانی
        updated = False
        if kardex.factor != factor:
            kardex.factor = factor
            updated = True

        if kardex.kala != kala:
            kardex.kala = kala
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
            Kardex.objects.bulk_update(updates, ['factor', 'kala', 'code_kala', 'code_factor', 'date'])


    t3 = time.time()
    print('جایگزین سیگنال انجام شد')

    tend = time.time()
    total_time = tend - t0
    db_time = t1 - t0
    up_time = t2 - t1
    sig_time = t3 - t2

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" اتصال به دیتابیس:{db_time:.2f} ثانیه")
    print(f" عملیات اصلی آپدیت:{up_time:.2f} ثانیه")
    print(f" جایگزین سیگنال:{sig_time:.2f} ثانیه")

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
    import time
    from django.db import transaction

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
            Person.objects.bulk_update(persons_to_update, ['grpcode', 'name', 'lname', 'tel1', 'tel2', 'fax', 'mobile', 'address', 'comment'])

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





def Update_from_mahak(request):
    t0 = time.time()
    print('شروع آپدیت---------------------------------------')
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



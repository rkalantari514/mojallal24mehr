from functools import update_wrapper
import pyodbc
from django.shortcuts import render
import os
from mahakupdate.models import Mtables, Kala, Factor, FactorDetaile, WordCount
import sys

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
import time
from collections import Counter


# Create your views here.
def connect_to_mahak():
    sn = os.getenv('COMPUTERNAME')
    print('sn')
    print(sn)

    # hp home
    if sn == 'DESKTOP-ITU3EHV':
        conn = pyodbc.connect('Driver={SQL Server};'
                              'Server=DESKTOP-ITU3EHV\\MAHAK14;'
                              'Database=mahak2;'
                              'Trusted_Connection=yes;')
        return conn  # برگرداندن conn در اینجا
    else:

        # surface
        if sn == 'TECH_MANAGER':
            conn = pyodbc.connect('Driver={SQL Server};'
                                  'Server=TECH_MANAGER\\RKALANTARI;'
                                  'Database=mahak2;'
                                  'Trusted_Connection=yes;')

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



    # Kala.objects.all().delete()

    t2 = time.time()

    #  ================================================== پر کردن جدول کالا ============
    cursor.execute("SELECT * FROM GoodInf")
    mahakt_data = cursor.fetchall()
    existing_in_mahak = {row[1] for row in mahakt_data}
    print('existing_in_mahak')
    print(existing_in_mahak)
    for row in mahakt_data:
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
    #
    Factor.objects.all().delete()
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
    cursor.execute("SELECT * FROM Kardex")  # یا نام همه ستون‌ها را به جا column4, column7, column11 وارد کنید
    mahakt_data = cursor.fetchall()
    # existing_in_mahak = {row[0] for row in mahakt_data}  # مجموعه‌ای از کدهای موجود در Fact_Fo
    # print('existing_in_mahak')
    # print(existing_in_mahak)
    for row in mahakt_data:
        if row[4] == 58692:
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


def Kala_group(request):
    # kalas = Kala.objects.all()
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

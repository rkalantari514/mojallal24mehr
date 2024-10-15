from functools import update_wrapper
import pyodbc
from django.shortcuts import render
import os
from mahakupdate.models import Mtables, Kala, Factor, FactorDetaile
import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
import time

# Create your views here.
def connect_to_mahak():
    sn = os.getenv('COMPUTERNAME')
    print('sn')
    print(sn)

    #hp home
    if sn == 'DESKTOP-ITU3EHV':
        conn = pyodbc.connect('Driver={SQL Server};'
                              'Server=DESKTOP-ITU3EHV\\MAHAK14;'
                              'Database=mahak2;'
                              'Trusted_Connection=yes;')
        cursor = conn.cursor()
        return cursor  # برگرداندن cursor در اینجا
    else:

        # surface
        if sn == 'TECH_MANAGER':
            conn = pyodbc.connect('Driver={SQL Server};'
                                  'Server=TECH_MANAGER\\RKALANTARI;'
                                  'Database=mahak2;'
                                  'Trusted_Connection=yes;')
            cursor = conn.cursor()
            return cursor  # برگرداندن cursor در اینجا
        else:
            # hp office
            if sn == 'DESKTOP-1ERPR1M':
                conn = pyodbc.connect('Driver={SQL Server};'
                                      'Server=DESKTOP-1ERPR1M\\MAHAK;'
                                      'Database=mahak2;'
                                      'Trusted_Connection=yes;')
                cursor = conn.cursor()
                return cursor  # برگرداندن cursor در اینجا
            else:
                raise EnvironmentError("The computer name does not match.")


def Update_from_mahak(request):
    t0 = time.time()
    print('شروع آپدیت')
    cursor=connect_to_mahak()
    print('cursor')
    print(cursor)


    t1 = time.time()
    # # شناسایی کل جاول موجود
    # cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    # tables = cursor.fetchall()
    # Mtables.objects.all().delete()
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
    #         Mtables.objects.create(
    #             name=table_name,
    #             row_count=row_count,
    #             cloumn_count=column_count
    #         )
    #     except:
    #         print('error')




    # Kala.objects.all().delete()

    t2 = time.time()

    # پر کردن جدول کالا
  #   cursor.execute("SELECT * FROM GoodInf;")
  #   rows=cursor.fetchall()
  #   for i in rows:
  #       Kala.objects.create(
  #
  #           code=i[1],
  #           name=i[2],
  # )
  #       print(i[1],i[2])

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
    model_to_delete =Kala.objects.exclude(code__in=existing_in_mahak)
    print('model_to_delete')
    print(model_to_delete)
    model_to_delete.delete()
    print('delete finish')




    #
    # # اتصال به دیتابیس SQLite
    # sqlite_conn = pyodbc.connect('DRIVER={SQLite3 ODBC Driver};DATABASE=BASE_DIR/db.sqlite3')
    #
    # # خواندن داده‌ها از SQLite
    # sqlite_cursor = sqlite_conn.cursor()
    # sqlite_cursor.execute('SELECT code, name FROM kala')
    # sqlite_data = sqlite_cursor.fetchall()
    #
    # # خواندن داده‌ها از SQL Server
    # cursor.execute('SELECT code, name FROM table_name')
    # sql_server_data = cursor.fetchall()
    #
    # # شناسایی ردیف‌های اضافی در SQLite
    # sqlite_keys = {row[0] for row in sqlite_data}  # استخراج کلیدها از SQLite
    # sql_server_keys = {row[0] for row in sql_server_data}  # استخراج کلیدها از SQL Server
    #
    # rows_to_delete = sqlite_keys - sql_server_keys
    # for key in rows_to_delete:
    #     sqlite_cursor.execute('DELETE FROM kala WHERE column1 = ?', (key,))
    #
    # # همگام‌سازی داده‌ها
    # for row_sqlite in sqlite_data:
    #     for row_sql_server in sql_server_data:
    #         if row_sqlite[0] == row_sql_server[0]:  # مثال برای کلید مشترک
    #             sqlite_cursor.execute('''
    #                 UPDATE kala
    #                 SET name = ?
    #                 WHERE code = ?
    #             ''', (row_sql_server[1], row_sqlite[0]))
    #
    # # درج داده‌های جدید در SQLite
    # for row_sql_server in sql_server_data:
    #     if row_sql_server[0] not in sqlite_keys:
    #         sqlite_cursor.execute('''
    #             INSERT INTO kala (cide,name)
    #             VALUES (?, ?, ?)
    #         ''', (row_sql_server[0], row_sql_server[1], row_sql_server[2]))

    # Factor.objects.all().delete()

    t3 = time.time()
    # # پر کردن جدول فاکتور
    # cursor.execute("SELECT * FROM Fact_Fo;")
    # rows=cursor.fetchall()
    # for i in rows:
    #     print(i)
    #     print(i[0], i[4], i[5], i[6], i[38],i[44])
    #     Factor.objects.create(
    #     code = i[0],
    #     pdate = i[4],
    #     mablagh_factor = i[5],
    #     takhfif = i[6],
    #     create_time=i[38],
    #     darsad_takhfif=i[44],
    #     )
    #

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

    t4 = time.time()
    # پر کردن جدول جزئیات فاکتور
    # cursor.execute("SELECT * FROM Fact_Fo_Detail;")
    # rows=cursor.fetchall()
    # for i in rows:
    #     print(i[0], i[3], i[5], i[6], i[29])
    #     print(i)
    #     print("---------------------------------------------")
    #     FactorDetaile.objects.create(
    #     code_factor=i[0],
    #     code_kala = i[3],
    #     count = i[5],
    #     mablagh_vahed = i[6],
    #     mablagh_nahaee =i[29],
    #     )
    # #

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

    existing_keys  = set((detail.code_factor, detail.radif) for detail in FactorDetaile.objects.all())
    model_to_delete = existing_keys - existing_in_mahak
    for key in model_to_delete:
        FactorDetaile.objects.filter(code_factor=key[0], radif=key[1]).delete()





        #         # پر کردن جدول ناشناس
    # cursor.execute("SELECT * FROM UserEvent;")
    # # rows=cursor.fetchall()
    # # rows = cursor.fetchmany(1000)  # دریافت 1000 ردیف اول
    #
    # # cursor.execute("SELECT * FROM AccDetails ORDER BY id OFFSET 200 ROWS FETCH NEXT 1300 ROWS ONLY;")
    # rows = cursor.fetchall()
    # # دریافت نام ستون‌ها
    # column_names = [desc[0] for desc in cursor.description]
    # print('column_names')
    # print(column_names)
    # # for i in rows:
    #     # print(i[0], i[3], i[5], i[6], i[29])
    #     # print(i)

    t5 = time.time()






    tend = time.time()

    cursor.close()

    total_time = tend - t0
    db_time = t1 - t0
    table_time = t2 - t1
    kala_time = t3 - t2
    factor_time = t4 - t3
    factor_detail_time = t5 - t4

    print(f"زمان کل: {total_time:.2f} ثانیه")
    print(f" اتصال به دیتا بیس:{db_time:.2f} ثانیه")
    print(f"شناسایی جداول:{table_time:.2f} ثانیه")
    print(f"شناسایی کالاها: {kala_time:.2f} ثانیه")
    print(f"فاکتورها {factor_time:.2f} ثانیه")
    print(f"جزئیات فاکتورها {factor_detail_time:.2f} ثانیه")

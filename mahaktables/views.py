from django.shortcuts import render
from django.http import JsonResponse

from mahakupdate.models import Mtables
from mahakupdate.views import connect_to_mahak
from django.contrib.auth.decorators import login_required


def get_table_columns(cursor, table_name):
    cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'")  
    columns = cursor.fetchall()  
    return [col[0] for col in columns]  # استخراج تنها نام ستون‌ها  





def get_all_table_data(cursor):  
        table_data = {}
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        tables = cursor.fetchall()

        # تبدیل به لیست و انتخاب فقط جدول‌های 50 تا 70
        # table_list = [t[0] for t in tables]  # تبدیل به لیست
        # selected_tables = table_list[450:460]  # فقط جدول‌های 50 تا 70 انتخاب می‌شوند

        selected_tables=[]

        mtable=Mtables.objects.filter(row_count__range=(1,100000))
        for m in mtable:
            selected_tables.append(m)


        for table_name in selected_tables:
            try:
                cursor.execute(f"SELECT * FROM {table_name};")
                # rows = cursor.fetchall()
                rows = cursor.fetchmany(20)  # دریافت 1000 ردیف اول

                columns = get_table_columns(cursor, table_name)  # دریافت نام ستون‌ها
                table_data[table_name] = {'rows': rows, 'columns': columns}  # ذخیره نام ستون‌ها به همراه داده‌ها
            except Exception as e:
                pass
                # print(f"خطا در دسترسی به جدول {table_name}: {e}")

        return table_data


@login_required(login_url='/login')
def MTable(request):
    conn = connect_to_mahak()
    cursor = conn.cursor()
    table_data = get_all_table_data(cursor)

    context = {  
        'table_data': table_data,  
    }  

    # conn.close()
    cursor.close()
    return render(request, 'tables.html', context)



def search_in_tables(request, search_text):
    conn = connect_to_mahak()
    cursor = conn.cursor()
    table_data = {}
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    tables = cursor.fetchall()

    selected_tables = []
    mtable = Mtables.objects.filter(row_count__range=(1, 100000))
    for m in mtable:
        selected_tables.append(m.name)

    for table_name in selected_tables:
        try:
            columns = get_table_columns(cursor, table_name)
            for column in columns:
                query = f"SELECT COUNT(*) FROM {table_name} WHERE {column} LIKE '%{search_text}%'"
                cursor.execute(query)
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"Table: {table_name}, Column: {column}, Count: {count}")
                    table_data[f"{table_name} ({column})"] = count
        except Exception as e:
            print(e)

    cursor.close()
    return JsonResponse(table_data)


# views.py

from django.shortcuts import render
from django.db import connection
from django.urls import path

# views.py

from django.shortcuts import render
from django.db import connection
from django.urls import path

# views.py

from django.shortcuts import render
from django.db import connection


# views.py
def list_tables(request):
    conn = connect_to_mahak()
    cursor = conn.cursor()

    # گرفتن اسکیما و نام جدول
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)
    tables = cursor.fetchall()

    table_data = []
    for schema, name in tables:
        full_name = f"{schema}.{name}"
        try:
            # استفاده از نام کامل با براکت
            cursor.execute(f"SELECT COUNT(*) FROM [{schema}].[{name}]")
            row_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            """, schema, name)
            column_count = cursor.fetchone()[0]

            table_data.append({
                'schema': schema,
                'name': name,
                'full_name': full_name,
                'rows': row_count,
                'columns': column_count
            })
        except Exception as e:
            print(f"خطا در دسترسی به جدول {full_name}: {e}")
            table_data.append({
                'schema': schema,
                'name': name,
                'full_name': full_name,
                'rows': 0,
                'columns': 0
            })

    context = {
        'tables': table_data
    }

    cursor.close()
    conn.close()  # مهم: بستن اتصال
    return render(request, 'list_tables.html', context)

# views.py
def get_table_columns(cursor, schema, table):
    """گرفتن لیست ستون‌های یک جدول"""
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """, schema, table)
    return [row[0] for row in cursor.fetchall()]


def table_detail(request, schema_name, table_name):
    conn = connect_to_mahak()
    cursor = conn.cursor()

    search_query = request.GET.get('search', '')
    full_table_name = f"[{schema_name}].[{table_name}]"

    try:
        if search_query:
            # گرفتن ستون‌ها برای جستجو
            columns = get_table_columns(cursor, schema_name, table_name)
            if columns:
                conditions = " OR ".join([f"CAST({col} AS NVARCHAR(MAX)) LIKE '%{search_query}%'" for col in columns])
                query = f"SELECT TOP 1500 * FROM {full_table_name} WHERE {conditions}"
            else:
                query = f"SELECT TOP 1500 * FROM {full_table_name}"
        else:
            query = f"SELECT TOP 1500 * FROM {full_table_name}"

        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]

        context = {
            'schema_name': schema_name,
            'table_name': table_name,
            'full_table_name': f"{schema_name}.{table_name}",
            'columns': columns,
            'rows': rows,
            'search_query': search_query
        }

    except Exception as e:
        context = {
            'schema_name': schema_name,
            'table_name': table_name,
            'full_table_name': f"{schema_name}.{table_name}",
            'columns': [],
            'rows': [],
            'search_query': search_query,
            'error': f"خطا در خواندن جدول: {e}"
        }

    cursor.close()
    conn.close()
    return render(request, 'table_detail.html', context)


def get_table_columns(cursor, table_name):
    cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='{table_name}'")
    return [col[0] for col in cursor.fetchall()]


import csv
import os
import pyodbc
from django.http import HttpResponse
from django.apps import apps


def export_all_tables(request):
    conn = connect_to_mahak()
    cursor = conn.cursor()

    # دریافت لیست جداول
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
    tables = [table[0] for table in cursor.fetchall()]

    for table_name in tables:
        try:
            export_table_to_csv(cursor, table_name)
        except Exception as e:
            print(f"❌ خطا در ذخیره جدول {table_name}: {e}")

    cursor.close()
    conn.close()
    return HttpResponse("✅ همه جداول ذخیره شدند!")

import os
import csv
from django.conf import settings  # دریافت مسیر پروژه

# مسیر پوشه temp را مشخص کنید
TEMP_DIR = os.path.join(settings.BASE_DIR, "temp")

# ایجاد پوشه temp در صورت نبودن
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# نام دیتابیس را دریافت کنیم تا پوشه مخصوص آن ساخته شود
def get_database_name():
    conn = connect_to_mahak()
    cursor = conn.cursor()
    cursor.execute("SELECT DB_NAME()")
    database_name = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return database_name

def export_table_to_csv(cursor, table_name):
    # دریافت نام دیتابیس و ایجاد مسیر ذخیره
    database_name = get_database_name()
    database_dir = os.path.join(TEMP_DIR, database_name)

    # ایجاد پوشه دیتابیس در صورت نبودن
    if not os.path.exists(database_dir):
        os.makedirs(database_dir)

    # مسیر ذخیره فایل در داخل پوشه دیتابیس
    file_path = os.path.join(database_dir, f"{table_name}.csv")

    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    with open(file_path, "w", newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(columns)  # ذخیره نام ستون‌ها
        writer.writerows(rows)  # ذخیره داده‌های جدول

    print(f"✅ جدول {table_name} ذخیره شد در مسیر: {file_path}")

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
def MTables(request):
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





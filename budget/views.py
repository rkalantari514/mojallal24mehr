from django.shortcuts import render

from custom_login.models import UserLog
from custom_login.views import page_permision
from dashboard.models import MasterInfo
from mahakupdate.models import SanadDetail, AccCoding
import time
from django.db.models import Sum, F, DecimalField
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import datetime

# Create your views here.
from django.db.models import Sum, F
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import time

from django.db.models import Sum, F
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import time

from django.db.models import Sum, F, Q
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import time
from django.shortcuts import render


def BudgetCostTotal(request, *args, **kwargs):
    start_time = time.time()
    name = 'کلیات بودجه هزینه ای'
    result = page_permision(request, name)
    if result:
        return result

    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='کلیات بودجه هزینه ای', code=0)

    master_info = MasterInfo.objects.filter(is_active=True).last()
    if not master_info:
        return render(request, 'error_page.html', {'message': 'سال مالی فعالی یافت نشد.'})

    acc_year = master_info.acc_year
    base_year = acc_year - 1
    today = date.today()
    one_year_ago = today - relativedelta(years=1)

    sanads_qs_base_year = SanadDetail.objects.filter(is_active=True, kol=501, acc_year=base_year)

    aggregated_sanads_base_year = sanads_qs_base_year.values('tafzili', 'moin').annotate(
        total_sanad_by=Sum('curramount'),
        total_sanad_by_today=Sum('curramount', filter=Q(date__lte=one_year_ago))
    )

    sanads_qs_current_year = SanadDetail.objects.filter(
        is_active=True, kol=501, acc_year=acc_year, date__lte=today
    ).values('tafzili', 'moin').annotate(
        total_sanad_cy_today=Sum('curramount')
    )

    aggregated_by_lookup = {}
    for item in aggregated_sanads_base_year:
        key = (item['tafzili'], item['moin'])
        aggregated_by_lookup[key] = {
            'total_sanad_by': item['total_sanad_by'] or 0,
            'total_sanad_by_today': item['total_sanad_by_today'] or 0
        }

    aggregated_cy_lookup = {}
    for item in sanads_qs_current_year:
        key = (item['tafzili'], item['moin'])
        aggregated_cy_lookup[key] = item['total_sanad_cy_today'] or 0

    unique_tafzili_codes = sanads_qs_base_year.values_list('tafzili', flat=True).distinct()
    unique_moin_codes = sanads_qs_base_year.values_list('moin', flat=True).distinct()

    all_acc_coding = AccCoding.objects.filter(
        Q(level=3, parent__parent__code=501, code__in=unique_tafzili_codes) |
        Q(level=2, parent__code=501, code__in=unique_moin_codes) |
        Q(level=3, parent__parent__code=501, is_budget=True)
    ).values('code', 'name', 'level', 'parent__code', 'parent__parent__code', 'is_budget', 'budget_rate')

    tafzili_names = {item['code']: item['name'] for item in all_acc_coding if
                     item['level'] == 3 and item['parent__parent__code'] == 501}
    moin_names = {item['code']: item['name'] for item in all_acc_coding if
                  item['level'] == 2 and item['parent__code'] == 501}
    budget_taf_info = {
        item['code']: item['budget_rate'] for item in all_acc_coding
        if item['level'] == 3 and item['parent__parent__code'] == 501 and item['is_budget']
    }
    first_sanad_day = SanadDetail.objects.filter(is_active=True, kol=501, acc_year=acc_year).first().date
    days_from_start = (today - first_sanad_day).days
    day_rate = days_from_start / 365
    print('day_rate', day_rate)

    table3 = []
    for (tafzili_code, moin_code), data in aggregated_by_lookup.items():
        total_sanad_by = data['total_sanad_by']
        total_sanad_by_today = data['total_sanad_by_today']
        total_sanad_cy_today = aggregated_cy_lookup.get((tafzili_code, moin_code), 0)

        moin_name = moin_names.get(moin_code, ' ')
        tafzili_name = tafzili_names.get(tafzili_code, ' ')

        is_budge = tafzili_code in budget_taf_info
        budget_rate = budget_taf_info.get(tafzili_code, '-')
        total_budget_cy = '-'
        total_budget_cy_today = '-'
        total_budget_by = '-'

        amalkard_by_year = '-'
        amalkard_by_year_ratio = '-'
        amalkard1 = True
        amalkard2 = True
        amalkard_by_day = '-'
        amalkard_by_day_ratio = '-'

        if is_budge and budget_rate != '-':
            try:
                rate = Decimal(budget_rate)
                total_budget_cy = total_sanad_by * rate * -1
                total_budget_cy_today = total_sanad_by_today * rate * -1
                total_budget_by = total_sanad_by * -1
                amalkard_by_year = (total_budget_cy_today + total_sanad_cy_today) * -1
                amalkard_by_year_ratio = (amalkard_by_year / total_budget_cy_today) * 100
                if amalkard_by_year > 0:
                    amalkard1 = False
                # amalkard_by_day=(total_budget_by*day_rate)-total_sanad_cy_today
                amalkard_by_day = ((float(total_budget_cy) * day_rate) + float(total_sanad_cy_today)) * -1
                print('amalkard_by_day', amalkard_by_day)
                amalkard_by_day_ratio = (amalkard_by_day / (float(total_budget_cy) * day_rate)) * 100
                if amalkard_by_day > 0:
                    amalkard2 = False
            except Exception as e:
                pass  # در صورت بروز خطا در تبدیل نرخ، از نمایش آن جلوگیری می‌کند

        table3.append({
            'moin_code': moin_code,
            'moin_name': moin_name,
            'tafzili_code': tafzili_code,
            'tafzili_name': tafzili_name,
            'is_budge': is_budge,
            'budget_rate': budget_rate,
            'total_sanad_by': total_sanad_by * -1,
            'total_budget_cy': total_budget_cy,
            'total_budget_by': total_budget_by,
            'total_sanad_by_today': total_sanad_by_today * -1,
            'total_budget_cy_today': total_budget_cy_today,
            'total_sanad_cy_today': total_sanad_cy_today * -1,

            'amalkard_by_year': amalkard_by_year,
            'amalkard_by_year_ratio': amalkard_by_year_ratio,
            'amalkard1': amalkard1,

            'amalkard_by_day': amalkard_by_day,
            'amalkard_by_day_ratio': amalkard_by_day_ratio,
            'amalkard2': amalkard2,

        })

    # -------------------------------- ایجاد جدول 2-----------------------

    # دیکشنری کمکی برای نگهداری جمع مقادیر بر اساس moin_code
    grouped_data = {}

    for entry in table3:
        moin_code = entry['moin_code']
        moin_name = entry['moin_name']

        # اگر moin_code در دیکشنری نیست، آن را اضافه کن و مقدارهای اولیه بده
        if moin_code not in grouped_data:
            grouped_data[moin_code] = {
                'moin_name': moin_name,
                'total_sanad_by': 0,
                'total_budget_cy': 0,
                'total_budget_by': 0,
                'total_sanad_by_today': 0,
                'total_budget_cy_today': 0,
                'total_sanad_cy_today': 0,
            }

        def safe_float(value):
            try:
                val = str(value).strip()
                if val == '-' or val == '':
                    return 0.0
                return float(val)
            except ValueError:
                return 0.0

        # در حلقه جمع‌بندی، از تابع بالا استفاده کن:
        if entry['is_budge']:
            grouped_data[moin_code]['total_sanad_by'] += safe_float(entry['total_sanad_by'])
            grouped_data[moin_code]['total_budget_cy'] += safe_float(entry['total_budget_cy'])
            grouped_data[moin_code]['total_budget_by'] += safe_float(entry['total_budget_by'])
            grouped_data[moin_code]['total_sanad_by_today'] += safe_float(entry['total_sanad_by_today'])
            grouped_data[moin_code]['total_budget_cy_today'] += safe_float(entry['total_budget_cy_today'])
            grouped_data[moin_code]['total_sanad_cy_today'] += safe_float(entry['total_sanad_cy_today'])

    table2 = []
    for moin_code, data in grouped_data.items():
        table2.append({
            'moin_code': moin_code,
            'moin_name': data['moin_name'],
            'total_sanad_by': data['total_sanad_by'],
            'total_budget_cy': data['total_budget_cy'],
            'total_budget_by': data['total_budget_by'],
            'total_sanad_by_today': data['total_sanad_by_today'],
            'total_budget_cy_today': data['total_budget_cy_today'],
            'total_sanad_cy_today': data['total_sanad_cy_today'],
        })

    context = {
        'acc_year': acc_year,
        'base_year': base_year,
        'user': user,
        'table3': table3,
        'table2': table2,
    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")
    return render(request, 'budget_total.html', context)


import time
import datetime
from django.db.models import Sum, Min, Max
from django.db.models import Q
from django.shortcuts import render
# from dateutil.relativedelta import relativedelta # اگر از این استفاده می کنید، مطمئن شوید نصب شده باشد
# from datetime import date # اگر از این استفاده می کنید، مطمئن شوید import شده باشد


import time
import datetime
from django.db.models import Sum, Min, Max
from django.db.models import Q
from django.shortcuts import render

import time
import datetime
import jdatetime  # <--- حتماً این کتابخانه را نصب کنید: pip install jdatetime
from django.db.models import Sum, Min, Max
from django.db.models import Q
from django.shortcuts import render

import time
import datetime
from django.db.models import Sum, Min, Max
from django.db.models import Q
from django.shortcuts import render

import time
import datetime
# jdatetime را حذف کنید اگر قرار نیست شمسی باشد
# import jdatetime # <--- این خط را حذف کنید

from django.db.models import Sum, Min, Max
from django.db.models import Q
from django.shortcuts import render

import time
import datetime
from django.db.models import Sum, Min, Max
from django.db.models import Q
from django.shortcuts import render
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import jdatetime
from datetime import datetime
import jdatetime
from datetime import datetime
def BudgetCostDetail(request, level, code, *args, **kwargs):
    start_time = time.time()
    name = 'جزئیات بودجه هزینه ای'
    result = page_permision(request, name)
    if result:
        return result

    user = request.user
    UserLog.objects.create(user=user, page='جزئیات بودجه هزینه ای', code=code)

    master_info = MasterInfo.objects.filter(is_active=True).last()
    acc_year = master_info.acc_year
    base_year = acc_year - 1
    tafzil = None
    moin_code = None
    tafzili_code = None
    budget_rate = 0  # نرخ بودجه پیش‌فرض

    if level == '3':
        tafzili_code = int(code)
        tafzil = AccCoding.objects.filter(code=tafzili_code, parent__parent__code=501).last()
        if tafzil:
            moin_code = tafzil.parent.code
            budget_rate=tafzil.budget_rate
            if hasattr(tafzil, 'budget_rate') and tafzil.budget_rate is not None and tafzil.budget_rate != 0:
                budget_rate = tafzil.budget_rate
        else:
            print(f"Error: Tafzili with code {tafzili_code} not found for level 3.")
            context = {  # مقداردهی اولیه به context حتی در صورت خطا
                'acc_year': acc_year, 'base_year': base_year, 'user': user,
                'tafzil_name': 'نامشخص', 'budget_rate': budget_rate,
                'chart_labels': [], 'chart_original_base_year_data': [],
                'chart_multiplied_base_year_data': [], 'chart_current_year_data': []
            }
            return render(request, 'budget_cost_detail.html', context)

        # --- ۱. کوئری‌های مربوط به سال پایه (Base Year) ---
        sanad_base_year_qs = SanadDetail.objects.filter(
            is_active=True,
            kol=501,
            moin=moin_code,
            tafzili=tafzili_code,
            acc_year=base_year
        )
        daily_totals_base_year = {}
        if sanad_base_year_qs.exists():
            for item in sanad_base_year_qs.values('date').annotate(total=Sum('curramount')).order_by('date'):
                daily_totals_base_year[str(item['date'])] = -float(item['total'] or 0)

        # --- ۲. کوئری‌های مربوط به سال جاری (Current Year) ---
        sanad_acc_year_qs = SanadDetail.objects.filter(
            is_active=True,
            kol=501,
            moin=moin_code,
            tafzili=tafzili_code,
            acc_year=acc_year
        )
        daily_totals_acc_year = {}
        if sanad_acc_year_qs.exists():
            for item in sanad_acc_year_qs.values('date').annotate(total=Sum('curramount')).order_by('date'):
                daily_totals_acc_year[str(item['date'])] = -float(item['total'] or 0)

        start_date = sanad_base_year_qs.aggregate(min_date=Min('date'))['min_date']
        end_date = sanad_base_year_qs.aggregate(max_date=Max('date'))['max_date']


        start_date = SanadDetail.objects.filter(is_active=True,acc_year=base_year).aggregate(min_date=Min('date'))['min_date']
        end_date = SanadDetail.objects.filter(is_active=True,acc_year=base_year).aggregate(max_date=Max('date'))['max_date']
        # ایجاد لیست روزها
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date.strftime('%Y-%m-%d'))  # قالب تاریخ به YYYY-MM-DD
            current_date += timedelta(days=1)

        for d in date_list:
            print(d)

        print('==============================================================')

        acc_date_list = [datetime.strptime(date, '%Y-%m-%d') + relativedelta(years=1) for date in date_list]
        acc_date_list = [date.strftime('%Y-%m-%d') for date in acc_date_list]

        for d in acc_date_list:
            print(d)


        month_names = {
            1: "فروردین", 2: "اردیبهشت", 3: "خرداد", 4: "تیر",
            5: "مرداد", 6: "شهریور", 7: "مهر", 8: "آبان",
            9: "آذر", 10: "دی", 11: "بهمن", 12: "اسفند"
        }

        chart_labels_shamsi = []
        for date in acc_date_list:
            try:
                miladi_date = datetime.strptime(date, '%Y-%m-%d')  # تبدیل میلادی به datetime
                shamsi_date = jdatetime.date.fromgregorian(day=miladi_date.day, month=miladi_date.month,
                                                           year=miladi_date.year)
                print(shamsi_date,shamsi_date.day)
                # تنظیم نمایش لیبل‌ها بر اساس شرط‌های تعیین‌شده
                if shamsi_date.day == 1:  # نمایش نام ماه برای اولین روز ماه
                    label = month_names[shamsi_date.month]
                    print(')))))))))))))))))))))',label)
                elif shamsi_date.day == 15:  # نمایش تاریخ کامل برای روز ۱۵ هر ماه
                    label = shamsi_date.strftime('%Y-%m-%d')
                else:  # سایر موارد خالی باشند
                    label = shamsi_date.day

                chart_labels_shamsi.append(shamsi_date.strftime('%Y-%m-%d'))

            except ValueError as e:
                print(f"خطای تبدیل تاریخ: {date}, {e}")  # نمایش خطا در صورت وجود مشکل

        for c in chart_labels_shamsi:
            print(c)

        chart_labels = chart_labels_shamsi  # برچسب‌های نمودار همان لیست تاریخ‌ها
        chart1_data = []
        chart2_data = []
        chart3_data = []
        chart4_data = []

        cumulative_base_year = 0
        cumulative_acc_year = 0
        today = datetime.today().strftime('%Y-%m-%d')  # تاریخ امروز به فرمت YYYY-MM-DD
        for day in acc_date_list:
            by_date = datetime.strptime(day, '%Y-%m-%d') + relativedelta(years=-1)  # تاریخ مربوط به سال پایه

            # مقدار روز جاری از سال پایه را دریافت و تجمعی محاسبه کن
            if str(by_date.date()) in daily_totals_base_year:
                cumulative_base_year += daily_totals_base_year[str(by_date.date())]  # علامت منفی برای تصحیح
            chart1_data.append(cumulative_base_year)
            chart3_data.append(cumulative_base_year * budget_rate)

            # مقدار روز جاری از سال جاری را دریافت و تجمعی محاسبه کن
            if day in daily_totals_acc_year:
                cumulative_acc_year += daily_totals_acc_year[day]  # علامت منفی برای تصحیح
            if day < today or day == today:
                chart2_data.append(cumulative_acc_year)

        last_value_chart1 = chart1_data[-1] if chart1_data else None
        count_acc_date_list = len(acc_date_list)
        s=last_value_chart1/count_acc_date_list * budget_rate
        ch4=0
        for day in acc_date_list:
            chart4_data.append(ch4)
            ch4 += s




    context = {
        'acc_year': acc_year,
        'base_year': base_year,
        'user': user,
        'tafzil_name': tafzil.name if tafzil else 'نامشخص',
        'budget_rate': budget_rate,
        'chart_labels': chart_labels,  # لیبل‌های نمودار
        'chart1_data': chart1_data,
        'chart2_data': chart2_data,
        'chart3_data': chart3_data,
        'chart4_data': chart4_data,

    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'budget_cost_detail.html', context)


def BudgetCostDetail2(request, level, code, *args, **kwargs):
    start_time = time.time()
    name = 'جزئیات بودجه هزینه ای'
    result = page_permision(request, name)
    if result:
        return result

    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='جزئیات بودجه هزینه ای', code=code)

    master_info = MasterInfo.objects.filter(is_active=True).last()
    if not master_info:
        return render(request, 'error_page.html', {'message': 'سال مالی فعالی یافت نشد.'})

    acc_year = master_info.acc_year
    base_year = acc_year - 1
    # today = date.today()
    # one_year_ago = today - relativedelta(years=1)
    tafzil = None

    if level == '3':
        tafzili_code = int(code)
        tafzil = AccCoding.objects.filter(code=tafzili_code, parent__parent__code=501).last()
        moin_code = tafzil.parent.code
        budget_rate = tafzil.budget_rate

        sanad_base_year = SanadDetail.objects.filter(
            is_active=True, kol=501, moin=moin_code, tafzili=tafzili_code, acc_year=base_year
        ).order_by('date')

        sanad_base_year_qs = SanadDetail.objects.filter(
            is_active=True, kol=501, moin=moin_code, tafzili=tafzili_code, acc_year=base_year
        ).values('date', 'curramount')
        sanad_base_year_list = list(sanad_base_year_qs)

        dates_in_db = sanad_base_year_qs.values_list('date', flat=True)
        min_date = min(dates_in_db)
        max_date = max(dates_in_db)

        start_date = min_date
        end_date = max_date
        total_days = (end_date - start_date).days + 1
        full_dates = [start_date + datetime.timedelta(days=i) for i in range(total_days)]

        sanads_acc_year = SanadDetail.objects.filter(is_active=True, kol=501, moin=moin_code, tafzili=tafzili_code,
                                                     acc_year=base_year)

    dates = sanad_base_year.values_list('date', flat=True).distinct().order_by('date')

    daily_totals = {}
    for date1 in full_dates:
        total_for_date = sanad_base_year.filter(date=date1).aggregate(total=Sum('curramount'))['total'] or 0
        daily_totals[str(date1)] = -float(total_for_date)  # منفی کردن مقدار

    # محاسبه تجمعی
    cumulative = []
    sum_so_far = 0
    dates_str = []
    for date in dates:
        date_str = str(date)
        sum_so_far += daily_totals[date_str]
        cumulative.append(sum_so_far)
        dates_str.append(date_str)

    context = {
        'acc_year': acc_year,
        'base_year': base_year,
        'user': user,

        'labels': dates_str,  # تاریخ‌ها
        'data': cumulative,  # مجموعه تجمعی منفی

    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")
    return render(request, 'budget_cost_detail.html', context)


def BudgetTotal1(request, *args, **kwargs):
    start_time = time.time()
    name = 'کلیات بودجه'
    result = page_permision(request, name)
    if result:
        return result
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='کلیات بودجه', code=0)

    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
    base_year = acc_year - 1
    today = date.today()
    one_year_ago = today - relativedelta(years=1)

    sanads_qs = SanadDetail.objects.filter(is_active=True, kol=501, acc_year=base_year)

    # فهرست کامل tafzili های یکتا در این بازه
    unique_tafzili = sanads_qs.exclude(tafzili__isnull=True).values_list('tafzili', flat=True).distinct().order_by(
        'tafzili')

    tafzili_names_qs = AccCoding.objects.filter(
        level=3, parent__parent__code=501, code__in=unique_tafzili
    ).values('code', 'name')

    tafzili_names = {item['code']: item['name'] for item in tafzili_names_qs}

    table3 = []
    budget_taf_ids = list(
        AccCoding.objects.filter(
            level=3,
            parent__parent__code=501,
            is_budget=True
        ).values_list('code', flat=True).distinct()
    )
    for tafzili_code in unique_tafzili:
        sanads_tafzili = sanads_qs.filter(tafzili=tafzili_code)
        moin_code = sanads_tafzili.last().moin
        moin_name = AccCoding.objects.filter(level=2, code=moin_code, parent__code=501).last().name
        total_sanad_by = sanads_tafzili.aggregate(curr=Sum('curramount'))['curr'] or 0

        total_sanad_by_today = sanads_tafzili.filter(date__lte=one_year_ago).aggregate(curr=Sum('curramount'))[
                                   'curr'] or 0

        total_sanad_cy_today = \
            SanadDetail.objects.filter(is_active=True, kol=501, acc_year=acc_year, date__lte=today,
                                       tafzili=tafzili_code,
                                       moin=moin_code).aggregate(curr=Sum('curramount'))['curr'] or 0

        tafzili_name = tafzili_names.get(tafzili_code, ' ')
        is_budge = False
        budget_rate = '-'
        total_budget_cy = '-'
        total_budget_cy_today = '-'
        if tafzili_code in budget_taf_ids:
            is_budge = True
            budget_rate = AccCoding.objects.filter(level=3, parent__code=moin_code,
                                                   parent__parent__code=501).last().budget_rate
            total_budget_cy = total_sanad_by * Decimal(budget_rate)
            total_budget_cy_today = total_sanad_by_today * Decimal(budget_rate)

        table3.append({
            'moin_code': moin_code,
            'moin_name': moin_name,
            'tafzili_code': tafzili_code,
            'tafzili_name': tafzili_name,
            'is_budge': is_budge,
            'budget_rate': budget_rate,
            'total_sanad_by': total_sanad_by,
            'total_budget_cy': total_budget_cy,
            'total_sanad_by_today': total_sanad_by_today,
            'total_budget_cy_today': total_budget_cy_today,
            'total_sanad_cy_today': total_sanad_cy_today,

        })

    for item in table3:
        print(item['code'])
        print(item['tafzili_name'])
        print(item['moin_name'])
        print(item['total_sanad'])
        print(item['budget_sanad'])
        print('-----------------------------')

    context = {
        'acc_year': acc_year,
        'base_year': base_year,
        'user': user,
        'table3': table3,
    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")
    return render(request, 'budget_total.html', context)

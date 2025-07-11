from unicodedata import category

from custom_login.models import UserLog
from custom_login.views import page_permision
from dashboard.models import MasterInfo
from mahakupdate.models import SanadDetail, AccCoding, FactorDetaile, Category, Kala, Factor
from datetime import date
from decimal import Decimal

from mahakupdate.views import jalali_to_gregorian


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
                'amalkard_by_year': 0,
                'amalkard_by_day': 0,
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
            grouped_data[moin_code]['amalkard_by_year'] += safe_float(entry['amalkard_by_year'])
            grouped_data[moin_code]['amalkard_by_day'] += safe_float(entry['amalkard_by_day'])

    table2 = []
    for moin_code, data in grouped_data.items():
        amalkard1 = True
        if data['amalkard_by_year'] > 0:
            amalkard1 = False
        amalkard2 = True
        if data['amalkard_by_day'] > 0:
            amalkard2 = False

        table2.append({
            'moin_code': moin_code,
            'moin_name': data['moin_name'],
            'total_sanad_by': data['total_sanad_by'],
            'total_budget_cy': data['total_budget_cy'],
            'total_budget_by': data['total_budget_by'],
            'total_sanad_by_today': data['total_sanad_by_today'],
            'total_budget_cy_today': data['total_budget_cy_today'],
            'total_sanad_cy_today': data['total_sanad_cy_today'],
            'amalkard_by_year': data['amalkard_by_year'],
            'amalkard_by_year_ratio': data['amalkard_by_year'] / data['total_budget_cy_today'] * 100,
            'amalkard1': amalkard1,
            'amalkard_by_day': data['amalkard_by_day'],
            'amalkard_by_day_ratio': (data['amalkard_by_day'] / (float(data['total_budget_cy']) * day_rate)) * 100,
            'amalkard2': amalkard2,

        })

        acc_code_2 = AccCoding.objects.filter(level=2, code=moin_code, parent__code=501).last()
        br = data['total_budget_cy'] / data['total_sanad_by']
        if acc_code_2.budget_rate != br:
            acc_code_2.budget_rate = br
            acc_code_2.save()

    # ----------------------------------ساخت جدول 1 ----------------------------

    # دیکشنری کمکی برای نگهداری جمع کل داده‌ها
    summary_data = {
        'total_sanad_by': 0,
        'total_budget_cy': 0,
        'total_budget_by': 0,
        'total_sanad_by_today': 0,
        'total_budget_cy_today': 0,
        'total_sanad_cy_today': 0,
        'amalkard_by_year': 0,
        'amalkard_by_day': 0,
    }
    table1 = []

    # جمع‌بندی مقادیر از table2
    for entry in table2:
        summary_data['total_sanad_by'] += entry['total_sanad_by']
        summary_data['total_budget_cy'] += entry['total_budget_cy']
        summary_data['total_budget_by'] += entry['total_budget_by']
        summary_data['total_sanad_by_today'] += entry['total_sanad_by_today']
        summary_data['total_budget_cy_today'] += entry['total_budget_cy_today']
        summary_data['total_sanad_cy_today'] += entry['total_sanad_cy_today']
        summary_data['amalkard_by_year'] += entry['amalkard_by_year']
        summary_data['amalkard_by_day'] += entry['amalkard_by_day']

    # محاسبه نسبت‌های عملکرد
    amalkard1 = summary_data['amalkard_by_year'] <= 0
    amalkard2 = summary_data['amalkard_by_day'] <= 0

    summary_data['amalkard_by_year_ratio'] = (
        summary_data['amalkard_by_year'] / summary_data['total_budget_cy_today'] * 100
        if summary_data['total_budget_cy_today'] != 0 else 0
    )

    summary_data['amalkard_by_day_ratio'] = (
        (summary_data['amalkard_by_day'] / (float(summary_data['total_budget_cy']) * day_rate)) * 100
        if summary_data['total_budget_cy'] != 0 else 0
    )

    # اضافه کردن داده‌های خلاصه‌شده به table1
    table1.append({
        'total_sanad_by': summary_data['total_sanad_by'],
        'total_budget_cy': summary_data['total_budget_cy'],
        'total_budget_by': summary_data['total_budget_by'],
        'total_sanad_by_today': summary_data['total_sanad_by_today'],
        'total_budget_cy_today': summary_data['total_budget_cy_today'],
        'total_sanad_cy_today': summary_data['total_sanad_cy_today'],
        'amalkard_by_year': summary_data['amalkard_by_year'],
        'amalkard_by_year_ratio': summary_data['amalkard_by_year_ratio'],
        'amalkard1': amalkard1,
        'amalkard_by_day': summary_data['amalkard_by_day'],
        'amalkard_by_day_ratio': summary_data['amalkard_by_day_ratio'],
        'amalkard2': amalkard2,
    })

    acc_code_1 = AccCoding.objects.filter(level=1, code=501).last()
    br = data['total_budget_cy'] / data['total_sanad_by']
    if acc_code_1.budget_rate != br:
        acc_code_1.budget_rate = br
        acc_code_1.save()

    context = {
        'acc_year': acc_year,
        'base_year': base_year,
        'user': user,
        'table3': table3,
        'table2': table2,
        'table1': table1,
    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")
    return render(request, 'budget_cost_total.html', context)


import time
import datetime
from django.db.models import Sum, Min, Max
from django.db.models import Q
from django.shortcuts import render
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import jdatetime
from django.db.models import Sum, Subquery # مطمئن شوید Subquery را ایمپورت کرده‌اید


def BudgetCostDetail(request, level, code, *args, **kwargs):
    start_time = time.time()
    name = 'جزئیات بودجه هزینه ای'
    result = page_permision(request, name)
    if result:
        return result

    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='کلیات بودجه هزینه ای', code=0)

    master_info = MasterInfo.objects.filter(is_active=True).last()
    acc_year = master_info.acc_year
    base_year = acc_year - 1
    tafzil = None
    moin_code = None
    tafzili_code = None
    g1 = -70
    g2 = 43
    today_bay_by = 0
    today_actual = 0
    today_by_time = 0
    budget_rate = 0  # نرخ بودجه پیش‌فرض
    level1 = AccCoding.objects.filter(level=1, code=501)
    kol_code = None
    moin_code = None
    level2 = AccCoding.objects.filter(level=2, parent__code=501)
    level3 = None
    tafzili_code = None

    if level == '3':
        tafzili_code = int(code)
        tafzil = AccCoding.objects.filter(code=tafzili_code, parent__parent__code=501).last()
        detail_name = f'سطح تفضیل - {tafzil.name}-{tafzili_code}'
        moin_code = int(tafzil.parent.code)
        level3 = AccCoding.objects.filter(level=3, parent__parent__code=501, parent__code=moin_code, is_budget=True)

        if tafzil:
            moin_code = tafzil.parent.code
            budget_rate = tafzil.budget_rate
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

        start_date = SanadDetail.objects.filter(is_active=True, acc_year=base_year).aggregate(min_date=Min('date'))[
            'min_date']
        end_date = SanadDetail.objects.filter(is_active=True, acc_year=base_year).aggregate(max_date=Max('date'))[
            'max_date']
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
                print(shamsi_date, shamsi_date.day)
                # تنظیم نمایش لیبل‌ها بر اساس شرط‌های تعیین‌شده
                if shamsi_date.day == 1:  # نمایش نام ماه برای اولین روز ماه
                    label = month_names[shamsi_date.month]
                    print(')))))))))))))))))))))', label)
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
            if day == today:
                today_bay_by = cumulative_base_year * budget_rate

            # مقدار روز جاری از سال جاری را دریافت و تجمعی محاسبه کن
            if day in daily_totals_acc_year:
                cumulative_acc_year += daily_totals_acc_year[day]  # علامت منفی برای تصحیح
            if day <= today:
                chart2_data.append(cumulative_acc_year)
                if day == today:
                    today_actual = cumulative_acc_year

        last_value_chart1 = chart1_data[-1] if chart1_data else None
        count_acc_date_list = len(acc_date_list)
        s = last_value_chart1 / count_acc_date_list * budget_rate
        ch4 = 0
        for day in acc_date_list:
            chart4_data.append(ch4)
            if day == today:
                today_by_time = ch4

            ch4 += s
        last_value_chart2 = chart2_data[-1] if chart2_data else None
        master_dat = {
            'by_sanads': last_value_chart1 / 10,
            'cy_budget': last_value_chart1 / 10 * budget_rate,
            'budget_rate': budget_rate,
            'cy_sanads': last_value_chart2 / 10

        }

        print('today_bay_by,today_actual,today_by_time')
        print(today_bay_by, today_actual, today_by_time)

        g1 = ((today_actual - today_bay_by) / today_bay_by * 100) if today_bay_by != 0 else 100
        g2 = ((today_actual - today_by_time) / today_by_time * 100) if today_by_time != 0 else 100
        print(g1, g2)

    if level == '2':
        moin_code = int(code)
        moin = AccCoding.objects.filter(level=2, code=moin_code, parent__code=501).last()
        detail_name = f'سطح معین - {moin.name}-{moin_code}'
        level3 = AccCoding.objects.filter(level=3, parent__parent__code=501, parent__code=moin_code, is_budget=True)

        budget_rate = moin.budget_rate

        tafzili_code_list = [
            t.code for t in AccCoding.objects.filter(
                level=3, parent__code=moin.code, parent__parent__code=501, is_budget=True
            )
        ]

        # --- ۱. کوئری‌های مربوط به سال پایه (Base Year) ---
        sanad_base_year_qs = SanadDetail.objects.filter(
            is_active=True,
            kol=501,
            moin=moin_code,
            tafzili__in=tafzili_code_list,
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
            tafzili__in=tafzili_code_list,
            acc_year=acc_year
        )
        daily_totals_acc_year = {}
        if sanad_acc_year_qs.exists():
            for item in sanad_acc_year_qs.values('date').annotate(total=Sum('curramount')).order_by('date'):
                daily_totals_acc_year[str(item['date'])] = -float(item['total'] or 0)

        start_date = SanadDetail.objects.filter(is_active=True, acc_year=base_year).aggregate(min_date=Min('date'))[
            'min_date']
        end_date = SanadDetail.objects.filter(is_active=True, acc_year=base_year).aggregate(max_date=Max('date'))[
            'max_date']
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
                print(shamsi_date, shamsi_date.day)
                # تنظیم نمایش لیبل‌ها بر اساس شرط‌های تعیین‌شده
                if shamsi_date.day == 1:  # نمایش نام ماه برای اولین روز ماه
                    label = month_names[shamsi_date.month]
                    print(')))))))))))))))))))))', label)
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
        chart3_d = 0
        today = datetime.today().strftime('%Y-%m-%d')  # تاریخ امروز به فرمت YYYY-MM-DD
        for day in acc_date_list:
            by_date = datetime.strptime(day, '%Y-%m-%d') + relativedelta(years=-1)  # تاریخ مربوط به سال پایه

            # مقدار روز جاری از سال پایه را دریافت و تجمعی محاسبه کن
            if str(by_date.date()) in daily_totals_base_year:
                cumulative_base_year += daily_totals_base_year[str(by_date.date())]  # علامت منفی برای تصحیح
            chart1_data.append(cumulative_base_year)
            chart3_data.append(cumulative_base_year * budget_rate)
            if day == today:
                today_bay_by = cumulative_base_year * budget_rate

            # مقدار روز جاری از سال جاری را دریافت و تجمعی محاسبه کن
            if day in daily_totals_acc_year:
                cumulative_acc_year += daily_totals_acc_year[day]  # علامت منفی برای تصحیح
            if day <= today:
                chart2_data.append(cumulative_acc_year)
                if day == today:
                    today_actual = cumulative_acc_year

        last_value_chart3 = chart3_data[-1] if chart3_data else None
        count_acc_date_list = len(acc_date_list)
        s = last_value_chart3 / count_acc_date_list
        ch4 = 0
        for day in acc_date_list:
            chart4_data.append(ch4)
            if day == today:
                today_by_time = ch4
            ch4 += s

        last_value_chart2 = chart2_data[-1] if chart2_data else None
        last_value_chart1 = chart1_data[-1] if chart1_data else None
        master_dat = {
            'by_sanads': last_value_chart1 / 10,
            'cy_budget': last_value_chart1 / 10 * budget_rate,
            'budget_rate': budget_rate,
            'cy_sanads': last_value_chart2 / 10

        }

        print('today_bay_by,today_actual,today_by_time')
        print(today_bay_by, today_actual, today_by_time)

        g1 = ((today_actual - today_bay_by) / today_bay_by * 100) if today_bay_by != 0 else 100
        g2 = ((today_actual - today_by_time) / today_by_time * 100) if today_by_time != 0 else 100
        print(g1, g2)

    if level == '1':
        kol_code = int(code)

        kol = AccCoding.objects.filter(level=1, code=kol_code).last()
        detail_name = f'سطح کل - {kol.name}-{kol_code}'

        budget_rate = kol.budget_rate

        tafzili_code_list = [
            t.code for t in AccCoding.objects.filter(
                level=3, parent__parent__code=kol_code, is_budget=True
            )
        ]

        # --- ۱. کوئری‌های مربوط به سال پایه (Base Year) ---
        sanad_base_year_qs = SanadDetail.objects.filter(
            is_active=True,
            kol=kol_code,
            tafzili__in=tafzili_code_list,
            acc_year=base_year
        )
        daily_totals_base_year = {}
        if sanad_base_year_qs.exists():
            for item in sanad_base_year_qs.values('date').annotate(total=Sum('curramount')).order_by('date'):
                daily_totals_base_year[str(item['date'])] = -float(item['total'] or 0)

        # --- ۲. کوئری‌های مربوط به سال جاری (Current Year) ---
        sanad_acc_year_qs = SanadDetail.objects.filter(
            is_active=True,
            kol=kol_code,
            tafzili__in=tafzili_code_list,
            acc_year=acc_year
        )
        daily_totals_acc_year = {}
        if sanad_acc_year_qs.exists():
            for item in sanad_acc_year_qs.values('date').annotate(total=Sum('curramount')).order_by('date'):
                daily_totals_acc_year[str(item['date'])] = -float(item['total'] or 0)

        start_date = SanadDetail.objects.filter(is_active=True, acc_year=base_year).aggregate(min_date=Min('date'))[
            'min_date']
        end_date = SanadDetail.objects.filter(is_active=True, acc_year=base_year).aggregate(max_date=Max('date'))[
            'max_date']
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
                print(shamsi_date, shamsi_date.day)
                # تنظیم نمایش لیبل‌ها بر اساس شرط‌های تعیین‌شده
                if shamsi_date.day == 1:  # نمایش نام ماه برای اولین روز ماه
                    label = month_names[shamsi_date.month]
                    print(')))))))))))))))))))))', label)
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
        chart1_data = []  # عکلکرد سال گذشته
        chart2_data = []  # عملکرد امسال تا امروز
        chart3_data = []  # بودجه با آهنگ پارسال
        chart4_data = []  # بودجه با تناسب زمان

        cumulative_base_year = 0
        cumulative_acc_year = 0
        chart3_d = 0
        today = datetime.today().strftime('%Y-%m-%d')  # تاریخ امروز به فرمت YYYY-MM-DD
        for day in acc_date_list:
            by_date = datetime.strptime(day, '%Y-%m-%d') + relativedelta(years=-1)  # تاریخ مربوط به سال پایه

            # مقدار روز جاری از سال پایه را دریافت و تجمعی محاسبه کن
            if str(by_date.date()) in daily_totals_base_year:
                cumulative_base_year += daily_totals_base_year[str(by_date.date())]  # علامت منفی برای تصحیح
            chart1_data.append(cumulative_base_year)
            chart3_data.append(cumulative_base_year * budget_rate)
            if day == today:
                today_bay_by = cumulative_base_year * budget_rate

            # مقدار روز جاری از سال جاری را دریافت و تجمعی محاسبه کن
            if day in daily_totals_acc_year:
                cumulative_acc_year += daily_totals_acc_year[day]  # علامت منفی برای تصحیح
            if day <= today:
                chart2_data.append(cumulative_acc_year)
                if day == today:
                    today_actual = cumulative_acc_year

        last_value_chart3 = chart3_data[-1] if chart3_data else None
        count_acc_date_list = len(acc_date_list)
        s = last_value_chart3 / count_acc_date_list
        ch4 = 0
        for day in acc_date_list:
            chart4_data.append(ch4)
            if day == today:
                today_by_time = ch4
            ch4 += s
        last_value_chart2 = chart2_data[-1] if chart2_data else None
        last_value_chart1 = chart1_data[-1] if chart1_data else None
        master_dat = {
            'by_sanads': last_value_chart1 / 10,
            'cy_budget': last_value_chart1 / 10 * budget_rate,
            'budget_rate': budget_rate,
            'cy_sanads': last_value_chart2 / 10

        }

        print('today_bay_by,today_actual,today_by_time')
        print(today_bay_by, today_actual, today_by_time)

        g1 = ((today_actual - today_bay_by) / today_bay_by * 100) if today_bay_by != 0 else 100
        g2 = ((today_actual - today_by_time) / today_by_time * 100) if today_by_time != 0 else 100
        print(g1, g2)

    g1 = max(-100, min(g1, 100))
    g2 = max(-100, min(g2, 100))

    context = {
        'acc_year': acc_year,
        'base_year': base_year,
        'user': user,
        'detail_name': detail_name,
        'budget_rate': budget_rate,
        'chart_labels': chart_labels,  # لیبل‌های نمودار
        'chart1_data': chart1_data,
        'chart2_data': chart2_data,
        'chart3_data': chart3_data,
        'chart4_data': chart4_data,

        'level': int(level),
        'level1': level1,
        'level2': level2,
        'level3': level3,
        'kol_code': kol_code,
        'moin_code': moin_code,
        'tafzili_code': tafzili_code,

        'master_dat': master_dat,

        'g1': g1,
        'g2': g2,

    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'budget_cost_detail.html', context)


def BudgetSaleTotal(request, *args, **kwargs):
    start_time = time.time()
    name = 'کلیات بودجه فروش'
    result = page_permision(request, name)

    if result:
        return result
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='کلیات بودجه فروش', code=0)
    master_info = MasterInfo.objects.filter(is_active=True).last()
    if not master_info:
        return render(request, 'error_page.html', {'message': 'سال مالی فعالی یافت نشد.'})
    acc_year = master_info.acc_year
    base_year = acc_year - 1
    today = date.today()
    one_year_ago = today - relativedelta(years=1)

    first_factor_day = FactorDetaile.objects.filter(acc_year=acc_year).first().factor.date
    days_from_start = (today - first_factor_day).days
    day_rate = days_from_start / 365

    level3 = Category.objects.filter(level=3)
    today = date.today()
    one_year_ago = today - relativedelta(years=1)

    # =======   محاسبات هزینه مشترک==================

    budget_tafzili_codes_subquery = AccCoding.objects.filter(
        level=3,
        is_budget=True
    ).values('code')





    table3 = []
    for cat in level3:
        by_factor = \
            FactorDetaile.objects.filter(kala__category=cat, acc_year=base_year).aggregate(
                forosh=Sum('mablagh_after_takhfif_kol'))[
                'forosh']
        cy_factor = \
            FactorDetaile.objects.filter(kala__category=cat, acc_year=acc_year).aggregate(
                forosh=Sum('mablagh_after_takhfif_kol'))[
                'forosh'] or 0
        by_today_factor = \
            FactorDetaile.objects.filter(kala__category=cat, acc_year=base_year,
                                         factor__date__lte=one_year_ago).aggregate(
                forosh=Sum('mablagh_after_takhfif_kol'))['forosh']
        budget_rate = 0
        category1 = cat
        for _ in range(3):  # بررسی cat و دو سطح از والدها
            br = getattr(category1, 'budget_rate', 0)
            if br and br > 0:
                budget_rate = br
                break
            category1 = getattr(category1, 'parent', None)
            if category1 is None:
                break

        cy_budget = (Decimal(by_factor) if by_factor is not None else Decimal(0)) * (
            Decimal(budget_rate) if budget_rate is not None else Decimal(0))

        cy_today_budget = (Decimal(by_today_factor) if by_today_factor is not None else Decimal(0)) * (
            Decimal(budget_rate) if budget_rate is not None else Decimal(0))
        if cy_today_budget != 0:
            amalkard_by_year_ratio = ((Decimal(cy_factor) / cy_today_budget) - Decimal(1.0)) * Decimal(100.0)
        else:
            amalkard_by_year_ratio = 0

        amalkard1 = False

        if amalkard_by_year_ratio > 0:
            amalkard1 = True

        cy_today_budget_line = Decimal(day_rate) * cy_budget
        if cy_today_budget_line != 0:
            amalkard_by_line_ratio = ((Decimal(cy_factor) / cy_today_budget_line) - Decimal(1.0)) * Decimal(100.0)
        else:
            amalkard_by_line_ratio = 0

        amalkard2 = False

        if amalkard_by_line_ratio > 0:
            amalkard2 = True

        actual_ratio_by_year = Decimal(cy_factor) / Decimal(
            by_today_factor) if by_today_factor and by_today_factor != 0 else 0.0







        table3.append({
            'l1': cat.parent.parent.name,
            'l2': cat.parent.name,
            'l3': cat.name,
            'cat_id': cat.id,
            'cat_par_id': cat.parent.id,
            'cat_par_par_id': cat.parent.parent.id,
            'by_factor': by_factor,
            'cy_budget': cy_budget,
            'budget_rate': budget_rate,
            'by_today_factor': by_today_factor,

            'cy_today_budget': cy_today_budget,
            'cy_today_budget_line': cy_today_budget_line,
            'cy_factor': cy_factor,
            'amalkard_by_year_ratio': amalkard_by_year_ratio,
            'amalkard_by_line_ratio': amalkard_by_line_ratio,
            'amalkard1': amalkard1,
            'amalkard2': amalkard2,
            'actual_ratio_by_year': actual_ratio_by_year,

        })

    no_cat_by_factor = \
        FactorDetaile.objects.filter(kala__isnull=True, acc_year=base_year).aggregate(
            forosh=Sum('mablagh_after_takhfif_kol'))[
            'forosh']
    no_cat_cy_factor = \
        FactorDetaile.objects.filter(kala__isnull=True, acc_year=acc_year).aggregate(
            forosh=Sum('mablagh_after_takhfif_kol'))[
            'forosh'] or 0
    no_cat_by_today_factor = \
        FactorDetaile.objects.filter(kala__isnull=True, acc_year=base_year, factor__date__lte=one_year_ago).aggregate(
            forosh=Sum('mablagh_after_takhfif_kol'))['forosh']

    table3.append({
        'l1': 'کالای حذف شده_',
        'l2': 'کالای حذف شده__',
        'l3': 'کالای حذف شده___',

        'cat_id': None,
        'cat_par_id': None,
        'cat_par_par_id': None,
        'by_factor': no_cat_by_factor,
        'cy_budget': 0,
        'budget_rate': 0,
        'by_today_factor': no_cat_by_today_factor,

        'cy_today_budget': 0,
        'cy_today_budget_line': 0,
        'cy_factor': no_cat_cy_factor,
        'amalkard_by_year_ratio': 0,
        'amalkard_by_line_ratio': 0,
        'amalkard1': amalkard1,
        'amalkard2': amalkard2,
        'actual_ratio_by_year': actual_ratio_by_year,

    })
    # ==============================================  table2
    # دیکشنری کمکی برای نگهداری جمع مقادیر بر اساس لایه‌های l1 و l2
    grouped_data = {}

    for entry in table3:
        l1 = entry['l1']
        l2 = entry['l2']
        cat_par_id = entry['cat_par_id']
        cat_par_par_id = entry['cat_par_par_id']
        by_factor = entry['by_factor']

        # کلید گروه‌بندی ترکیبی از l1 و l2
        group_key = (l1, l2)

        if group_key not in grouped_data:
            grouped_data[group_key] = {
                'l1': l1,
                'l2': l2,
                'by_factor': 0,
                'cy_budget': 0,
                'cy_today_budget': 0,
                'cy_today_budget_line': 0,
                'cy_factor': 0,
                'by_today_factor': 0,
                'cat_par_id': cat_par_id,
                'cat_par_par_id': cat_par_par_id,
            }

        def safe_float(value):
            try:
                val = str(value).strip()
                if val == '-' or val == '':
                    return 0.0
                return float(val)
            except ValueError:
                return 0.0

        # جمع کردن مقادیر بر اساس شرط
        # if entry['by_factor'] != 0:
        grouped_data[group_key]['by_factor'] += safe_float(entry['by_factor'])
        grouped_data[group_key]['cy_budget'] += safe_float(entry['cy_budget'])
        grouped_data[group_key]['cy_today_budget'] += safe_float(entry['cy_today_budget'])
        grouped_data[group_key]['cy_today_budget_line'] += safe_float(entry['cy_today_budget_line'])
        grouped_data[group_key]['cy_factor'] += safe_float(entry['cy_factor'])
        grouped_data[group_key]['by_today_factor'] += safe_float(entry['by_today_factor'])

    # ساخت جدول نهایی
    table2 = []

    for key, data in grouped_data.items():
        # محاسبه نسبت budget_rate
        budget_rate = data['cy_budget'] / data['by_factor'] if data['by_factor'] != 0 else 0

        if data['cy_today_budget'] != 0:
            amalkard_by_year_ratio = ((Decimal(data['cy_factor']) / Decimal(data['cy_today_budget'])) - Decimal(
                1.0)) * Decimal(100.0)
        else:
            amalkard_by_year_ratio = 0

        amalkard1 = False

        if amalkard_by_year_ratio > 0:
            amalkard1 = True

        cy_today_budget_line = Decimal(day_rate) * Decimal(data['cy_budget'])
        if cy_today_budget_line != 0:
            amalkard_by_line_ratio = ((Decimal(data['cy_factor']) / cy_today_budget_line) - Decimal(1.0)) * Decimal(
                100.0)
        else:
            amalkard_by_line_ratio = 0

        amalkard2 = False

        if amalkard_by_line_ratio > 0:
            amalkard2 = True

        actual_ratio_by_year = Decimal(data['cy_factor']) / Decimal(data['by_today_factor']) if data[
                                                                                                    'by_today_factor'] and \
                                                                                                data[
                                                                                                    'by_today_factor'] != 0 else 0.0

        table2.append({
            'l1': data['l1'],
            'l2': data['l2'],
            'cat_id': data['cat_par_id'],
            'by_factor': data['by_factor'],
            'cy_budget': data['cy_budget'],
            'budget_rate': budget_rate,
            'cy_today_budget': data['cy_today_budget'],
            'cy_today_budget_line': data['cy_today_budget_line'],
            'cy_factor': data['cy_factor'],
            'by_today_factor': data['by_today_factor'],
            'cat_par_par_id': data['cat_par_par_id'],

            'amalkard_by_year_ratio': amalkard_by_year_ratio,
            'amalkard_by_line_ratio': amalkard_by_line_ratio,
            'amalkard1': amalkard1,
            'amalkard2': amalkard2,
            'actual_ratio_by_year': actual_ratio_by_year,
        })

    # =======================================table1
    # دیکشنری کمکی برای نگهداری جمع مقادیر بر اساس لایه‌های l1
    grouped_data = {}

    for entry in table3:
        l1 = entry['l1']
        cat_par_par_id = entry['cat_par_par_id']
        # حذف l2
        # l2 = entry['l2']
        by_factor = entry['by_factor']

        # کلید گروه‌بندی فقط بر اساس l1
        group_key = l1

        if group_key not in grouped_data:
            grouped_data[group_key] = {
                'l1': l1,
                'cat_par_par_id': cat_par_par_id,
                'by_factor': 0,
                'cy_budget': 0,
                'cy_today_budget': 0,
                'cy_today_budget_line': 0,
                'cy_factor': 0,
                'by_today_factor': 0,
            }

        def safe_float(value):
            try:
                val = str(value).strip()
                if val == '-' or val == '':
                    return 0.0
                return float(val)
            except ValueError:
                return 0.0

        # جمع کردن مقادیر بر اساس شرط
        grouped_data[group_key]['by_factor'] += safe_float(entry['by_factor'])
        grouped_data[group_key]['cy_budget'] += safe_float(entry['cy_budget'])
        grouped_data[group_key]['cy_today_budget'] += safe_float(entry['cy_today_budget'])
        grouped_data[group_key]['cy_today_budget_line'] += safe_float(entry['cy_today_budget_line'])
        grouped_data[group_key]['cy_factor'] += safe_float(entry['cy_factor'])
        grouped_data[group_key]['by_today_factor'] += safe_float(entry['by_today_factor'])

    # ساخت جدول نهایی
    table1 = []

    for key, data in grouped_data.items():
        # محاسبه نسبت budget_rate
        budget_rate = data['cy_budget'] / data['by_factor'] if data['by_factor'] != 0 else 0

        if data['cy_today_budget'] != 0:
            amalkard_by_year_ratio = ((Decimal(data['cy_factor']) / Decimal(data['cy_today_budget'])) - Decimal(
                1.0)) * Decimal(100.0)
        else:
            amalkard_by_year_ratio = 0

        amalkard1 = False
        if amalkard_by_year_ratio > 0:
            amalkard1 = True

        cy_today_budget_line = Decimal(day_rate) * Decimal(data['cy_budget'])
        if cy_today_budget_line != 0:
            amalkard_by_line_ratio = ((Decimal(data['cy_factor']) / cy_today_budget_line) - Decimal(1.0)) * Decimal(
                100.0)
        else:
            amalkard_by_line_ratio = 0

        amalkard2 = False
        if amalkard_by_line_ratio > 0:
            amalkard2 = True
        actual_ratio_by_year = Decimal(data['cy_factor']) / Decimal(data['by_today_factor']) if data[
                                                                                                    'by_today_factor'] and \
                                                                                                data[
                                                                                                    'by_today_factor'] != 0 else 0.0

        table1.append({
            'l1': data['l1'],
            'cat_id': data['cat_par_par_id'],
            # حذف 'l2'
            'by_factor': data['by_factor'],
            'cy_budget': data['cy_budget'],
            'budget_rate': budget_rate,
            'cy_today_budget': data['cy_today_budget'],
            'cy_today_budget_line': data['cy_today_budget_line'],
            'cy_factor': data['cy_factor'],
            'amalkard_by_year_ratio': amalkard_by_year_ratio,
            'amalkard_by_line_ratio': amalkard_by_line_ratio,
            'amalkard1': amalkard1,
            'amalkard2': amalkard2,
            'by_today_factor': data['by_today_factor'],
            'actual_ratio_by_year': actual_ratio_by_year,
        })

    # =========================================  table0
    # دیکشنری کمکی برای نگهداری جمع مقادیر بدون هیچ گروه‌بندی خاصی
    grouped_data = {
        'by_factor': 0,
        'cy_budget': 0,
        'cy_today_budget': 0,
        'cy_today_budget_line': 0,
        'cy_factor': 0,
        'by_today_factor': 0,
    }

    for entry in table3:
        def safe_float(value):
            try:
                val = str(value).strip()
                if val == '-' or val == '':
                    return 0.0
                return float(val)
            except ValueError:
                return 0.0

        grouped_data['by_factor'] += safe_float(entry['by_factor'])
        grouped_data['cy_budget'] += safe_float(entry['cy_budget'])
        grouped_data['cy_today_budget'] += safe_float(entry['cy_today_budget'])
        grouped_data['cy_today_budget_line'] += safe_float(entry['cy_today_budget_line'])
        grouped_data['cy_factor'] += safe_float(entry['cy_factor'])
        grouped_data['by_today_factor'] += safe_float(entry['by_today_factor'])

    # ساخت جدول نهایی (table0)
    table0 = []

    # محاسبه نسبت budget_rate
    budget_rate = grouped_data['cy_budget'] / grouped_data['by_factor'] if grouped_data['by_factor'] != 0 else 0

    if grouped_data['cy_today_budget'] != 0:
        amalkard_by_year_ratio = ((Decimal(grouped_data['cy_factor']) / Decimal(
            grouped_data['cy_today_budget'])) - Decimal(1.0)) * Decimal(100.0)
    else:
        amalkard_by_year_ratio = 0

    amalkard1 = False
    if amalkard_by_year_ratio > 0:
        amalkard1 = True

    cy_today_budget_line = Decimal(day_rate) * Decimal(grouped_data['cy_budget'])
    if cy_today_budget_line != 0:
        amalkard_by_line_ratio = ((Decimal(grouped_data['cy_factor']) / cy_today_budget_line) - Decimal(1.0)) * Decimal(
            100.0)
    else:
        amalkard_by_line_ratio = 0

    amalkard2 = False
    if amalkard_by_line_ratio > 0:
        amalkard2 = True
    actual_ratio_by_year = Decimal(grouped_data['cy_factor']) / Decimal(grouped_data['by_today_factor']) if \
        grouped_data['by_today_factor'] and \
        grouped_data[
            'by_today_factor'] != 0 else 0.0
    # افزودن رکورد نهایی بدون هیچ لایه‌ای به جدول
    table0.append({
        # حذف 'l1', 'l2'
        'by_factor': grouped_data['by_factor'],
        'cy_budget': grouped_data['cy_budget'],
        'budget_rate': budget_rate,
        'cy_today_budget': grouped_data['cy_today_budget'],
        'cy_today_budget_line': grouped_data['cy_today_budget_line'],
        'cy_factor': grouped_data['cy_factor'],
        'amalkard_by_year_ratio': amalkard_by_year_ratio,
        'amalkard_by_line_ratio': amalkard_by_line_ratio,
        'amalkard1': amalkard1,
        'amalkard2': amalkard2,
        'by_today_factor': by_today_factor,
        'actual_ratio_by_year': actual_ratio_by_year,



        # 'by_sayer_hazine_ratio': by_sayer_hazine_ratio,
        # 'cy_sayer_hazine_ratio': cy_sayer_hazine_ratio,
        # 'by_sayer_daramad_ratio': by_sayer_daramad_ratio,
        # 'cy_sayer_daramad_ratio': cy_sayer_daramad_ratio,


    })

    # ساخت دوباره جدول صفر ============================
    table0 = []
    by_factor = FactorDetaile.objects.filter(acc_year=base_year).aggregate(forosh=Sum('mablagh_after_takhfif_kol'))[
        'forosh']
    cy_factor = FactorDetaile.objects.filter(acc_year=acc_year).aggregate(forosh=Sum('mablagh_after_takhfif_kol'))[
                    'forosh'] or 0
    by_today_factor = FactorDetaile.objects.filter(acc_year=base_year, factor__date__lte=one_year_ago).aggregate(
        forosh=Sum('mablagh_after_takhfif_kol'))['forosh']

    cy_budget = (Decimal(by_factor) if by_factor is not None else Decimal(0)) * (
        Decimal(budget_rate) if budget_rate is not None else Decimal(0))

    cy_today_budget = (Decimal(by_today_factor) if by_today_factor is not None else Decimal(0)) * (
        Decimal(budget_rate) if budget_rate is not None else Decimal(0))
    if cy_today_budget != 0:
        amalkard_by_year_ratio = ((Decimal(cy_factor) / cy_today_budget) - Decimal(1.0)) * Decimal(100.0)
    else:
        amalkard_by_year_ratio = 0

    amalkard1 = False

    if amalkard_by_year_ratio > 0:
        amalkard1 = True

    cy_today_budget_line = Decimal(day_rate) * cy_budget
    if cy_today_budget_line != 0:
        amalkard_by_line_ratio = ((Decimal(cy_factor) / cy_today_budget_line) - Decimal(1.0)) * Decimal(100.0)
    else:
        amalkard_by_line_ratio = 0

    amalkard2 = False

    if amalkard_by_line_ratio > 0:
        amalkard2 = True

    actual_ratio_by_year = Decimal(cy_factor) / Decimal(
        by_today_factor) if by_today_factor and by_today_factor != 0 else 0.0

    table0.append({
        'by_factor': by_factor,
        'cy_budget': cy_budget,
        'budget_rate': budget_rate,
        'cy_today_budget': cy_today_budget,
        'cy_today_budget_line': cy_today_budget_line,
        'cy_factor': cy_factor,
        'amalkard_by_year_ratio': amalkard_by_year_ratio,
        'amalkard_by_line_ratio': amalkard_by_line_ratio,
        'amalkard1': amalkard1,
        'amalkard2': amalkard2,
        'by_today_factor': by_today_factor,
        'actual_ratio_by_year': actual_ratio_by_year,

    }

    )

    # فرض بر این است که این کد در ویو Django یا فریمورک مشابه است
    table100 = [{'l1': item['l1'], 'cy_factor': item['cy_factor'] / 10000000} for item in table1 if
                item.get('cy_factor', 0) > 0]
    table200 = [{'l1': item['l1'], 'l2': item['l2'], 'cy_factor': item['cy_factor'] / 10000000} for item in table2 if
                item.get('cy_factor', 0) > 0]
    table300 = [{'l1': item['l1'], 'l2': item['l2'], 'l3': item['l3'], 'cy_factor': item['cy_factor'] / 10000000} for
                item
                in table3 if item.get('cy_factor', 0) > 0]

    for item in table100:
        print(item['l1'])

    change_name = [
        ('لوازم آشپزخانه (طیقه اول)', 'طبقه اول'),
        ('موبایل و کالای دیجیتال', 'موبایل'),
        # می توانید موارد دیگر را اینجا اضافه کنید
        # ('نام_طولانی_دیگر', 'نام_کوتاه_آن'),
    ]

    name_map = {original: short for original, short in change_name}

    def apply_short_names(item):
        if 'l1' in item and item['l1'] in name_map:
            item['l1'] = name_map[item['l1']]
        if 'l2' in item and item['l2'] in name_map:
            item['l2'] = name_map[item['l2']]
        if 'l3' in item and item['l3'] in name_map:
            item['l3'] = name_map[item['l3']]
        return item

    table10 = [apply_short_names(item.copy()) for item in table100]
    table20 = [apply_short_names(item.copy()) for item in table200]
    table30 = [apply_short_names(item.copy()) for item in table300]

    context = {
        'acc_year': acc_year,
        'base_year': base_year,
        'user': user,
        'table3': table3,
        'table2': table2,
        'table1': table1,
        'table0': table0,
        'table10': table10,
        'table20': table20,
        'table30': table30,

    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")
    return render(request, 'budget_sale_total.html', context)


def BudgetSaleDetail(request, level, code, *args, **kwargs):
    start_time = time.time()
    name = 'جزئیات بودجه فروش'
    result = page_permision(request, name)
    if result:
        return result

    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='کلیات بودجه فروش', code=0)

    master_info = MasterInfo.objects.filter(is_active=True).last()
    acc_year = master_info.acc_year
    base_year = acc_year - 1

    tafzil = None
    moin_code = None
    tafzili_code = None
    g1 = 0
    g2 = 0
    today_bay_by = 0
    today_actual = 0
    today_by_time = 0
    budget_rate = 0  # نرخ بودجه پیش‌فرض
    tafzili_code = None
    level1 = Category.objects.filter(level=1)
    level2 = None
    level3 = None
    cat1 = None
    cat2 = None
    cat3 = None
    chart5_data = []
    chart6_data = []
    if level == '3':
        cat_id = int(code)
        category = Category.objects.filter(id=cat_id, level=3).last()
        detail_name = f'دسته - {category.name}-{cat_id}'
        parent_cat = category.parent
        parent_parent_cat = category.parent.parent
        level3 = Category.objects.filter(level=3, parent=parent_cat)
        level2 = Category.objects.filter(level=2, parent=parent_cat.parent)
        cat3 = category
        cat2 = cat3.parent
        cat1 = cat2.parent

        if category.budget_rate is not None and category.budget_rat != 0:
            budget_rate = category.budget_rate
        elif parent_cat.budget_rate is not None and parent_cat.budget_rate != 0:
            budget_rate = parent_cat.budget_rate
        else:
            budget_rate = parent_parent_cat.budget_rate
        budget_rate = float(budget_rate)

        print(detail_name)

        # --- ۱. کوئری‌های مربوط به سال پایه (Base Year) ---
        factor_base_year_qs = FactorDetaile.objects.filter(
            kala__category=category,
            acc_year=base_year
        )
        print('factor_base_year_qs.count()')
        print(factor_base_year_qs.count())

        daily_totals_base_year = {}
        if factor_base_year_qs.exists():
            for item in factor_base_year_qs.values('date').annotate(total=Sum('mablagh_after_takhfif_kol')).order_by(
                    'date'):
                daily_totals_base_year[str(item['date'])] = float(item['total'] or 0)

        print(len(daily_totals_base_year))
        # --- ۲. کوئری‌های مربوط به سال جاری (Current Year) ---
        facor_acc_year_qs = FactorDetaile.objects.filter(
            kala__category=category,
            acc_year=acc_year
        )

        daily_totals_acc_year = {}
        if facor_acc_year_qs.exists():
            for item in facor_acc_year_qs.values('date').annotate(total=Sum('mablagh_after_takhfif_kol')).order_by(
                    'date'):
                daily_totals_acc_year[str(item['date'])] = float(item['total'] or 0)

        start_date = FactorDetaile.objects.filter(acc_year=base_year).aggregate(min_date=Min('date'))['min_date']
        end_date = FactorDetaile.objects.filter(acc_year=base_year).aggregate(max_date=Max('date'))['max_date']
        print(detail_name)
        print('#############################################')

        # ایجاد لیست روزها
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date.strftime('%Y-%m-%d'))  # قالب تاریخ به YYYY-MM-DD
            current_date += timedelta(days=1)

        acc_date_list = [datetime.strptime(date, '%Y-%m-%d') + relativedelta(years=1) for date in date_list]
        acc_date_list = [date.strftime('%Y-%m-%d') for date in acc_date_list]

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
                # تنظیم نمایش لیبل‌ها بر اساس شرط‌های تعیین‌شده
                if shamsi_date.day == 1:  # نمایش نام ماه برای اولین روز ماه
                    label = month_names[shamsi_date.month]
                elif shamsi_date.day == 15:  # نمایش تاریخ کامل برای روز ۱۵ هر ماه
                    label = shamsi_date.strftime('%Y-%m-%d')
                else:  # سایر موارد خالی باشند
                    label = shamsi_date.day

                chart_labels_shamsi.append(shamsi_date.strftime('%Y-%m-%d'))

            except ValueError as e:
                print(f"خطای تبدیل تاریخ: {date}, {e}")  # نمایش خطا در صورت وجود مشکل

        chart_labels = chart_labels_shamsi  # برچسب‌های نمودار همان لیست تاریخ‌ها
        print('==============================================================')

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
            for_chart3_data = ((cumulative_base_year) * budget_rate)
            for_chart3_data = float(for_chart3_data)
            chart3_data.append(for_chart3_data)
            if day == today:
                today_bay_by = (cumulative_base_year) * budget_rate

            # مقدار روز جاری از سال جاری را دریافت و تجمعی محاسبه کن
            if day in daily_totals_acc_year:
                cumulative_acc_year += daily_totals_acc_year[day]  # علامت منفی برای تصحیح
            if day < today or day == today:
                chart2_data.append(cumulative_acc_year)
                chart5_data.append('-')
                if day == today:
                    today_actual = cumulative_acc_year
                    by_today_actual = cumulative_base_year
                    actual_rate = 1
                    if cumulative_base_year > 0:
                        actual_rate = today_actual / cumulative_base_year
            else:
                # chart2_data.append(0)
                chart5_data.append(cumulative_base_year * actual_rate)

        last_value_chart1 = chart1_data[-1] if chart1_data else None
        count_acc_date_list = len(acc_date_list)
        s = (last_value_chart1) / count_acc_date_list * budget_rate
        ch4 = 0
        ch6 = 0
        s6=0
        for day in acc_date_list:
            chart4_data.append(ch4)
            if day == today:
                today_by_time = ch4
                ch6=today_actual
                s6=today_actual/95
            if day <= today:
                chart6_data.append('-')
            else:
                chart6_data.append(ch6)
            ch4 += s
            ch6 += s6


        last_value_chart2 = chart2_data[-1] if chart2_data else None
        last_value_chart5 = chart5_data[-1] if chart5_data else None
        last_value_chart6 = chart6_data[-1] if chart6_data else None
        master_dat = {
            'by_sanads': last_value_chart1 / 10,
            'cy_budget': (last_value_chart1) / 10 * budget_rate,
            'budget_rate': budget_rate,
            'cy_sanads': last_value_chart2 / 10,'cy_sanads': last_value_chart2 / 10,

            'actual_rate':actual_rate,
            'by_today_actual':by_today_actual/10,
            'pishbini':last_value_chart5 / 10,
            'pishbini_line':last_value_chart6 / 10,


        }

        print('today_bay_by,today_actual,today_by_time')
        print(today_bay_by, today_actual, today_by_time)
        today_actual = Decimal(today_actual)
        today_bay_by = Decimal(today_bay_by)
        today_by_time = Decimal(today_by_time)
        g1 = ((today_actual - today_bay_by) / today_bay_by * 100) if today_bay_by != 0 else 100
        g2 = ((today_actual - today_by_time) / today_by_time * 100) if today_by_time != 0 else 100
        print(g1, g2)

    if level == '2':
        cat_id = int(code)
        category = Category.objects.filter(id=cat_id, level=2).last()
        detail_name = f'دسته - {category.name}-{cat_id}'
        parent_cat = category.parent
        level3 = Category.objects.filter(level=3, parent=category)
        level2 = Category.objects.filter(level=2, parent=parent_cat)

        cat2 = category
        cat1 = cat2.parent

        if category.budget_rate is not None and category.budget_rat != 0:
            budget_rate = category.budget_rate
        else:
            budget_rate = parent_cat.budget_rate

        budget_rate = float(budget_rate)

        print(detail_name)

        # --- ۱. کوئری‌های مربوط به سال پایه (Base Year) ---
        factor_base_year_qs = FactorDetaile.objects.filter(
            kala__category__parent=category,
            acc_year=base_year
        )
        print('factor_base_year_qs.count()')
        print(factor_base_year_qs.count())

        daily_totals_base_year = {}
        if factor_base_year_qs.exists():
            for item in factor_base_year_qs.values('date').annotate(total=Sum('mablagh_after_takhfif_kol')).order_by(
                    'date'):
                daily_totals_base_year[str(item['date'])] = float(item['total'] or 0)

        print(len(daily_totals_base_year))
        # --- ۲. کوئری‌های مربوط به سال جاری (Current Year) ---
        facor_acc_year_qs = FactorDetaile.objects.filter(
            kala__category__parent=category,
            acc_year=acc_year
        )

        daily_totals_acc_year = {}
        if facor_acc_year_qs.exists():
            for item in facor_acc_year_qs.values('date').annotate(total=Sum('mablagh_after_takhfif_kol')).order_by(
                    'date'):
                daily_totals_acc_year[str(item['date'])] = float(item['total'] or 0)

        start_date = FactorDetaile.objects.filter(acc_year=base_year).aggregate(min_date=Min('date'))['min_date']
        end_date = FactorDetaile.objects.filter(acc_year=base_year).aggregate(max_date=Max('date'))['max_date']
        print(detail_name)
        print('#############################################')

        # ایجاد لیست روزها
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date.strftime('%Y-%m-%d'))  # قالب تاریخ به YYYY-MM-DD
            current_date += timedelta(days=1)

        acc_date_list = [datetime.strptime(date, '%Y-%m-%d') + relativedelta(years=1) for date in date_list]
        acc_date_list = [date.strftime('%Y-%m-%d') for date in acc_date_list]

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
                # تنظیم نمایش لیبل‌ها بر اساس شرط‌های تعیین‌شده
                if shamsi_date.day == 1:  # نمایش نام ماه برای اولین روز ماه
                    label = month_names[shamsi_date.month]
                elif shamsi_date.day == 15:  # نمایش تاریخ کامل برای روز ۱۵ هر ماه
                    label = shamsi_date.strftime('%Y-%m-%d')
                else:  # سایر موارد خالی باشند
                    label = shamsi_date.day

                chart_labels_shamsi.append(shamsi_date.strftime('%Y-%m-%d'))

            except ValueError as e:
                print(f"خطای تبدیل تاریخ: {date}, {e}")  # نمایش خطا در صورت وجود مشکل

        chart_labels = chart_labels_shamsi  # برچسب‌های نمودار همان لیست تاریخ‌ها
        print('==============================================================')

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
            for_chart3_data = ((cumulative_base_year) * budget_rate)
            for_chart3_data = float(for_chart3_data)
            chart3_data.append(for_chart3_data)
            if day == today:
                today_bay_by = (cumulative_base_year) * budget_rate

            # مقدار روز جاری از سال جاری را دریافت و تجمعی محاسبه کن
            if day in daily_totals_acc_year:
                cumulative_acc_year += daily_totals_acc_year[day]  # علامت منفی برای تصحیح
            if day <= today:
                chart2_data.append(cumulative_acc_year)
                chart5_data.append('-')
                if day == today:
                    today_actual = cumulative_acc_year
                    by_today_actual = cumulative_base_year
                    actual_rate = 1
                    if cumulative_base_year > 0:
                        actual_rate = today_actual / cumulative_base_year
            else:
                # chart2_data.append(0)
                chart5_data.append(cumulative_base_year * actual_rate)

        last_value_chart1 = chart1_data[-1] if chart1_data else None
        count_acc_date_list = len(acc_date_list)
        s = (last_value_chart1) / count_acc_date_list * budget_rate
        ch4 = 0
        ch6 = 0
        s6 = 0
        for day in acc_date_list:
            chart4_data.append(ch4)
            if day == today:
                today_by_time = ch4
                ch6 = today_actual
                s6 = today_actual / 95
            if day <= today:
                chart6_data.append('-')
            else:
                chart6_data.append(ch6)
            ch4 += s
            ch6 += s6
        last_value_chart2 = chart2_data[-1] if chart2_data else None
        last_value_chart5 = chart5_data[-1] if chart5_data else None
        last_value_chart6 = chart6_data[-1] if chart6_data else None
        master_dat = {
            'by_sanads': last_value_chart1 / 10,
            'cy_budget': (last_value_chart1) / 10 * budget_rate,
            'budget_rate': budget_rate,
            'cy_sanads': last_value_chart2 / 10,

            'actual_rate': actual_rate,
            'by_today_actual': by_today_actual / 10,
            'pishbini': last_value_chart5 / 10,
            'pishbini_line': last_value_chart6 / 10,

        }

        print('today_bay_by,today_actual,today_by_time')
        print(today_bay_by, today_actual, today_by_time)
        today_actual = Decimal(today_actual)
        today_bay_by = Decimal(today_bay_by)
        today_by_time = Decimal(today_by_time)
        g1 = ((today_actual - today_bay_by) / today_bay_by * 100) if today_bay_by != 0 else 100
        g2 = ((today_actual - today_by_time) / today_by_time * 100) if today_by_time != 0 else 100
        print(g1, g2)

    if level == '1':
        cat_id = int(code)
        category = Category.objects.filter(id=cat_id, level=1).last()
        detail_name = f'دسته - {category.name}-{cat_id}'
        level2 = Category.objects.filter(level=2, parent=category)
        cat1 = category
        budget_rate = category.budget_rate

        budget_rate = float(budget_rate)

        print(detail_name)

        # --- ۱. کوئری‌های مربوط به سال پایه (Base Year) ---
        factor_base_year_qs = FactorDetaile.objects.filter(
            kala__category__parent__parent=category,
            acc_year=base_year
        )
        print('factor_base_year_qs.count()')
        print(factor_base_year_qs.count())

        daily_totals_base_year = {}
        if factor_base_year_qs.exists():
            for item in factor_base_year_qs.values('date').annotate(total=Sum('mablagh_after_takhfif_kol')).order_by(
                    'date'):
                daily_totals_base_year[str(item['date'])] = float(item['total'] or 0)

        print(len(daily_totals_base_year))
        # --- ۲. کوئری‌های مربوط به سال جاری (Current Year) ---
        facor_acc_year_qs = FactorDetaile.objects.filter(
            kala__category__parent__parent=category,
            acc_year=acc_year
        )

        daily_totals_acc_year = {}
        if facor_acc_year_qs.exists():
            for item in facor_acc_year_qs.values('date').annotate(total=Sum('mablagh_after_takhfif_kol')).order_by(
                    'date'):
                daily_totals_acc_year[str(item['date'])] = float(item['total'] or 0)

        start_date = FactorDetaile.objects.filter(acc_year=base_year).aggregate(min_date=Min('date'))['min_date']
        end_date = FactorDetaile.objects.filter(acc_year=base_year).aggregate(max_date=Max('date'))['max_date']
        print(detail_name)
        print('#############################################')

        # ایجاد لیست روزها
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date.strftime('%Y-%m-%d'))  # قالب تاریخ به YYYY-MM-DD
            current_date += timedelta(days=1)

        acc_date_list = [datetime.strptime(date, '%Y-%m-%d') + relativedelta(years=1) for date in date_list]
        acc_date_list = [date.strftime('%Y-%m-%d') for date in acc_date_list]

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
                # تنظیم نمایش لیبل‌ها بر اساس شرط‌های تعیین‌شده
                if shamsi_date.day == 1:  # نمایش نام ماه برای اولین روز ماه
                    label = month_names[shamsi_date.month]
                elif shamsi_date.day == 15:  # نمایش تاریخ کامل برای روز ۱۵ هر ماه
                    label = shamsi_date.strftime('%Y-%m-%d')
                else:  # سایر موارد خالی باشند
                    label = shamsi_date.day

                chart_labels_shamsi.append(shamsi_date.strftime('%Y-%m-%d'))

            except ValueError as e:
                print(f"خطای تبدیل تاریخ: {date}, {e}")  # نمایش خطا در صورت وجود مشکل

        chart_labels = chart_labels_shamsi  # برچسب‌های نمودار همان لیست تاریخ‌ها
        print('==============================================================')

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
            for_chart3_data = ((cumulative_base_year) * budget_rate)
            for_chart3_data = float(for_chart3_data)
            chart3_data.append(for_chart3_data)
            if day == today:
                today_bay_by = (cumulative_base_year) * budget_rate

            # مقدار روز جاری از سال جاری را دریافت و تجمعی محاسبه کن
            if day in daily_totals_acc_year:
                cumulative_acc_year += daily_totals_acc_year[day]  # علامت منفی برای تصحیح
            if day <= today:
                chart2_data.append(cumulative_acc_year)
                chart5_data.append('-')
                if day == today:
                    today_actual = cumulative_acc_year
                    by_today_actual = cumulative_base_year
                    actual_rate = 1
                    if cumulative_base_year > 0:
                        actual_rate = today_actual / cumulative_base_year
            else:
                # chart2_data.append(0)
                chart5_data.append(cumulative_base_year * actual_rate)

        last_value_chart1 = chart1_data[-1] if chart1_data else None
        count_acc_date_list = len(acc_date_list)
        s = (last_value_chart1) / count_acc_date_list * budget_rate
        ch4 = 0
        ch6 = 0
        s6 = 0
        for day in acc_date_list:
            chart4_data.append(ch4)
            if day == today:
                today_by_time = ch4
                ch6 = today_actual
                s6 = today_actual / 95
            if day <= today:
                chart6_data.append('-')
            else:
                chart6_data.append(ch6)
            ch4 += s
            ch6 += s6
        last_value_chart2 = chart2_data[-1] if chart2_data else None
        last_value_chart5 = chart5_data[-1] if chart5_data else None
        last_value_chart6 = chart6_data[-1] if chart6_data else None
        master_dat = {
            'by_sanads': last_value_chart1 / 10,
            'cy_budget': (last_value_chart1) / 10 * budget_rate,
            'budget_rate': budget_rate,
            'cy_sanads': last_value_chart2 / 10,

            'actual_rate': actual_rate,
            'by_today_actual': by_today_actual / 10,
            'pishbini': last_value_chart5 / 10,
            'pishbini_line': last_value_chart6 / 10,

        }

        print('today_bay_by,today_actual,today_by_time')
        print(today_bay_by, today_actual, today_by_time)
        today_actual = Decimal(today_actual)
        today_bay_by = Decimal(today_bay_by)
        today_by_time = Decimal(today_by_time)
        g1 = ((today_actual - today_bay_by) / today_bay_by * 100) if today_bay_by != 0 else 100
        g2 = ((today_actual - today_by_time) / today_by_time * 100) if today_by_time != 0 else 100
        print(g1, g2)

    if level == '0':
        detail_name = 'همه کالاها'
        budget_rate = 1.5
        budget_rate = float(budget_rate)
        print(detail_name)

        # --- ۱. کوئری‌های مربوط به سال پایه (Base Year) ---
        factor_base_year_qs = FactorDetaile.objects.filter(
            acc_year=base_year
        )
        print('factor_base_year_qs.count()')
        print(factor_base_year_qs.count())

        daily_totals_base_year = {}
        if factor_base_year_qs.exists():
            for item in factor_base_year_qs.values('date').annotate(total=Sum('mablagh_after_takhfif_kol')).order_by(
                    'date'):
                daily_totals_base_year[str(item['date'])] = float(item['total'] or 0)

        print(len(daily_totals_base_year))
        # --- ۲. کوئری‌های مربوط به سال جاری (Current Year) ---
        facor_acc_year_qs = FactorDetaile.objects.filter(
            acc_year=acc_year
        )

        daily_totals_acc_year = {}
        if facor_acc_year_qs.exists():
            for item in facor_acc_year_qs.values('date').annotate(total=Sum('mablagh_after_takhfif_kol')).order_by(
                    'date'):
                daily_totals_acc_year[str(item['date'])] = float(item['total'] or 0)

        start_date = FactorDetaile.objects.filter(acc_year=base_year).aggregate(min_date=Min('date'))['min_date']
        end_date = FactorDetaile.objects.filter(acc_year=base_year).aggregate(max_date=Max('date'))['max_date']
        print(detail_name)
        print('#############################################')

        # ایجاد لیست روزها
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date.strftime('%Y-%m-%d'))  # قالب تاریخ به YYYY-MM-DD
            current_date += timedelta(days=1)

        acc_date_list = [datetime.strptime(date, '%Y-%m-%d') + relativedelta(years=1) for date in date_list]
        acc_date_list = [date.strftime('%Y-%m-%d') for date in acc_date_list]

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
                # تنظیم نمایش لیبل‌ها بر اساس شرط‌های تعیین‌شده
                if shamsi_date.day == 1:  # نمایش نام ماه برای اولین روز ماه
                    label = month_names[shamsi_date.month]
                elif shamsi_date.day == 15:  # نمایش تاریخ کامل برای روز ۱۵ هر ماه
                    label = shamsi_date.strftime('%Y-%m-%d')
                else:  # سایر موارد خالی باشند
                    label = shamsi_date.day

                chart_labels_shamsi.append(shamsi_date.strftime('%Y-%m-%d'))

            except ValueError as e:
                print(f"خطای تبدیل تاریخ: {date}, {e}")  # نمایش خطا در صورت وجود مشکل

        chart_labels = chart_labels_shamsi  # برچسب‌های نمودار همان لیست تاریخ‌ها
        print('==============================================================')

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
            for_chart3_data = ((cumulative_base_year) * budget_rate)
            for_chart3_data = float(for_chart3_data)
            chart3_data.append(for_chart3_data)
            if day == today:
                today_bay_by = (cumulative_base_year) * budget_rate

            # مقدار روز جاری از سال جاری را دریافت و تجمعی محاسبه کن
            if day in daily_totals_acc_year:
                cumulative_acc_year += daily_totals_acc_year[day]  # علامت منفی برای تصحیح
            if day <= today:
                chart2_data.append(cumulative_acc_year)
                chart5_data.append('-')
                if day == today:
                    today_actual = cumulative_acc_year
                    by_today_actual = cumulative_base_year
                    actual_rate = 1
                    if cumulative_base_year > 0:
                        actual_rate = today_actual / cumulative_base_year
            else:
                # chart2_data.append(0)
                chart5_data.append(cumulative_base_year * actual_rate)

        last_value_chart1 = chart1_data[-1] if chart1_data else None
        count_acc_date_list = len(acc_date_list)
        s = (last_value_chart1) / count_acc_date_list * budget_rate
        ch4 = 0
        ch6 = 0
        s6 = 0
        for day in acc_date_list:
            chart4_data.append(ch4)
            if day == today:
                today_by_time = ch4
                ch6 = today_actual
                s6 = today_actual / 95
            if day <= today:
                chart6_data.append('-')
            else:
                chart6_data.append(ch6)
            ch4 += s
            ch6 += s6
        last_value_chart2 = chart2_data[-1] if chart2_data else None
        last_value_chart5 = chart5_data[-1] if chart5_data else None
        last_value_chart6 = chart6_data[-1] if chart6_data else None
        master_dat = {
            'by_sanads': last_value_chart1 / 10,
            'cy_budget': (last_value_chart1) / 10 * budget_rate,
            'budget_rate': budget_rate,
            'cy_sanads': last_value_chart2 / 10,

            'actual_rate': actual_rate,
            'by_today_actual': by_today_actual / 10,
            'pishbini': last_value_chart5 / 10,
            'pishbini_line': last_value_chart6 / 10,

        }

        print('today_bay_by,today_actual,today_by_time')
        print(today_bay_by, today_actual, today_by_time)
        today_actual = Decimal(today_actual)
        today_bay_by = Decimal(today_bay_by)
        today_by_time = Decimal(today_by_time)
        g1 = ((today_actual - today_bay_by) / today_bay_by * 100) if today_bay_by != 0 else 100
        g2 = ((today_actual - today_by_time) / today_by_time * 100) if today_by_time != 0 else 100
        print(g1, g2)

    g1 = max(-100, min(g1, 100))
    g2 = max(-100, min(g2, 100))
    for item in chart1_data:
        print(item)

    context = {
        'acc_year': acc_year,
        'base_year': base_year,
        'user': user,
        'detail_name': detail_name,
        'budget_rate': budget_rate,
        'chart_labels': chart_labels,  # لیبل‌های نمودار
        'chart1_data': chart1_data,
        'chart2_data': chart2_data,
        'chart3_data': chart3_data,
        'chart4_data': chart4_data,
        'chart5_data': chart5_data,
        'chart6_data': chart6_data,

        'level': int(level),
        'level1': level1,
        'level2': level2,
        'level3': level3,
        'cat1': cat1,
        'cat2': cat2,
        'cat3': cat3,

        'master_dat': master_dat,

        'g1': g1,
        'g2': g2,

    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'budget_sale_detail.html', context)


def BudgetSaleFactorDetail(request, year, level, code, *args, **kwargs):
    start_time = time.time()
    name = 'جزئیات فاکتور های فروش'
    result = page_permision(request, name)
    if result:
        return result

    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='جزئیات فاکتور های فروش', code=int(code))

    master_info = MasterInfo.objects.filter(is_active=True).last()
    acc_year = master_info.acc_year
    is_b_year = False
    if int(year) == acc_year - 1:
        is_b_year = True
    level1 = Category.objects.filter(level=1)
    level2 = None
    level3 = None
    cat1 = None
    cat2 = None
    cat3 = None

    if int(level) == 3:
        cat3 = Category.objects.filter(id=int(code), level=3).last()
        cat2 = cat3.parent
        cat1 = cat2.parent
        detail_name = cat3.name
        level3 = Category.objects.filter(level=3, parent=cat3.parent)
        level2 = Category.objects.filter(level=2, parent=cat3.parent.parent)
        factors = FactorDetaile.objects.filter(kala__category=cat3, acc_year=int(year))

    if int(level) == 2:
        cat2 = Category.objects.filter(id=int(code), level=2).last()
        cat1 = cat2.parent
        detail_name = cat2.name
        level2 = Category.objects.filter(level=2, parent=cat2.parent)
        level3 = Category.objects.filter(level=3, parent=cat2)

        factors = FactorDetaile.objects.filter(kala__category__parent=cat2, acc_year=int(year))

    if int(level) == 1:
        cat1 = Category.objects.filter(id=int(code), level=1).last()
        detail_name = cat1.name
        level2 = Category.objects.filter(level=2, parent=cat1)
        factors = FactorDetaile.objects.filter(kala__category__parent__parent=cat1, acc_year=int(year))

    today = date.today()
    one_year_ago = today - relativedelta(years=1)

    context = {
        'user': user,
        'level': int(level),
        'level1': level1,
        'level2': level2,
        'level3': level3,
        'cat1': cat1,
        'cat2': cat2,
        'cat3': cat3,

        'year': year,
        'factors': factors,
        'detail_name': detail_name,
        'is_b_year': is_b_year,
        'one_year_ago': one_year_ago,
    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'budget_sale_factor_detail.html', context)

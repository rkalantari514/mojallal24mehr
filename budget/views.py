from custom_login.models import UserLog
from custom_login.views import page_permision
from dashboard.models import MasterInfo
from mahakupdate.models import SanadDetail, AccCoding, FactorDetaile
from datetime import date
from decimal import Decimal



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
        amalkard2 =True
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
            'amalkard_by_year_ratio': data['amalkard_by_year'] / data['total_budget_cy_today'] * 100 ,
            'amalkard1': amalkard1,
            'amalkard_by_day': data['amalkard_by_day'],
            'amalkard_by_day_ratio':  (data['amalkard_by_day'] / (float(data['total_budget_cy']) * day_rate)) * 100,
            'amalkard2': amalkard2,

        })

        acc_code_2=AccCoding.objects.filter(level=2,code=moin_code,parent__code=501).last()
        br=data['total_budget_cy']/data['total_sanad_by']
        if acc_code_2.budget_rate != br:
            acc_code_2.budget_rate = br
            acc_code_2.save()

#----------------------------------ساخت جدول 1 ----------------------------

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
    g1=-70
    g2=43
    today_bay_by = 0
    today_actual = 0
    today_by_time = 0
    budget_rate = 0  # نرخ بودجه پیش‌فرض
    level1=AccCoding.objects.filter(level=1,code=501)
    kol_code=None
    moin_code=None
    level2=AccCoding.objects.filter(level=2,parent__code=501)
    level3=None
    tafzili_code=None



    if level == '3':
        tafzili_code = int(code)
        tafzil = AccCoding.objects.filter(code=tafzili_code, parent__parent__code=501).last()
        detail_name=f'سطح تفضیل - {tafzil.name}-{tafzili_code}'
        moin_code=int(tafzil.parent.code)
        level3 = AccCoding.objects.filter(level=3, parent__parent__code=501 ,parent__code=moin_code, is_budget=True)

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
            if day == today:
                today_bay_by=cumulative_base_year * budget_rate

            # مقدار روز جاری از سال جاری را دریافت و تجمعی محاسبه کن
            if day in daily_totals_acc_year:
                cumulative_acc_year += daily_totals_acc_year[day]  # علامت منفی برای تصحیح
            if day <= today:
                chart2_data.append(cumulative_acc_year)
                if day == today:
                    today_actual=cumulative_acc_year

        last_value_chart1 = chart1_data[-1] if chart1_data else None
        count_acc_date_list = len(acc_date_list)
        s=last_value_chart1/count_acc_date_list * budget_rate
        ch4=0
        for day in acc_date_list:
            chart4_data.append(ch4)
            if day == today:
                today_by_time=ch4

            ch4 += s
        last_value_chart2 = chart2_data[-1] if chart2_data else None
        master_dat={
            'by_sanads':last_value_chart1/10,
            'cy_budget':last_value_chart1/10*budget_rate,
            'budget_rate':budget_rate,
            'cy_sanads': last_value_chart2 / 10

        }

        print('today_bay_by,today_actual,today_by_time')
        print(today_bay_by,today_actual,today_by_time)

        g1 = ((today_actual - today_bay_by) / today_bay_by * 100) if today_bay_by != 0 else 100
        g2 = ((today_actual - today_by_time) / today_by_time * 100) if today_by_time != 0 else 100
        print(g1,g2)

    if level == '2':
        moin_code = int(code)
        moin = AccCoding.objects.filter(level=2, code=moin_code, parent__code=501).last()
        detail_name=f'سطح معین - {moin.name}-{moin_code}'
        level3 = AccCoding.objects.filter(level=3, parent__parent__code=501 ,parent__code=moin_code, is_budget=True)

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
        chart3_d= 0
        today = datetime.today().strftime('%Y-%m-%d')  # تاریخ امروز به فرمت YYYY-MM-DD
        for day in acc_date_list:
            by_date = datetime.strptime(day, '%Y-%m-%d') + relativedelta(years=-1)  # تاریخ مربوط به سال پایه

            # مقدار روز جاری از سال پایه را دریافت و تجمعی محاسبه کن
            if str(by_date.date()) in daily_totals_base_year:
                cumulative_base_year += daily_totals_base_year[str(by_date.date())]  # علامت منفی برای تصحیح
            chart1_data.append(cumulative_base_year)
            chart3_data.append(cumulative_base_year * budget_rate)
            if day == today:
                today_bay_by=cumulative_base_year * budget_rate

            # مقدار روز جاری از سال جاری را دریافت و تجمعی محاسبه کن
            if day in daily_totals_acc_year:
                cumulative_acc_year += daily_totals_acc_year[day]  # علامت منفی برای تصحیح
            if day <= today:
                chart2_data.append(cumulative_acc_year)
                if day == today:
                    today_actual=cumulative_acc_year



        last_value_chart3 = chart3_data[-1] if chart3_data else None
        count_acc_date_list = len(acc_date_list)
        s=last_value_chart3/count_acc_date_list
        ch4=0
        for day in acc_date_list:
            chart4_data.append(ch4)
            if day == today:
                today_by_time=ch4
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
        print(today_bay_by,today_actual,today_by_time)

        g1 = ((today_actual - today_bay_by) / today_bay_by * 100) if today_bay_by != 0 else 100
        g2 = ((today_actual - today_by_time) / today_by_time * 100) if today_by_time != 0 else 100
        print(g1,g2)

    if level == '1':
        kol_code = int(code)

        kol = AccCoding.objects.filter(level=1, code=kol_code).last()
        detail_name=f'سطح کل - {kol.name}-{kol_code}'

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
        chart1_data = [] #عکلکرد سال گذشته
        chart2_data = [] # عملکرد امسال تا امروز
        chart3_data = [] # بودجه با آهنگ پارسال
        chart4_data = [] # بودجه با تناسب زمان



        cumulative_base_year = 0
        cumulative_acc_year = 0
        chart3_d= 0
        today = datetime.today().strftime('%Y-%m-%d')  # تاریخ امروز به فرمت YYYY-MM-DD
        for day in acc_date_list:
            by_date = datetime.strptime(day, '%Y-%m-%d') + relativedelta(years=-1)  # تاریخ مربوط به سال پایه

            # مقدار روز جاری از سال پایه را دریافت و تجمعی محاسبه کن
            if str(by_date.date()) in daily_totals_base_year:
                cumulative_base_year += daily_totals_base_year[str(by_date.date())]  # علامت منفی برای تصحیح
            chart1_data.append(cumulative_base_year)
            chart3_data.append(cumulative_base_year * budget_rate)
            if day == today:
                today_bay_by=cumulative_base_year * budget_rate

            # مقدار روز جاری از سال جاری را دریافت و تجمعی محاسبه کن
            if day in daily_totals_acc_year:
                cumulative_acc_year += daily_totals_acc_year[day]  # علامت منفی برای تصحیح
            if day <= today:
                chart2_data.append(cumulative_acc_year)
                if day == today:
                    today_actual=cumulative_acc_year



        last_value_chart3 = chart3_data[-1] if chart3_data else None
        count_acc_date_list = len(acc_date_list)
        s=last_value_chart3/count_acc_date_list
        ch4=0
        for day in acc_date_list:
            chart4_data.append(ch4)
            if day == today:
                today_by_time=ch4
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
        print(today_bay_by,today_actual,today_by_time)


        g1 = ((today_actual - today_bay_by) / today_bay_by * 100) if today_bay_by != 0 else 100
        g2 = ((today_actual - today_by_time) / today_by_time * 100) if today_by_time != 0 else 100
        print(g1,g2)

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

        'g1':g1,
        'g2':g2,



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

    sanads_qs_base_year = SanadDetail.objects.filter(is_active=True, kol=501, acc_year=base_year)   #حذف

    factors_qs_base_year = FactorDetaile.objects.filter(acc_year=base_year)

    aggregated_sanads_base_year = sanads_qs_base_year.values('tafzili', 'moin').annotate(            #حذف
        total_sanad_by=Sum('curramount'),
        total_sanad_by_today=Sum('curramount', filter=Q(date__lte=one_year_ago))
    )

    aggregated_factors_base_year = factors_qs_base_year.values('code_kala').annotate(
            total_factor_by=Sum('mablagh_nahaee'),
            total_factor_by_today=Sum('mablagh_nahaee', filter=Q(factor__date__lte=one_year_ago))
        )

    sanads_qs_current_year = SanadDetail.objects.filter(                          #حذف
        is_active=True, kol=501, acc_year=acc_year, date__lte=today
    ).values('tafzili', 'moin').annotate(
        total_sanad_cy_today=Sum('curramount')
    )
    factors_qs_current_year = FactorDetaile.objects.filter(acc_year=acc_year, factor__date__lte=today).values('code_kala').annotate(
        total_factor_cy_today=Sum('mablagh_nahaee')
    )

    aggregated_by_lookup2 = {}                              #حذف
    for item in aggregated_sanads_base_year:
        key = (item['tafzili'], item['moin'])
        aggregated_by_lookup2[key] = {
            'total_sanad_by': item['total_sanad_by'] or 0,
            'total_sanad_by_today': item['total_sanad_by_today'] or 0
        }

    aggregated_by_lookup = {}
    for item in aggregated_factors_base_year:
        key = (item['code_kala'])
        aggregated_by_lookup[key] = {
            'total_factor_by': item['total_factor_by'] or 0,
            'total_factor_by_today': item['total_factor_by_today'] or 0
        }

    aggregated_cy_lookup2 = {}                      #حذف
    for item in sanads_qs_current_year:
        key = (item['tafzili'], item['moin'])
        aggregated_cy_lookup2[key] = item['total_sanad_cy_today'] or 0


    aggregated_cy_lookup = {}
    for item in factors_qs_current_year:
        key = (item['code_kala'])
        aggregated_cy_lookup[key] = item['total_factor_cy_today'] or 0




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
    first_factor_day = FactorDetaile.objects.filter(acc_year=acc_year).first().factor.date
    days_from_start = (today - first_factor_day).days
    day_rate = days_from_start / 365
    print('day_rate', day_rate)
    print('تا اینجا آمدیم')

    table3 = []
    for (tafzili_code, moin_code), data in aggregated_by_lookup2.items():
        total_sanad_by = data['total_sanad_by']
        total_sanad_by_today = data['total_sanad_by_today']
        total_sanad_cy_today = aggregated_cy_lookup2.get((tafzili_code, moin_code), 0)

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
                # print('amalkard_by_day', amalkard_by_day)
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
        amalkard2 =True
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
            'amalkard_by_year_ratio': data['amalkard_by_year'] / data['total_budget_cy_today'] * 100 ,
            'amalkard1': amalkard1,
            'amalkard_by_day': data['amalkard_by_day'],
            'amalkard_by_day_ratio':  (data['amalkard_by_day'] / (float(data['total_budget_cy']) * day_rate)) * 100,
            'amalkard2': amalkard2,

        })

        acc_code_2=AccCoding.objects.filter(level=2,code=moin_code,parent__code=501).last()
        br=data['total_budget_cy']/data['total_sanad_by']
        if acc_code_2.budget_rate != br:
            acc_code_2.budget_rate = br
            acc_code_2.save()

#----------------------------------ساخت جدول 1 ----------------------------

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

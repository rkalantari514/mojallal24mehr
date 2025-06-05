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

def BudgetTotal(request, *args, **kwargs):
    start_time = time.time()
    name = 'کلیات بودجه'
    result = page_permision(request, name)
    if result:
        return result

    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='کلیات بودجه', code=0)

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

    tafzili_names = {item['code']: item['name'] for item in all_acc_coding if item['level'] == 3 and item['parent__parent__code'] == 501}
    moin_names = {item['code']: item['name'] for item in all_acc_coding if item['level'] == 2 and item['parent__code'] == 501}
    budget_taf_info = {
        item['code']: item['budget_rate'] for item in all_acc_coding
        if item['level'] == 3 and item['parent__parent__code'] == 501 and item['is_budget']
    }

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

        if is_budge and budget_rate != '-':
            try:
                rate = Decimal(budget_rate)
                total_budget_cy = total_sanad_by * rate * -1
                total_budget_cy_today = total_sanad_by_today * rate  * -1
                total_budget_by=total_sanad_by * -1
            except Exception as e:
                pass # در صورت بروز خطا در تبدیل نرخ، از نمایش آن جلوگیری می‌کند

        table3.append({
            'moin_code': moin_code,
            'moin_name': moin_name,
            'tafzili_code': tafzili_code,
            'tafzili_name': tafzili_name,
            'is_budge': is_budge,
            'budget_rate': budget_rate,
            'total_sanad_by': total_sanad_by  * -1,
            'total_budget_cy': total_budget_cy,
            'total_budget_by': total_budget_by,
            'total_sanad_by_today': total_sanad_by_today  * -1,
            'total_budget_cy_today': total_budget_cy_today,
            'total_sanad_cy_today': total_sanad_cy_today  * -1,
        })

#-------------------------------- ایجاد جدول 2-----------------------

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
        grouped_data[moin_code]['total_sanad_by'] += safe_float(entry['total_sanad_by'])
        grouped_data[moin_code]['total_budget_cy'] += safe_float(entry['total_budget_cy'])
        grouped_data[moin_code]['total_budget_by'] += safe_float(entry['total_budget_by'])
        grouped_data[moin_code]['total_sanad_by_today'] += safe_float(entry['total_sanad_by_today'])
        grouped_data[moin_code]['total_budget_cy_today'] += safe_float(entry['total_budget_cy_today'])
        grouped_data[moin_code]['total_sanad_cy_today'] += safe_float(entry['total_sanad_cy_today'])

    # حالا لیست نهایی table2 را بر اساس جمع‌بندی می‌سازیم
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
        SanadDetail.objects.filter(is_active=True, kol=501, acc_year=acc_year, date__lte=today, tafzili=tafzili_code,
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

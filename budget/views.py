from django.shortcuts import render

from custom_login.models import UserLog
from custom_login.views import page_permision
from dashboard.models import MasterInfo
from mahakupdate.models import SanadDetail, AccCoding
import time
from django.db.models import Sum, F, DecimalField


# Create your views here.


def BudgetTotal(request, *args, **kwargs):
    start_time = time.time()  # زمان شروع تابع
    name = 'کلیات بودجه'
    result = page_permision(request, name)  # بررسی دسترسی
    if result:  # اگر هدایت انجام شده است
        return result
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='کلیات بودجه', code=0)

    # دریافت سال مالی پایه
    acc_year = MasterInfo.objects.filter(is_active=True).last().acc_year
    base_year = acc_year - 1

    # فیلتر کردن تمام SanadDetail های مربوط به kol=501 در یک کوئری
    sanads_qs = SanadDetail.objects.filter(is_active=True, kol=501, acc_year=base_year).select_related('person')

    # دانلود تمامی moin های یکتا در یک عملیات استعلام
    unique_moins = sanads_qs.exclude(moin__isnull=True).values_list('moin', flat=True).distinct().order_by('moin')

    # دریافت نام ماین های مربوطه در یک عملیات
    moin_names_qs = AccCoding.objects.filter(
        level=2, parent__code=501, code__in=unique_moins
    ).values('code', 'name')

    # ساخت یک دیکشنری برای نگهداری نام‌ها بلافاصله
    moin_names = {item['code']: item['name'] for item in moin_names_qs}

    # حالا حلقه بر روی Moins و محاسبه مقادیر
    table1 = []

    for moin_code in unique_moins:
        moin_name = moin_names.get(moin_code, ' ')

        # فیلتر کردن در یک‌بار و استفاده مجدد
        sanads_moin = sanads_qs.filter(moin=moin_code)

        # گرفتن نتایج aggregate
        total_sanad = sanads_moin.aggregate(curr=Sum('curramount'))['curr'] or 0

        # فیلتر کردن tafzili های مربوط به این moin
        budget_taf_ids = list(
            AccCoding.objects.filter(
                level=3,
                parent__code=moin_code,
                parent__parent__code=501,
                is_budget=True
            ).values_list('code', flat=True).distinct()
        )

        # محاسبه مقدار بودجه‌ای
        budget_sanad = sanads_moin.filter(tafzili__in=budget_taf_ids).aggregate(curr=Sum('curramount'))['curr'] or 0

        table1.append({
            'code': moin_code,
            'moin_name': moin_name,
            'total_sanad': total_sanad,
            'budget_sanad': budget_sanad,
        })

    # نمایش نتایج
    for item in table1:
        print(item['code'])
        print(item['moin_name'])
        print(item['total_sanad'])
        print(item['budget_sanad'])
        print('-----------------------------')

    context = {
        'user': user,
        'table1':table1,

        # 'level': level,
        # 'sanads': sanads,
        # 'kol_code': int(kol_code),
        # 'moin_code': int(moin_code),
        # 'tafzili_code': int(tafzili_code),
        # 'level1': level1,
        # 'level2': level2,
        # 'level3': level3,
        # 'total_bed': bed_sum,
        # 'total_bes': bes_sum,
        # 'total_curramount': curramount_sum,

    }

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")
    return render(request, 'budget_total.html', context)

    sanads = SanadDetail.objects.filter(kol=kol_code, moin=moin_code, tafzili=tafzili_code, acc_year=acc_year)

    level1 = []
    level2 = []
    level3 = []
    for l in AccCoding.objects.filter(level=1).order_by('code'):
        level1.append(
            {
                'code': l.code,
                'name': l.name,

            }
        )

    for l in AccCoding.objects.filter(level=2, parent__code=kol_code).order_by('code'):
        level2.append(
            {
                'code': l.code,
                'name': l.name,

            }
        )

    # فعلا خالی است
    for l in AccCoding.objects.filter(level=3, parent__code=moin_code, parent__parent__code=kol_code).order_by('code'):
        print(l.code, l.name)
        level3.append(
            {
                'code': l.code,
                'name': l.name,

            }
        )
    level3 = []

    # فیلتر کردن داده‌ها
    sanads2 = SanadDetail.objects.filter(kol=kol_code, moin=moin_code, acc_year=acc_year)

    # استفاده از مجموعه برای حذف تکراری‌ها و سپس تبدیل به لیست مرتب‌شده
    tafzili_set = sorted({s.tafzili for s in sanads2})

    # ایجاد لیست level3
    for tafzili_code1 in tafzili_set:
        print(tafzili_code)
        try:
            taf_name=AccCoding.objects.filter(level=3, parent__code=moin_code, parent__parent__code=kol_code,code=tafzili_code1).last().name
        except:
            taf_name=' '
        level3.append(
            {
                'code': tafzili_code1,
                'name': taf_name,

            }
        )

    level = 4

    print(level, kol_code, moin_code, tafzili_code)
    bed_sum = SanadDetail.objects.filter(is_active=True, kol=kol_code, moin=moin_code, tafzili=tafzili_code,
                                         acc_year=acc_year).aggregate(Sum('bed'))[
        'bed__sum']
    bes_sum = SanadDetail.objects.filter(is_active=True, kol=kol_code, moin=moin_code, tafzili=tafzili_code,
                                         acc_year=acc_year).aggregate(Sum('bes'))[
        'bes__sum']
    curramount_sum = \
        SanadDetail.objects.filter(is_active=True, kol=kol_code, moin=moin_code, tafzili=tafzili_code,
                                   acc_year=acc_year).aggregate(Sum('curramount'))[
            'curramount__sum']

    context = {
        'year': year,
        'level': level,
        'sanads': sanads,
        'kol_code': int(kol_code),
        'moin_code': int(moin_code),
        'tafzili_code': int(tafzili_code),
        'level1': level1,
        'level2': level2,
        'level3': level3,
        'total_bed': bed_sum,
        'total_bes': bes_sum,
        'total_curramount': curramount_sum,

    }

    return render(request, 'sanad_total.html', context)

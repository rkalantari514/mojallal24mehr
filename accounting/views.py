from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import time
from django.db.models import Sum

from custom_login.models import UserLog
from mahakupdate.models import SanadDetail, AccCoding


# Create your views here.



@login_required(login_url='/login')
def TarazKol(request, *args, **kwargs):
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='تراز آزمایشی', code=0)

    start_time = time.time()  # زمان شروع تابع

    # بارگذاری اطلاعات کل با جمع بدهکاری و بستانکاری
    kol_totals = SanadDetail.objects.values('kol').annotate(
        total_bed=Sum('bed'),
        total_bes=Sum('bes'),
        total_curramount=Sum('curramount')
    ).order_by('kol')

    # بارگذاری AccCoding برای سطوح کل و معین
    acc_codings = AccCoding.objects.filter(level__in=[1, 2]).values('code', 'name', 'level')
    acc_coding_dict = {coding['code']: (coding['name'], coding['level']) for coding in acc_codings}

    # ایجاد جدول کلی
    table_kol = []
    for kol in kol_totals:
        total_bed = kol['total_bed'] or 0
        total_bes = kol['total_bes'] or 0
        total_curramount = kol['total_curramount'] or 0
        name, level = acc_coding_dict.get(kol['kol'], ('نام نامشخص', 0))

        table_kol.append({
            'kol': kol['kol'],
            'name': name,
            'level': level,
            'total_bed': total_bed,
            'total_bes': total_bes,
            'total_curramount': total_curramount,
        })

    # ایجاد جدول معین با ارتباط به کل
    moin_totals = SanadDetail.objects.values('moin', 'kol').annotate(
        total_bed=Sum('bed'),
        total_bes=Sum('bes'),
        total_curramount=Sum('curramount')
    ).order_by('moin')

    table_moin = []
    for moin in moin_totals:
        total_bed = moin['total_bed'] or 0
        total_bes = moin['total_bes'] or 0
        total_curramount = moin['total_curramount'] or 0
        name, level = acc_coding_dict.get(moin['moin'], ('نام نامشخص', 0))
        kol_info = acc_coding_dict.get(moin['kol'], ('نام کل نامشخص', 0))
        kol_name = kol_info[0]  # نام کل
        kol_level = kol_info[1]  # سطح کل

        table_moin.append({
            'kol_num': moin['kol'],     # شماره کل
            'kol_name': kol_name,       # نام کل
            'moin': moin['moin'],       # شماره معین
            'name': name,               # نام معین
            'level': level,             # سطح معین
            'total_bed': total_bed,     # مجموع بدهکار
            'total_bes': total_bes,     # مجموع بستانکار
            'total_curramount': total_curramount,  # مجموع مانده
        })

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    # ایجاد کانتکست برای ارسال به تمپلیت
    context = {
        'title': 'تراز آزمایشی',
        'user': user,
        'table_kol': table_kol,
        'table_moin': table_moin,
    }

    return render(request, 'taraz_kol.html', context)
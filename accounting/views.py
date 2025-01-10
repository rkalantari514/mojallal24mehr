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
        UserLog.objects.create(
            user=user,
            page='تراز آزمایشی',
            code=0,
        )

    start_time = time.time()  # زمان شروع تابع
    col = kwargs.get('col')
    moin = kwargs.get('moin')
    tafzili = kwargs.get('tafzili')

    # جدول برای kol
    kol_totals = SanadDetail.objects.values('kol').annotate(
        total_bed=Sum('bed'),
        total_bes=Sum('bes'),
        total_curramount=Sum('curramount')  # اضافه کردن curramount
    ).order_by('kol')

    # جدول برای moin
    moin_totals = SanadDetail.objects.values('moin').annotate(
        total_bed=Sum('bed'),
        total_bes=Sum('bes'),
        total_curramount=Sum('curramount')  # اضافه کردن curramount
    ).order_by('moin')

    # جدول برای tafzili
    tafzili_totals = SanadDetail.objects.values('tafzili').annotate(
        total_bed=Sum('bed'),
        total_bes=Sum('bes'),
        total_curramount=Sum('curramount')  # اضافه کردن curramount
    ).order_by('tafzili')

    # تابع برای ایجاد لیست و محاسبه جمع کل
    def create_table(data, key):
        table = []
        total_bed_sum = 0
        total_bes_sum = 0
        total_curramount_sum = 0  # جمع کل curramount

        for item in data:
            total_bed = item['total_bed'] or 0
            total_bes = item['total_bes'] or 0
            total_curramount = item['total_curramount'] or 0  # مقدار curramount

            # دریافت نام دسته‌بندی از مدل AccCoding
            if key == 'kol':
                acc_coding = AccCoding.objects.filter(code=item[key], level=1).first()
                name = acc_coding.name if acc_coding else 'نام نامشخص'
            else:
                name = ''

            table.append({
                key: item[key],
                'name': name,  # اضافه کردن نام دسته‌بندی
                'total_bed': total_bed,
                'total_bes': total_bes,
                'total_curramount': total_curramount,  # اضافه کردن curramount
            })

            total_bed_sum += total_bed
            total_bes_sum += total_bes
            total_curramount_sum += total_curramount  # جمع‌زدن curramount

        # اضافه کردن ردیف جمع کل
        table.append({
            key: 'جمع کل',
            'name': '',  # نام برای ردیف جمع کل خالی است
            'total_bed': total_bed_sum,
            'total_bes': total_bes_sum,
            'total_curramount': total_curramount_sum,  # اضافه کردن curramount
        })

        return table, total_bed_sum, total_bes_sum, total_curramount_sum

    # ایجاد جداول و محاسبه جمع‌های کل
    table_kol, kol_bed_sum, kol_bes_sum, kol_curramount_sum = create_table(kol_totals, 'kol')
    table_moin, moin_bed_sum, moin_bes_sum, moin_curramount_sum = create_table(moin_totals, 'moin')
    table_tafzili, tafzili_bed_sum, tafzili_bes_sum, tafzili_curramount_sum = create_table(tafzili_totals, 'tafzili')

    # جدول مقایسه‌ای بین جمع‌های کل
    comparison_table = [
        {
            'type': 'کل',
            'total_bed': kol_bed_sum,
            'total_bes': kol_bes_sum,
            'total_curramount': kol_curramount_sum,  # اضافه کردن curramount
        },
        {
            'type': 'معین',
            'total_bed': moin_bed_sum,
            'total_bes': moin_bes_sum,
            'total_curramount': moin_curramount_sum,  # اضافه کردن curramount
        },
        {
            'type': 'تفضیلی',
            'total_bed': tafzili_bed_sum,
            'total_bes': tafzili_bes_sum,
            'total_curramount': tafzili_curramount_sum,  # اضافه کردن curramount
        },
    ]

    # محاسبه زمان اجرای تابع
    execution_time = time.time() - start_time
    print(f"زمان کل اجرای تابع: {execution_time:.2f} ثانیه")

    # ایجاد کانتکست برای ارسال به تمپلیت
    context = {
        'title': 'تراز آزمایشی',
        'user': user,
        'table_kol': table_kol,
        'table_moin': table_moin,
        'table_tafzili': table_tafzili,
        'comparison_table': comparison_table,
    }

    return render(request, 'taraz_kol.html', context)




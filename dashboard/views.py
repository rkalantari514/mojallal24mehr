from django.shortcuts import render

from mahakupdate.models import Factor, FactorDetaile
from django.db.models import Sum
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect
from django.utils import timezone
from .models import MasterInfo, MasterReport
import jdatetime  # برای کار با تاریخ جلالی
from datetime import datetime, timedelta
import time
from django.shortcuts import render
from django.utils import timezone
from .models import MasterInfo, MasterReport
import jdatetime  # برای کار با تاریخ جلالی
from datetime import datetime, timedelta
import time
import logging
# Create your views here.



@login_required(login_url='/login')
def Home1(request):
    user=request.user

    factor=Factor.objects.all()
    mablagh_factor_total = factor.aggregate(Sum('mablagh_factor'))['mablagh_factor__sum']
    count_factor_total = factor.count()





    factor_detile=FactorDetaile.objects.all()
    count_factor_detile = factor_detile.count()







    for i in factor_detile:
        print(i.kala.name)
    print('i.kala=====================================================================.name')




    yakhfa = FactorDetaile.objects.filter(kala__name__contains='يخچال')
    mablagh_yakh=yakhfa.aggregate(Sum('mablagh_nahaee'))['mablagh_nahaee__sum']
    yakhdarsad = mablagh_yakh /mablagh_factor_total*100

    lebafa = FactorDetaile.objects.filter(kala__name__contains='لباسشويي')
    mablagh_leba = lebafa.aggregate(Sum('mablagh_nahaee'))['mablagh_nahaee__sum']
    lebadarsad = mablagh_leba / mablagh_factor_total * 100


    colfa = FactorDetaile.objects.filter(kala__name__contains='کولر')
    mablagh_col = colfa.aggregate(Sum('mablagh_nahaee'))['mablagh_nahaee__sum']
    coldarsad = mablagh_col / mablagh_factor_total * 100





    print(mablagh_factor_total)

    context = {

        'factor': factor,
        'user': user,
        'mablagh_factor_total':mablagh_factor_total,
        'count_factor_total':count_factor_total,
        'factor_detile':factor_detile,
        'mablagh_yakh':mablagh_yakh,
        'yakhdarsad':yakhdarsad,


        'mablagh_leba':mablagh_leba,
        'lebadarsad':lebadarsad,


        'mablagh_col':mablagh_col,
        'coldarsad':coldarsad,
    }



    return render(request, 'homepage.html',context)




# تنظیمات لاگ‌گیری
logger = logging.getLogger(__name__)

from django.shortcuts import render
from django.utils import timezone
from .models import MasterInfo, MasterReport
import jdatetime  # برای کار با تاریخ جلالی
from datetime import datetime, timedelta
import time
import logging

# تنظیمات لاگ‌گیری
logger = logging.getLogger(__name__)

def CreateReport(request):
    start_time = time.time()  # زمان شروع ویو

    # بررسی وجود MasterInfo فعال
    master_info = MasterInfo.objects.filter(is_active=True).last()
    if not master_info:
        print("هیچ شرکت فعالی یافت نشد.")
        return

    acc_year = master_info.acc_year

    try:
        # تبدیل ۱/۱/سال مالی به تاریخ میلادی
        start_date_jalali = jdatetime.date(acc_year, 1, 1)  # ۱ فروردین سال مالی
        start_date_gregorian = start_date_jalali.togregorian()  # تبدیل به میلادی
    except Exception as e:
        logger.error(f"خطا در تبدیل تاریخ: {str(e)}")
        print("خطا در تبدیل تاریخ.")
        return

    # تاریخ جاری
    end_date_gregorian = timezone.now().date()

    # لیست برای ذخیره رکوردهای جدید
    reports_to_create = []

    # ایجاد رکوردهای روزانه از تاریخ شروع تا تاریخ جاری
    current_date = start_date_gregorian
    while current_date <= end_date_gregorian:
        # بررسی وجود رکورد برای این روز
        report, created = MasterReport.objects.get_or_create(
            day=current_date,
            defaults={
                'total_mojodi': 0,
                'value_of_purchased_goods': 0,
                'cost_of_sold_goods': 0,
                'revenue_from_sales': 0,
            }
        )

        if created:
            reports_to_create.append(report)
            logger.info(f"رکورد برای تاریخ {current_date} ایجاد شد.")
        else:
            logger.info(f"رکورد برای تاریخ {current_date} از قبل وجود داشت.")

        # TODO: آپدیت سایر ستون‌ها (total_mojodi, value_of_purchased_goods, ...)

        # افزایش تاریخ به روز بعد
        current_date += timedelta(days=1)

    # محاسبه زمان اجرای ویو
    end_time = time.time()
    execution_time = end_time - start_time

    # ذخیره زمان آخرین گزارش در مدل MasterInfo
    master_info.last_report_time = timezone.now()
    master_info.save()

    # چاپ نتیجه در کنسول
    print(f"message: گزارش‌ها با موفقیت ایجاد شدند")
    print(f"execution_time: {execution_time:.2f} ثانیه")
    print(f"start_date: {start_date_gregorian}")
    print(f"end_date: {end_date_gregorian}")

    return redirect('/updatedb')

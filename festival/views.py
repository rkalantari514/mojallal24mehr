from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.db import transaction
from django.utils import timezone
import time
from django.db.models import F

from custom_login.models import UserLog
from custom_login.views import page_permision
from .models import Festival, CustomerPoints
from mahakupdate.models import Factor
from decimal import Decimal
import math

from django.shortcuts import redirect
from django.db import transaction
from django.utils import timezone
from .models import Festival, CustomerPoints
from mahakupdate.models import Factor
from decimal import Decimal
import math  # اطمینان از import بودن ماژول math

def Calculate_and_award_points(request):
    active_festivals = Festival.objects.filter(is_active=True)
    updated_points_count = 0
    created_points_count = 0
    deleted_points_count = 0

    for festival in active_festivals:
        start_date = festival.start_date
        end_date = festival.end_date
        min_invoice_amount = festival.min_invoice_amount
        points_per_purchase_ratio = festival.points_per_purchase_ratio

        eligible_factors = Factor.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
        ).select_related('person')

        existing_points_for_festival = CustomerPoints.objects.filter(festival=festival).select_related('factor')
        existing_points_map = {(cp.customer_id, cp.factor_id): cp for cp in existing_points_for_festival}
        points_to_create = []
        points_to_update = []
        points_to_delete_ids = []

        for factor in eligible_factors:
            invoice_value = Decimal(factor.mablagh_factor) - Decimal(factor.takhfif)
            calculated_points = 0
            if invoice_value >= min_invoice_amount and points_per_purchase_ratio > 0:
                calculated_points_float = invoice_value / points_per_purchase_ratio
                calculated_points = math.floor(calculated_points_float)  # تغییر به math.floor

                # calculated_points_float = invoice_value / points_per_purchase_ratio
                # calculated_points = int(round(calculated_points_float))

            if (factor.person_id, factor.id) in existing_points_map:
                customer_point = existing_points_map[(factor.person_id, factor.id)]
                if customer_point.points_awarded != calculated_points:
                    if calculated_points > 0:
                        customer_point.points_awarded = calculated_points
                        points_to_update.append(customer_point)
                        updated_points_count += 1
                    else:
                        points_to_delete_ids.append(customer_point.id)
                        del existing_points_map[(factor.person_id, factor.id)] # برای جلوگیری از پردازش مجدد
                else:
                    if calculated_points == 0:
                        points_to_delete_ids.append(customer_point.id)
                        del existing_points_map[(factor.person_id, factor.id)] # برای جلوگیری از پردازش مجدد
                    else:
                        del existing_points_map[(factor.person_id, factor.id)] # فاکتور همچنان واجد شرایط است و امتیاز تغییر نکرده
            elif calculated_points > 0:
                points_to_create.append(CustomerPoints(
                    festival=festival,
                    customer=factor.person,
                    factor=factor,
                    points_awarded=calculated_points
                ))
                created_points_count += calculated_points

        # هر امتیازی که در existing_points_map باقی مانده، مربوط به فاکتورهایی است که دیگر واجد شرایط نیستند یا حذف شده‌اند.
        points_to_delete_ids.extend([cp.id for cp in existing_points_map.values()])
        deleted_points_count += len(points_to_delete_ids)

        if points_to_delete_ids:
            CustomerPoints.objects.filter(id__in=points_to_delete_ids).distinct().delete()

        with transaction.atomic():
            CustomerPoints.objects.bulk_create(points_to_create)
            CustomerPoints.objects.bulk_update(points_to_update, ['points_awarded'])

    return redirect('/updatedb')





def FestivalTotal(request):
    name = 'جشنواره'
    result = page_permision(request, name)  # بررسی دسترسی
    if result:  # اگر هدایت انجام شده است
        return result
    user = request.user
    if user.mobile_number != '09151006447':
        UserLog.objects.create(user=user, page='جشنواره', code=0)

    start_time = time.time()  # زمان شروع تابع


    points = CustomerPoints.objects.filter(festival__is_active=True).annotate(
        mablagh_k=F('factor__mablagh_factor') - F('factor__takhfif')
    )


    context = {
        'title': 'جشنواره',
        'user': user,
        'points': points,
    }



    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'festival_total.html', context)




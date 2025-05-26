from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.db import transaction
from django.utils import timezone
import time
from django.db.models import F

from custom_login.models import UserLog
from custom_login.views import page_permision
from mahakupdate.sendtogap import send_sms, check_sms_status
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

from django.shortcuts import redirect
from django.db import transaction
from django.utils import timezone
from .models import Festival, CustomerPoints
from mahakupdate.models import Factor
from decimal import Decimal
import math

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

        # بررسی امتیازات موجود و حذف اگر فاکتور خارج از بازه جشنواره است
        for (customer_id, factor_id), customer_point in existing_points_map.items():
            try:
                factor = Factor.objects.get(id=customer_point.factor_id)
                if not (festival.start_date <= factor.date <= festival.end_date):
                    points_to_delete_ids.append(customer_point.id)
            except Factor.DoesNotExist:
                # اگر فاکتور دیگر وجود ندارد، امتیاز را حذف کنید
                points_to_delete_ids.append(customer_point.id)

        for factor in eligible_factors:
            if factor.person is None:
                print(f"Warning: Factor with ID {factor.id} has no associated person. Skipping.")
                continue  # رد شدن از این فاکتور و رفتن به فاکتور بعدی
            invoice_value = Decimal(factor.mablagh_factor) - Decimal(factor.takhfif)
            calculated_points = 0
            if factor.person is None:
                print(f"Warning: Factor with ID {factor.id} has no associated person. Skipping.")
                continue  # رد شدن از این فاکتور و رفتن به فاکتور بعدی
            if invoice_value >= min_invoice_amount and points_per_purchase_ratio > 0:
                calculated_points_float = invoice_value / points_per_purchase_ratio
                calculated_points = math.floor(calculated_points_float)

            if (factor.person_id, factor.id) in existing_points_map:
                customer_point = existing_points_map[(factor.person_id, factor.id)]
                if customer_point.points_awarded != calculated_points:
                    if calculated_points > 0:
                        customer_point.points_awarded = calculated_points
                        points_to_update.append(customer_point)
                        updated_points_count += 1
                    else:
                        points_to_delete_ids.append(customer_point.id)
                        del existing_points_map[(factor.person_id, factor.id)]
                else:
                    if calculated_points == 0:
                        points_to_delete_ids.append(customer_point.id)
                        del existing_points_map[(factor.person_id, factor.id)]
                    else:
                        del existing_points_map[(factor.person_id, factor.id)]
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


    # points = CustomerPoints.objects.filter(festival__is_active=True,points_awarded__gt=100).annotate(
    points = CustomerPoints.objects.filter(festival__is_active=True).annotate(
        mablagh_k=F('factor__mablagh_factor') - F('factor__takhfif')
    )
    festivals=Festival.objects.filter(is_active=True)

    context = {
        'title': 'جشنواره',
        'user': user,
        'points': points,
        'festivals': festivals,
    }

    for t in points:
        try:
            if t.message_id and t.status_code != 2 and t.status_code != 3 and t.status_code != 4:
                status_code = check_sms_status(t.message_id)
                if status_code is not None:  # فقط اگر مقدار معتبر باشد، ذخیره شود
                    t.status_code = status_code
                    t.save()
        except:
            pass

    print(f"زمان کل اجرای تابع: {time.time() - start_time:.2f} ثانیه")

    return render(request, 'festival_total.html', context)



from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from .models import CustomerPoints
import requests
import re
from django.conf import settings  # برای دسترسی به ip_panel_token

def normalize_phone_number(phone_number):
    print('phone_number:', phone_number)
    if not phone_number:
        return None
    phone_number = phone_number.strip()
    print('phone_number.strip():', phone_number)

    # حذف + در ابتدای +98
    if phone_number.startswith('+98'):
        phone_number = phone_number[1:]
        print('after removing +:', phone_number)

    # حذف 98 در ابتدای 989...
    if phone_number.startswith('98'):
        phone_number = '0' + phone_number[2:]
        print('after adding 0 and removing 98:', phone_number)
    elif phone_number.startswith('09') and len(phone_number) == 11:
        print('already in 09 format:', phone_number)
        return phone_number
    elif phone_number.startswith('9') and len(phone_number) == 10:
        phone_number = '0' + phone_number
        print('added 0 to 9 format:', phone_number)
        return phone_number
    else:
        print('invalid format:', phone_number)
        return None

    # بررسی نهایی فرمت 09xxxxxxxxx
    if phone_number.startswith('09') and len(phone_number) == 11:
        print('final 09 format:', phone_number)
        return phone_number
    else:
        print('final invalid format:', phone_number)
        return None

@transaction.atomic
def send_bulk_promotional_sms(request):
    user = request.user
    # st = (0, 1, 2, 3, 4)
    st = (0, 1, 2, 3, 4)
    customer_points = CustomerPoints.objects.filter(festival__is_active=True).exclude(status_code__in=st)
    print('customer_points.count()')
    print(customer_points.count())

    sent_count = 0
    failed_count = 0
    invalid_count = 0
    skipped_count = 0
    counter = 1

    for customer_point in customer_points:
        print('counter=',counter)
        # if counter > 25:
        #     break

        person = customer_point.customer
        phone_number = normalize_phone_number(person.mobile)
        if not phone_number:
            phone_number = normalize_phone_number(person.tel1)
        if not phone_number:
            phone_number = normalize_phone_number(person.tel2)
        if not phone_number:
            phone_number = normalize_phone_number(person.fax)

        print('normalize_phone_number:',phone_number)

        if phone_number:
            message1 = f"""مشتری گرامی {customer_point.customer.clname}
تشکر بابت شرکت در جشنواره {customer_point.festival.name}
با توجه به فاکتور خرید شماره {customer_point.factor.code}
{customer_point.points_awarded} امتیاز کسب کرده‌اید.
مجموع امتیازات شما در این جشنواره:
{customer_point.total_point_this_festival()} امتیاز
منتظر خرید بعدی شما هستیم
هر {customer_point.festival.min_invoice_amount / 10000000} میلیون تومان خرید یک امتیاز
فروشگاه سرای یاس مجلل"""

            message = f"""{customer_point.customer.clname} عزیز 
سپاس از  شرکت در جشنواره {customer_point.festival.name}
با فاکتور  {customer_point.factor.code} شما {customer_point.points_awarded} امتیاز گرفتین!
 مجموع امتیازات شما  {customer_point.total_point_this_festival()} 
هر {customer_point.festival.min_invoice_amount / 10000000} میلیون خرید = 1 امتیاز 
منتظر خرید بعدی‌تون هستیم!
سرای یاس مجلل"""










            message_id = None

            # خط زیر برای ارسال واقعی به شماره مشتری است (در آینده فعال کنید)
            message_id = send_sms(phone_number, message)

            # خط زیر فقط برای تست به شماره ثابت ارسال می‌کند
            # message_id = send_sms('09151006447', message)
            # message_id = send_sms(user.mobile_number, message)

            if message_id:
                customer_point.phone_number = phone_number
                customer_point.status_code = 1
                customer_point.message_id = message_id
                customer_point.save()
                sent_count += 1
            else:
                customer_point.phone_number = phone_number
                customer_point.status_code = None  # Failed (در صورت عدم دریافت message_id)
                customer_point.save()
                failed_count += 1
        else:
            customer_point.status_code = 404  # No Verified Number
            customer_point.save()
            invalid_count += 1

        counter += 1

    messages.info(request, f"تعداد پیامک‌های ارسالی (تلاش): {sent_count}")
    messages.error(request, f"تعداد ارسال‌های ناموفق (در زمان تلاش): {failed_count}")
    messages.warning(request, f"تعداد شماره‌های نامعتبر: {invalid_count}")
    messages.info(request, f"تعداد رکوردهای بررسی شده: {counter - 1}")

    return redirect('/festival_total')

from operator import is_not

from django.contrib.auth import logout
from mahakupdate.sendtogap import send_to_managers, send_to_admin
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .forms import LoginForm, ForgotPasswordForm
from .models import CustomUser, MyPage, CustomGroup
import random

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            mobile_number = form.cleaned_data['mobile_number']
            password = form.cleaned_data['password']

            user = authenticate(request, username=mobile_number, password=password)

            if user is not None:
                if user.password_expiry_date and user.password_expiry_date < timezone.now():
                    new_password = str(random.randint(1000, 9999))
                    user.set_password(new_password)
                    user.set_password_expiry()
                    user.save()
                    mobiles = [mobile_number]
                    send_to_admin(f'رمز جدید {mobile_number}-{user.first_name}-{user.last_name}-: {new_password}')  # ارسال رمز جدید به کاربر
                    send_to_managers(mobiles,f'رمز جدید شما: {new_password}')
                    messages.info(request, 'رمز عبور شما منقضی شده و یک رمز جدید به شما ارسال شد.')
                login(request, user)
                return redirect('/')
            else:
                messages.error(request, 'اطلاعات معتبر نیست.')

    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})



def forgot_password_view(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            mobile_number = form.cleaned_data['mobile_number']
            try:
                user = CustomUser.objects.get(mobile_number=mobile_number)  # جستجو با استفاده از mobile_number
                new_password = str(random.randint(1000, 9999))  # تولید عدد 4 رقمی
                user.set_password(new_password)  # تنظیم رمز جدید
                user.set_password_expiry()  # تنظیم تاریخ انقضا
                user.save()
                mobiles = [mobile_number]
                send_to_admin(f'رمز جدید {mobile_number}-{user.first_name}-{user.last_name}-: {new_password}')  # ارسال رمز جدید به کاربر
                send_to_managers(mobiles,f'رمز جدید شما: {new_password}')  # ارسال رمز جدید به کاربر
                messages.success(request, 'رمز جدید برای شما ارسال شد.')
                return redirect('/login')
            except CustomUser.DoesNotExist:
                messages.error(request, 'کاربری با این شماره موبایل یافت نشد.')
    else:
        form = ForgotPasswordForm()

    return render(request, 'forgot_password.html', {'form': form})

def log_out(request):
    logout(request)
    return redirect('/')



from django.shortcuts import render
from .models import CustomUser, UserLog
from collections import Counter

from django.shortcuts import render
from .models import CustomUser, UserLog
from collections import Counter

from collections import Counter
from django.db.models import Count
from django.utils.timezone import now, timedelta

from collections import Counter
from django.db.models import Count
from django.utils.timezone import now, timedelta

from collections import Counter
from django.db.models import Count
from django.utils.timezone import now, timedelta

from collections import Counter
from django.db.models import Count
from django.utils.timezone import now, timedelta

from collections import Counter
from django.db.models import Count
from django.utils.timezone import now, timedelta

from collections import Counter
from django.db.models import Count
from django.utils.timezone import now, timedelta

from collections import Counter
from django.db.models import Count
from django.utils.timezone import now, timedelta

from collections import Counter
from django.db.models import Count
from django.utils.timezone import now, timedelta

from collections import Counter
from django.db.models import Count
from django.utils.timezone import now, timedelta


def dashboard_view(request):
    managers = ["مجید وارسته", "مهدی وارسته", "رضا وارسته", "صادق وارسته"]
    varaste_users = CustomUser.objects.filter(last_name__icontains="وارسته")
    user_logs = UserLog.objects.filter(user__in=varaste_users)

    # محاسبه مجموع و درصد بازدید هر مدیر
    user_visit_counts = Counter([log.user for log in user_logs])
    total_visits = sum(user_visit_counts.values())
    table_data = [
        {
            "user": f"{user.first_name} {user.last_name}",
            "visits": user_visit_counts.get(user, 0),
            "percentage": round((user_visit_counts.get(user, 0) / total_visits) * 100, 2) if total_visits > 0 else 0
        }
        for user in varaste_users
    ]

    # محاسبه بازدید صفحات برای هر مدیر
    page_visit_counts = {manager: {} for manager in managers}

    for user in varaste_users:
        full_name = f"{user.first_name} {user.last_name}"
        user_page_logs = user_logs.filter(user=user).values('page').annotate(count=Count('page'))

        for entry in user_page_logs:
            page_visit_counts[full_name][entry["page"]] = entry["count"]

    table_page_visits = [
        {"manager": manager, "pages": page_visit_counts.get(manager, {})} for manager in managers
    ]

    # پراکندگی ساعت بازدید در ۸ بازه‌ی ۳ ساعته برای هر مدیر
    time_slots = {"00-03": {}, "03-06": {}, "06-09": {}, "09-12": {}, "12-15": {}, "15-18": {}, "18-21": {},
                  "21-24": {}}

    for user in varaste_users:
        full_name = f"{user.first_name} {user.last_name}"
        visit_hours = user_logs.filter(user=user).values_list('time__hour', flat=True)

        for hour in visit_hours:
            for slot in time_slots.keys():
                start, end = map(int, slot.split('-'))
                if start <= hour < end:
                    time_slots[slot][full_name] = time_slots[slot].get(full_name, 0) + 1

    visit_by_hour = [{"hour_range": k, "data": v} for k, v in time_slots.items()]

    context = {
        "table_data": table_data,
        "table_page_visits": table_page_visits,
        "visit_by_hour": visit_by_hour,
        "managers": managers
    }
    return render(request, 'dashboard.html', context)


from django.http import Http404  # برای هدایت به صفحه 404


from django.http import Http404

from django.http import Http404

from django.shortcuts import redirect

from django.shortcuts import redirect

from django.shortcuts import redirect, resolve_url
from django.http import Http404

from django.shortcuts import redirect, resolve_url
from django.http import Http404

from django.shortcuts import resolve_url, redirect

from django.shortcuts import redirect, resolve_url
from django.http import Http404

from django.shortcuts import redirect, resolve_url
from django.http import Http404

def page_permision(request, name):
    v_name = request.resolver_match.view_name  # تشخیص خودکار نام ویو
    # به‌روزرسانی یا ایجاد صفحه با استفاده از نام به‌جای p_url
    page, created = MyPage.objects.update_or_create(
        v_name= v_name,
        defaults={
            'name': name,
            'p_url': request.path  # همچنان ذخیره p_url برای اطلاعات اضافی
        }
    )

    # بررسی دسترسی کاربر
    if not request.user.is_superuser:  # اگر کاربر superuser نیست
        user_groups = set(request.user.groups.values_list('name', flat=True))  # گرفتن نام گروه‌ها به جای اشیاء
        allowed_groups = set(CustomGroup.objects.filter(allowed_pages=page).values_list('name', flat=True))  # گرفتن نام گروه‌ها

        print('page:', page)
        print('user_groups:', user_groups)
        print('allowed_groups:', allowed_groups)

        # بررسی اشتراک گروه‌ها
        if not user_groups.intersection(allowed_groups):  # اگر اشتراک وجود نداشت
            print('اشتراک وجود ندارد')
            default_page = (
                CustomGroup.objects.filter(id__in=request.user.groups.values_list('id', flat=True))
                .exclude(default_page__isnull=True)
                .first()
            )

            if default_page and default_page.default_page and default_page.default_page.p_url:  # بررسی وجود صفحه پیش‌فرض
                print('Redirecting to:', default_page.default_page.p_url)
                return redirect(default_page.default_page.p_url)  # هدایت به صفحه پیش‌فرض

            raise Http404("شما اجازه دسترسی به این صفحه را ندارید.")

    # اگر کاربر مجاز بود، ادامه دهید
    # return None

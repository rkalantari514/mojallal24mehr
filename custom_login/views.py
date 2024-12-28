from django.contrib.auth import logout
from mahakupdate.sendtogap import send_to_managers
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .forms import LoginForm, ForgotPasswordForm
from .models import CustomUser
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
                    send_to_managers(f'رمز جدید شما: {new_password}')
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
                send_to_managers(f'رمز جدید شما: {new_password}')  # ارسال رمز جدید به کاربر
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




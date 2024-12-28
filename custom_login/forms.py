from django import forms

from mahakupdate.sendtogap import send_to_managers
from .models import CustomUser
import random
class LoginForm(forms.Form):
    mobile_number = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder':"×××××××××09" ,
            'maxlength':"11",
            'class': 'form-control'
        }),
        label='موبایل'
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control text-center',
        }),
        label='رمز عبور'
    )

    def clean_mobile_number(self):
        mobile_number = self.cleaned_data.get('mobile_number')
        if mobile_number[0] != "0" or mobile_number[1] != "9" or len(mobile_number) != 11:
            raise forms.ValidationError('شماره موبایل اشتباه است')
        return mobile_number

    def forgot_password(self):
        mobile_number = self.cleaned_data.get('mobile_number')
        try:
            user = CustomUser.objects.get(username=mobile_number)  # فرض بر این است که شماره موبایل نام کاربری است
            new_password = str(random.randint(1000, 9999))  # تولید عدد 4 رقمی
            user.set_password(new_password)  # تنظیم رمز جدید
            user.set_password_expiry()  # تنظیم تاریخ انقضا
            user.save()
            send_to_managers(f'رمز جدید شما: {new_password}')  # ارسال رمز جدید به کاربر
            return True
        except CustomUser.DoesNotExist:
            return False

class ForgotPasswordForm(forms.Form):
    mobile_number = forms.CharField(
        max_length=11,
        widget=forms.TextInput(attrs={
            'placeholder': "شماره موبایل",
            'class': 'form-control'
        }),
        label='موبایل'
    )
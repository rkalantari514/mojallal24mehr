from django import forms
from .models import Tracking

from django import forms
from .models import Tracking

from django import forms
from .models import Tracking, SampleSMS
from django import forms
from .models import Tracking, CALL_STATUS
from datetime import timedelta
from django.utils import timezone



class SMSTrackingForm(forms.ModelForm):
    phone_number = forms.ChoiceField(
        choices=[],  # لیست شماره‌های معتبر همراه با نام فیلد تنظیم می‌شود
        required=True,
        label="شماره تلفن",
        widget=forms.Select(attrs={
            'placeholder': 'شماره تلفن مشتری',
            # 'class': 'selectpicker form-control',
            'class': 'custom-select my-1 mr-sm-2',

            # 'data-live-search': "true",
            'id': 'id_phone_number'
        })
    )

    sample_sms = forms.ModelChoiceField(
        queryset=SampleSMS.objects.filter(is_active=True),
        required=False,
        label="پیامک اصلی",
        widget=forms.Select(attrs={
            'placeholder': 'انتخاب پیامک نمونه',
            # 'class': 'selectpicker form-control',
            'class': 'custom-select my-1 mr-sm-2',
            # 'data-live-search': "true",
            'id': 'id_sample_sms'
        })
    )
    message = forms.CharField(
        required=False,
        label="ادامه پیامک",
        widget=forms.Textarea(attrs={
            'placeholder': 'متن پیامک تکمیلی را اینجا وارد کنید...',
            'class': 'form-control',
            'rows': 4,
            'id': 'id_message'
        })
    )



    class Meta:
        model = Tracking
        fields = [ 'phone_number', 'sample_sms','message']

    def __init__(self, *args, **kwargs):
        customer = kwargs.pop('customer', None)  # دریافت مشتری به عنوان ورودی
        super().__init__(*args, **kwargs)
        if customer:
            person = customer.person
            if person:
                # فیلتر شماره‌های معتبر (شروع با 09 و طول 11 رقمی)
                valid_numbers = []
                for field_name, phone in [
                    ('موبایل', person.mobile),
                    ('تلفن1', person.tel1),
                    ('تلفن2', person.tel2),
                    ('فکس', person.fax)
                ]:
                    if phone and phone.startswith('09') and len(phone) == 11 and phone not in valid_numbers:
                        valid_numbers.append((phone, f"{field_name}: {phone}"))

                self.fields['phone_number'].choices = valid_numbers








class CallTrackingForm(forms.ModelForm):
    phone_number = forms.ChoiceField(
        choices=[],  # مقدار توسط ویو تنظیم می‌شود
        required=True,
        label="شماره تلفن",
        widget=forms.Select(attrs={'class': 'custom-select'}),
    )

    call_status = forms.ChoiceField(
        choices=[(key, value["persian"]) for key, value in CALL_STATUS.items()],
        required=True,
        label="وضعیت تماس",
        widget=forms.Select(attrs={'class': 'custom-select'}),
    )

    call_description = forms.CharField(
        required=False,
        label="شرح تماس",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4,'placeholder': 'شرح تماس را اینجا وارد کنید...',}),
    )

    next_reminder_date = forms.IntegerField(
        required=True,
        label="زمان پیگیری بعدی",
        widget=forms.Select(choices=[
            (30, "یک ماه دیگر"),
            (14, "دو هفته دیگر"),
            (7, "یک هفته دیگر"),
            (3, "۳ روز دیگر"),
            (1, "یک روز دیگر")

        ], attrs={'class': 'custom-select'}),
    )

    class Meta:
        model = Tracking
        fields = ['phone_number', 'call_status', 'call_description', 'next_reminder_date']

    def clean_next_reminder_date(self):
        """ تبدیل عدد به تاریخ صحیح """
        next_reminder_days = self.cleaned_data['next_reminder_date']
        return timezone.now().date() + timedelta(days=next_reminder_days)



    def __init__(self, *args, **kwargs):
        customer = kwargs.pop('customer', None)  # دریافت مشتری به عنوان ورودی
        super().__init__(*args, **kwargs)
        if customer:
            person = customer.person
            if person:
                # فیلتر شماره‌های معتبر (شروع با 09 و طول 11 رقمی)
                valid_numbers = []
                for field_name, phone in [
                    ('موبایل', person.mobile),
                    ('تلفن1', person.tel1),
                    ('تلفن2', person.tel2),
                    ('فکس', person.fax)
                ]:
                    if phone and phone not in valid_numbers:
                        # 🔹 شماره‌ای که با '0' شروع نمی‌شود و ۸ رقمی است
                        if not phone.startswith('0') and len(phone) == 8:
                            valid_numbers.append((phone, f"{field_name}: {phone}"))

                        # 🔹 شماره‌ای که **با '051' شروع نمی‌شود** و ۱۱ رقمی است
                        elif not phone.startswith('051') and len(phone) == 11:
                            valid_numbers.append((phone, f"{field_name}: {phone}"))

                        # 🔹 اگر شماره **با '051' شروع شد و ۱۱ رقمی بود**، `051` را حذف کن
                        elif phone.startswith('051') and len(phone) == 11:
                            corrected_phone = phone[3:]  # حذف '051'
                            valid_numbers.append((corrected_phone, f"{field_name}: {corrected_phone}"))

                self.fields['phone_number'].choices = valid_numbers

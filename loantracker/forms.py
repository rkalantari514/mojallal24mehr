from django import forms
from .models import Tracking

from django import forms
from .models import Tracking

from django import forms
from .models import Tracking, SampleSMS

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
        queryset=SampleSMS.objects.all(),
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
                    if phone and phone.startswith('09') and len(phone) == 11:
                        valid_numbers.append((phone, f"{field_name}: {phone}"))

                self.fields['phone_number'].choices = valid_numbers

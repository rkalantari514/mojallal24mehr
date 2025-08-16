# forms.py
from django import forms
from persianutils import standardize

from accounting.models import BedehiMoshtari


# forms.py
from django import forms
from persianutils import standardize


def fix_persian_characters(value):
    """تبدیل کاراکترهای غیراستاندارد فارسی (مثل 'ي' به 'ی' و 'ك' به 'ک')"""
    if not value:
        return ""
    return standardize(str(value))


class BedehiMoshtariChoiceField(forms.ModelChoiceField):
    """فیلد سفارشی برای نمایش زیبای مشتریان در کرکره"""
    def label_from_instance(self, obj):
        person = obj.person
        if person:
            name = fix_persian_characters(person.name or "")
            lname = fix_persian_characters(person.lname or "")
            code = person.code
        else:
            name = "نامشخص"
            lname = "نامشخص"
            code = "نامشخص"

        tafzili = obj.tafzili or "نامشخص"

        # قالب نمایش: کد فرد | کد تفصیلی | نام | نام خانوادگی
        return f"{code} | {tafzili} | {name} | {lname}"


class SalesExpertForm(forms.Form):
    """فرم انتخاب مشتری برای کارشناسان فروش (بدون لاگین)"""
    bedehi_moshtari = BedehiMoshtariChoiceField(
        # فقط مشتریانی که person دارند + بهینه‌سازی با select_related
        queryset=BedehiMoshtari.objects.select_related('person').exclude(person__isnull=True).order_by('person__lname'),
        label="انتخاب مشتری",
        empty_label="یک مشتری انتخاب کنید...",
        widget=forms.Select(attrs={
            'class': 'form-control selectpicker',
            'data-live-search': 'true',
            'data-width': '100%',
            'title': 'جستجوی مشتری بر اساس نام، کد یا تفصیلی...',
            'data-none-selected-text': 'مشتری انتخاب کنید',
        })
    )
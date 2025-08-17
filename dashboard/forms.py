# forms.py
from django import forms
from persianutils import standardize

from accounting.models import BedehiMoshtari


# forms.py
from django import forms
from persianutils import standardize


# forms.py
from django import forms
from persianutils import standardize


def fix_persian_characters(value):
    """استانداردسازی کاراکترهای فارسی"""
    if not value:
        return ""
    return standardize(str(value))


class SalesExpertForm(forms.Form):
    bedehi_moshtari = forms.ChoiceField(
        label="انتخاب مشتری",
        choices=[],  # پویا پر می‌شود
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control selectpicker',
            'data-live-search': 'true',
            'data-width': '100%',
            'title': 'جستجوی مشتری بر اساس نام، کد یا تفصیلی...',
            'id': 'bedehi-selector',

        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [('', 'یک مشتری انتخاب کنید...')]

        # فقط مشتریانی که person دارند و tafzili معتبر است
        queryset = BedehiMoshtari.objects.select_related('person').exclude(
            person__isnull=True
        ).exclude(tafzili__isnull=True).order_by('person__lname')

        for obj in queryset:
            person = obj.person
            name = fix_persian_characters(person.name or "")
            lname = fix_persian_characters(person.lname or "")
            code = person.code
            tafzili = obj.tafzili

            label = f"{code} | {tafzili} | {name} | {lname}"
            choices.append((tafzili, label))  # tafzili به عنوان value

        self.fields['bedehi_moshtari'].choices = choices
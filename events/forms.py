# events/forms.py

from django import forms
from .models import EventCategory, Event, EventDetail, Resolution, EventImage
from django.forms import inlineformset_factory



from jalali_date.fields import JalaliDateField, SplitJalaliDateTimeField
from jalali_date.widgets import AdminJalaliDateWidget, AdminSplitJalaliDateTime


# -----------------------------------------------------------
# 1. فرم برای EventCategory
# -----------------------------------------------------------
class EventCategoryForm(forms.ModelForm):
    class Meta:
        model = EventCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام دسته بندی'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'توضیحات'}),
        }

# -----------------------------------------------------------
# 2. فرم برای Event
# -----------------------------------------------------------
class EventForm(forms.ModelForm):
    # استفاده از DateInput استاندارد جنگو برای فیلدهای تاریخ
    # first_occurrence = forms.DateField(label='زمان اولین رویداد',
    #                                    widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}))

    first_occurrence = forms.DateField(
        widget=forms.DateInput(),
    )

    last_occurrence = forms.DateField(
        widget=forms.DateInput(),
    )

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.fields['first_occurrence'] = JalaliDateField(
            label=('تاریخ اولین رویداد'),
            widget=AdminJalaliDateWidget
        )

        self.fields['last_occurrence'] = JalaliDateField(
            label=('تاریخ آخرین رویداد'),
            widget=AdminJalaliDateWidget
        )





    class Meta:
        model = Event
        fields = ['category', 'name', 'repeat_interval', 'first_occurrence', 'last_occurrence', 'reminder_interval', 'is_active']
        widgets = {
            'category': forms.Select(attrs={'placeholder': 'دسته بندی', 'class': 'selectpicker text-left','data-live-search' : "true",}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام رویداد'}),
            'repeat_interval': forms.Select(attrs={'placeholder': 'بازه تکرار', 'class': 'selectpicker','data-live-search' : "true",}),
            'reminder_interval': forms.Select(attrs={'placeholder': 'یاد آوری', 'class': 'selectpicker','data-live-search' : "true",}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    # متد __init__ دیگر برای تبدیل تاریخ شمسی لازم نیست
    # اما اگر نیاز به تنظیمات اولیه دیگر دارید، می‌توانید آن را نگه دارید.
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)


# -----------------------------------------------------------
# 3. فرم برای EventDetail
# -----------------------------------------------------------
# events/forms.py

from django import forms
from django.forms import inlineformset_factory
from .models import EventDetail, Resolution, EventImage

# -----------------------------------------------------------
# EventDetail form (دیگه فیلد event داخل فرم نیست - در ویو ست میشه)
# -----------------------------------------------------------
class EventDetailForm(forms.ModelForm):
    # occurrence_date = forms.DateField(
    #     label='تاریخ برگزاری',
    #     widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    # )
    occurrence_date = forms.DateField(
        widget=forms.DateInput(),
    )

    def __init__(self, *args, **kwargs):
        super(EventDetailForm, self).__init__(*args, **kwargs)
        self.fields['occurrence_date'] = JalaliDateField(
            label=('تاریخ  برگزاری'),
            widget=AdminJalaliDateWidget
        )






    class Meta:
        model = EventDetail
        # توجه: 'event' حذف شده — در ویو خودش ست میشه
        fields = ['occurrence_date', 'status_relative_to_schedule', 'report']
        widgets = {
            'status_relative_to_schedule': forms.Select(attrs={'class': 'form-control'}),
            'report': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }


# -----------------------------------------------------------
# Resolution form
# -----------------------------------------------------------
class ResolutionForm(forms.ModelForm):
    # due_date = forms.DateField(label='مهلت انجام', required=False,
    #                            widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    # completed_date = forms.DateField(label='تاریخ انجام', required=False,
    #                                  widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))


    due_date = forms.DateField(
        widget=forms.DateInput(),
    )

    completed_date = forms.DateField(
        widget=forms.DateInput(),
    )


    class Meta:
        model = Resolution
        fields = ['text', 'responsible_person', 'status', 'due_date', 'completed_date']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'responsible_person': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(ResolutionForm, self).__init__(*args, **kwargs)
        self.fields['due_date'] = JalaliDateField(
            label=('مهلت انجام'),
            widget=AdminJalaliDateWidget,
            required=False  # 👈 این خط را اضافه کنید

        )

        self.fields['completed_date'] = JalaliDateField(
            label=('تاریخ انجام'),
            widget=AdminJalaliDateWidget,
            required=False
        )


# -----------------------------------------------------------
# EventImage form
# -----------------------------------------------------------
class EventImageForm(forms.ModelForm):
    class Meta:
        model = EventImage
        fields = ['image', 'caption']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'caption': forms.TextInput(attrs={'class': 'form-control'}),
        }


# -----------------------------------------------------------
# Inline formsets (برای EventDetail)
# -----------------------------------------------------------
ResolutionFormSet = inlineformset_factory(
    EventDetail, Resolution, form=ResolutionForm, extra=1, can_delete=True
)

EventImageFormSet = inlineformset_factory(
    EventDetail, EventImage, form=EventImageForm, extra=1, can_delete=True
)

# events/forms.py

from django import forms
from .models import EventCategory, Event, EventDetail, Resolution, EventImage
from django.forms import inlineformset_factory

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
    first_occurrence = forms.DateField(label='زمان اولین رویداد',
                                       widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}))
    last_occurrence = forms.DateField(label='زمان آخرین رویداد (اختیاری)', required=False,
                                      widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}))

    class Meta:
        model = Event
        fields = ['category', 'name', 'repeat_interval', 'first_occurrence', 'last_occurrence', 'reminder_interval', 'is_active']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام رویداد'}),
            'repeat_interval': forms.Select(attrs={'class': 'form-control'}),
            'reminder_interval': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    # متد __init__ دیگر برای تبدیل تاریخ شمسی لازم نیست
    # اما اگر نیاز به تنظیمات اولیه دیگر دارید، می‌توانید آن را نگه دارید.
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)


# -----------------------------------------------------------
# 3. فرم برای EventDetail
# -----------------------------------------------------------
class EventDetailForm(forms.ModelForm):
    occurrence_date = forms.DateField(label='تاریخ برگزاری',
                                      widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}))

    class Meta:
        model = EventDetail
        fields = ['event', 'occurrence_date', 'status_relative_to_schedule', 'report']
        widgets = {
            'event': forms.Select(attrs={'class': 'form-control'}),
            'status_relative_to_schedule': forms.Select(attrs={'class': 'form-control'}),
            'report': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'گزارش برگزاری رویداد'}),
        }
    # متد __init__ دیگر برای تبدیل تاریخ شمسی لازم نیست
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)


# -----------------------------------------------------------
# 4. فرم برای Resolution
# -----------------------------------------------------------
class ResolutionForm(forms.ModelForm):
    due_date = forms.DateField(label='مهلت انجام', required=False,
                               widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}))
    completed_date = forms.DateField(label='تاریخ انجام', required=False,
                                     widget=forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}))

    class Meta:
        model = Resolution
        fields = ['text', 'responsible_person', 'status', 'due_date', 'completed_date']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'متن مصوبه'}),
            'responsible_person': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    # متد __init__ دیگر برای تبدیل تاریخ شمسی لازم نیست
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)


# -----------------------------------------------------------
# 5. فرم برای EventImage
# -----------------------------------------------------------
class EventImageForm(forms.ModelForm):
    class Meta:
        model = EventImage
        fields = ['image', 'caption']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'caption': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'توضیح تصویر (اختیاری)'}),
        }

# -----------------------------------------------------------
# Formsets برای EventDetail
# -----------------------------------------------------------
ResolutionFormSet = inlineformset_factory(
    EventDetail, Resolution, form=ResolutionForm, extra=1, can_delete=True
)
EventImageFormSet = inlineformset_factory(
    EventDetail, EventImage, form=EventImageForm, extra=1, can_delete=True
)
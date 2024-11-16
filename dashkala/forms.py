from django import forms

from mahakupdate.models import Kala, Storagek, Category


class FilterForm(forms.Form):
    kala = forms.ModelChoiceField(queryset=Kala.objects.all(), required=False, label='کالا')
    storage = forms.ModelChoiceField(queryset=Storagek.objects.all(), required=False, label='انبار')
    category = forms.ModelChoiceField(queryset=Category.objects.filter(level=3), required=False, label='دسته‌بندی')  # فقط سطح 3
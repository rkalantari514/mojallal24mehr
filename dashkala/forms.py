from django import forms
from django.forms import ModelChoiceField, ModelMultipleChoiceField

from mahakupdate.models import Kala, Storagek, Category


class FilterForm(forms.Form):
    kala = forms.ModelChoiceField(queryset=Kala.objects.all(), required=False, label='کالا')
    storage = forms.ModelChoiceField(queryset=Storagek.objects.all(), required=False, label='انبار')
    category = forms.ModelChoiceField(queryset=Category.objects.filter(level=3), required=False, label='دسته‌بندی')  # فقط سطح 3


class KalaSelectForm(forms.Form):
    storage = ModelChoiceField(
        widget=forms.Select(attrs={'placeholder': 'نام انبار', 'class': 'selectpicker', 'data-live-search': "true"}),
        queryset=Storagek.objects.all(),
        label='نام انبار',
        required=False,
        empty_label='همه انبارها',
    )

    category1 = ModelChoiceField(
        widget=forms.Select(
            attrs={'placeholder': 'دسته بندی سطح 1', 'class': 'selectpicker', 'data-live-search': "true",
                   'id': 'id_category1'}),
        queryset=Category.objects.filter(level=1),
        label='دسته بندی سطح 1',
        required=False,
        empty_label='همه',
    )

    category2 = ModelChoiceField(
        widget=forms.Select(
            attrs={'placeholder': 'دسته بندی سطح 2', 'class': 'selectpicker', 'data-live-search': "true",
                   'id': 'id_category2'}),
        queryset=Category.objects.filter(level=2),
        label='دسته بندی سطح 2',
        required=False,
        empty_label='همه',
    )

    category3 = ModelChoiceField(
        widget=forms.Select(
            attrs={'placeholder': 'دسته بندی سطح 3', 'class': 'selectpicker', 'data-live-search': "true",
                   'id': 'id_category3'}),
        queryset=Category.objects.filter(level=3),
        label='دسته بندی سطح 3',
        required=False,
        empty_label='همه',
    )




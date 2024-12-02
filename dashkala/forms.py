from django import forms
from django.forms import ModelChoiceField, ModelMultipleChoiceField, TextInput
from mahakupdate.models import Kala, Storagek, Category
from persianutils import standardize


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


def fix_persian_characters(value):
    return standardize(value)

class KModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return fix_persian_characters(obj.name)

class Kala_Detail_Form(forms.Form):
    kala = KModelChoiceField(
        widget=forms.Select(attrs={'placeholder': 'کالا', 'class': 'selectpicker', 'data-live-search': "true"}),
        queryset=Kala.objects.all(),
        label='نام کالا',
        required=False,
        # empty_label='------',
    )

    code_kala = forms.IntegerField(
        widget=forms.TextInput(attrs={'placeholder': 'کد کالا', 'class': 'form-control' }),
        label='کد کالا',
        required=False,
    )


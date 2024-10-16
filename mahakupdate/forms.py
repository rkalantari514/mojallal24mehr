from django import forms
from .models import Category, Kala

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'parent', 'level']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.parent:
            self.fields['parent'].queryset = Category.objects.filter(parent=self.instance.parent.parent)
        else:
            self.fields['parent'].queryset = Category.objects.filter(level=1)

class KalaForm(forms.ModelForm):
    class Meta:
        model = Kala
        fields = ['code', 'name', 'category']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.category:
            self.fields['category'].queryset = Category.objects.filter(parent=self.instance.category.parent)
        else:
            self.fields['category'].queryset = Category.objects.filter(level=1)

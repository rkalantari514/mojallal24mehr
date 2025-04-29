from django.contrib import admin
from .models import CustomUser, UserLog


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('mobile_number', 'first_name', 'last_name', 'is_active', 'is_admin','password_expiry_date','is_dark_mode')  # اضافه کردن فیلدهای جدید
    list_filter = ('is_admin', 'is_active')
    search_fields = ('mobile_number', 'first_name', 'last_name')  # جستجو در فیلدهای جدید



class UserLogAdmin(admin.ModelAdmin):
    list_display = ['user','__str__','time','page','code']

    class Meta:
        model = UserLog

from django.contrib import admin
from django.forms import CheckboxSelectMultiple
from .models import MyPage

@admin.register(MyPage)
class MyPageAdmin(admin.ModelAdmin):
    list_display = ('name', 'v_name', 'p_url')  # ستون‌های نمایش
    search_fields = ('name', 'v_name')  # قابلیت جستجو
    filter_horizontal = ('allowed_groups',)  # حذف این خط چون از فرم چک‌باکس استفاده می‌کنیم

    formfield_overrides = {
        'allowed_groups': {'widget': CheckboxSelectMultiple},  # تغییر به چک‌باکس
    }




admin.site.register(UserLog, UserLogAdmin)

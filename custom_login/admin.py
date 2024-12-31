from django.contrib import admin
from .models import CustomUser, UserLog


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('mobile_number', 'first_name', 'last_name', 'is_active', 'is_admin','password_expiry_date')  # اضافه کردن فیلدهای جدید
    list_filter = ('is_admin', 'is_active')
    search_fields = ('mobile_number', 'first_name', 'last_name')  # جستجو در فیلدهای جدید



class UserLogAdmin(admin.ModelAdmin):
    list_display = ['user','__str__','time','page','code']

    class Meta:
        model = UserLog



admin.site.register(UserLog, UserLogAdmin)

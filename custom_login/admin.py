from django.contrib import admin
from .models import CustomUser, UserLog, CustomGroup


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
    # filter_horizontal = ('allowed_groups',)  # حذف این خط چون از فرم چک‌باکس استفاده می‌کنیم

    # formfield_overrides = {
    #     'allowed_groups': {'widget': CheckboxSelectMultiple},  # تغییر به چک‌باکس
    # }





from django.contrib import admin
from django.contrib.auth.models import Group




from django.contrib import admin
from .models import CustomGroup

@admin.register(CustomGroup)
class CustomGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'persian_name', 'get_allowed_pages','default_page')

    def get_allowed_pages(self, obj):
        return ", ".join([page.name for page in obj.allowed_pages.all()])
    get_allowed_pages.short_description = 'صفحات مجاز'

    filter_horizontal = ('allowed_pages',)  # استفاده از چک‌باکس برای انتخاب صفحات







admin.site.register(UserLog, UserLogAdmin)
admin.site.unregister(Group)
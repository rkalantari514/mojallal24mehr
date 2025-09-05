from django.contrib import admin
from .models import CustomUser, UserLog, CustomGroup


# @admin.register(CustomUser)
# class CustomUserAdmin(admin.ModelAdmin):
#     list_display = ('mobile_number', 'first_name', 'last_name', 'is_active', 'is_admin','password_expiry_date','is_dark_mode')  # اضافه کردن فیلدهای جدید
#     list_filter = ('is_admin', 'is_active')
#     search_fields = ('mobile_number', 'first_name', 'last_name')  # جستجو در فیلدهای جدید
#


# class UserLogAdmin(admin.ModelAdmin):
#     list_display = ['user','__str__','time','page','code']
#
#     class Meta:
#         model = UserLog

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



# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
from .models import UserLog
from django.contrib.auth import get_user_model

CustomUser = get_user_model()


# فیلترهای زمانی سفارشی
class TimeFilter(admin.SimpleListFilter):
    title = 'زمان بازدید'
    parameter_name = 'time'

    def lookups(self, request, model_admin):
        return [
            ('today', 'امروز'),
            ('yesterday', 'دیروز'),
            ('this_week', 'این هفته'),
            ('last_week', 'هفته گذشته'),
            ('this_month', 'این ماه'),
            ('last_month', 'ماه گذشته'),
            ('this_year', 'این سال'),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'today':
            return queryset.filter(time__date=now.date())
        elif self.value() == 'yesterday':
            return queryset.filter(time__date=now.date() - timedelta(days=1))
        elif self.value() == 'this_week':
            start = now - timedelta(days=now.weekday())
            return queryset.filter(time__date__gte=start.date())
        elif self.value() == 'last_week':
            start = now - timedelta(days=now.weekday() + 7)
            end = start + timedelta(days=6)
            return queryset.filter(time__date__range=[start.date(), end.date()])
        elif self.value() == 'this_month':
            return queryset.filter(time__year=now.year, time__month=now.month)
        elif self.value() == 'last_month':
            month = now.month - 1 if now.month > 1 else 12
            year = now.year if now.month > 1 else now.year - 1
            return queryset.filter(time__year=year, time__month=month)
        elif self.value() == 'this_year':
            return queryset.filter(time__year=now.year)
        return queryset


# Admin برای UserLog
@admin.register(UserLog)
class UserLogAdmin(admin.ModelAdmin):
    # نمایش ستون‌ها در لیست
    list_display = (
        'get_user_full_name',
        'get_user_avatar',
        'page',
        'code',
        'time',
    )

    # امکان جستجو بر اساس نام کاربر، صفحه و کد
    search_fields = (
        'user__first_name',
        'user__last_name',
        'user__mobile_number',
        'page',
        'code',
    )

    # فیلترهای سمت راست
    list_filter = (
        'user',
        TimeFilter,
        'page',
    )

    # مرتب‌سازی پیش‌فرض
    ordering = ('-time',)

    # فقط خواندنی (اختیاری)
    readonly_fields = ('user', 'page', 'code', 'time')

    # تابع برای نمایش نام کامل کاربر
    @admin.display(description='نام کاربر')
    def get_user_full_name(self, obj):
        user = obj.user
        if user:
            full_name = f"{user.first_name} {user.last_name}".strip()
            return full_name if full_name else "نامشخص"
        return "کاربر حذف شده"

    # تابع برای نمایش تصویر پروفایل
    @admin.display(description='عکس پروفایل')
    def get_user_avatar(self, obj):
        user = obj.user
        if user and user.avatar:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />',
                user.avatar.url
            )
        return format_html(
            '<div style="width: 40px; height: 40px; border-radius: 50%; background: #ccc; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 12px;">{}</div>',
            (obj.user.first_name[0] + obj.user.last_name[0]).upper() if obj.user else "?"
        )

    # بهینه‌سازی کوئری برای جلوگیری از N+1
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')  # بهینه‌سازی برای دسترسی به user و avatar


# اختیاری: اگر می‌خواهید کاربران هم در ادمین دیده شوند
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'mobile_number', 'is_active', 'is_admin', 'get_avatar_preview')
    list_filter = ('is_active', 'is_admin', 'is_dark_mode')
    search_fields = ('first_name', 'last_name', 'mobile_number')
    readonly_fields = ('password',)  # امنیتی

    @admin.display(description='نام')
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or "نامشخص"

    @admin.display(description='عکس')
    def get_avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 30px; height: 30px; border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url
            )
        return "—"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()



# admin.site.register(UserLog, UserLogAdmin)
admin.site.unregister(Group)
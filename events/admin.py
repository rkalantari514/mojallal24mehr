# events/admin.py

from django.contrib import admin
from .models import EventCategory, Event, EventDetail, Resolution, EventImage

# -----------------------------------------------------------
# Inline برای Resolution و EventImage
# اینها اجازه می دهند که مصوبات و تصاویر را مستقیماً از صفحه جزئیات رویداد (EventDetail) مدیریت کنید.
# -----------------------------------------------------------
class ResolutionInline(admin.TabularInline): # یا admin.StackedInline
    model = Resolution
    extra = 1 # تعداد فرم های خالی برای افزودن مصوبه جدید
    fields = ['text', 'responsible_person', 'status', 'due_date', 'completed_date']
    # اگر CustomUser را در admin.py دیگر ثبت نکرده‌اید، ممکن است لازم باشد آن را هم register کنید.
    # یا مطمئن شوید که فیلد responsible_person در admin برای شما قابل نمایش و انتخاب است.
    autocomplete_fields = ['responsible_person'] # برای فیلد فارنکی به CustomUser

class EventImageInline(admin.TabularInline): # یا admin.StackedInline
    model = EventImage
    extra = 1
    fields = ['image', 'caption'] # فیلدهای مربوط به تصویر

# -----------------------------------------------------------
# 1. ادمین برای EventCategory
# -----------------------------------------------------------
@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    list_filter = ('name',)

# -----------------------------------------------------------
# 2. ادمین برای Event
# -----------------------------------------------------------
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'repeat_interval', 'first_occurrence', 'last_occurrence', 'is_active')
    list_filter = ('category', 'repeat_interval', 'is_active')
    search_fields = ('name', 'description')
    date_hierarchy = 'first_occurrence' # امکان فیلتر بر اساس سال/ماه/روز برای اولین رویداد
    # fieldsets: برای سازماندهی بهتر فیلدها در صفحه ادمین
    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'is_active')
        }),
        ('زمان بندی', {
            'fields': ('repeat_interval', 'first_occurrence', 'last_occurrence', 'reminder_interval'),
            'classes': ('collapse',) # این قسمت را می توان جمع کرد
        }),
    )

# -----------------------------------------------------------
# 3. ادمین برای EventDetail
# -----------------------------------------------------------
@admin.register(EventDetail)
class EventDetailAdmin(admin.ModelAdmin):
    list_display = ('event', 'occurrence_date', 'status_relative_to_schedule', 'report_snippet')
    list_filter = ('event__category', 'event', 'status_relative_to_schedule', 'occurrence_date')
    search_fields = ('event__name', 'report')
    date_hierarchy = 'occurrence_date'
    inlines = [ResolutionInline, EventImageInline] # افزودن Inlines به EventDetail

    # برای نمایش بخشی از گزارش در لیست
    def report_snippet(self, obj):
        return obj.report[:50] + '...' if len(obj.report) > 50 else obj.report
    report_snippet.short_description = 'خلاصه گزارش'

# -----------------------------------------------------------
# 4. ادمین برای Resolution
# (اگر می خواهید این مدل به صورت جداگانه در ادمین قابل دسترسی باشد، علاوه بر Inline)
# -----------------------------------------------------------
@admin.register(Resolution)
class ResolutionAdmin(admin.ModelAdmin):
    list_display = ('text_snippet', 'event_detail', 'responsible_person', 'status', 'due_date', 'completed_date')
    list_filter = ('status', 'responsible_person', 'due_date')
    search_fields = ('text', 'event_detail__event__name', 'responsible_person__username')
    date_hierarchy = 'due_date'
    autocomplete_fields = ['responsible_person', 'event_detail'] # فعال کردن جستجوی خودکار برای فارنکی ها

    def text_snippet(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_snippet.short_description = 'متن مصوبه'


# -----------------------------------------------------------
# 5. ادمین برای EventImage
# (اگر می خواهید این مدل به صورت جداگانه در ادمین قابل دسترسی باشد، علاوه بر Inline)
# -----------------------------------------------------------
@admin.register(EventImage)
class EventImageAdmin(admin.ModelAdmin):
    list_display = ('event_detail', 'image_tag', 'caption', 'uploaded_at')
    list_filter = ('uploaded_at', 'event_detail__event__name')
    search_fields = ('caption', 'event_detail__report')
    readonly_fields = ('uploaded_at', 'image_tag') # تاریخ آپلود فقط خواندنی باشد
    autocomplete_fields = ['event_detail']

    # برای نمایش تصویر کوچک در لیست ادمین
    from django.utils.html import mark_safe
    def image_tag(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="width: 100px; height: auto;" />')
        return "بدون تصویر"
    image_tag.short_description = 'تصویر'
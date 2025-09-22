# events/admin.py
from django.contrib import admin
from django.utils.safestring import mark_safe
import jdatetime  # برای تبدیل تاریخ میلادی به شمسی
from .models import EventCategory, Event, EventDetail, Resolution, EventImage, Reminder

# -----------------------------------------------------------
# تابع کمکی برای تبدیل تاریخ میلادی به شمسی (فقط تاریخ)
# -----------------------------------------------------------
def to_jalali(date_obj):
    if date_obj:
        j_date = jdatetime.date.fromgregorian(date=date_obj)
        return j_date.strftime('%Y/%m/%d')
    return '-'

# -----------------------------------------------------------
# Inline برای Resolution و EventImage
# -----------------------------------------------------------
class ResolutionInline(admin.TabularInline):
    model = Resolution
    extra = 1
    fields = ['text', 'responsible_person', 'status', 'due_date', 'completed_date']
    autocomplete_fields = ['responsible_person']

    # نمایش تاریخ شمسی در inline
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # اینجا فقط برای نمایش در لیست اصلی تاریخ‌ها را شمسی می‌کنیم، در فرم ویرایش همچنان میلادی است
        # ولی اگر بخواهید در فرم inline هم شمسی باشد، باید widget را تغییر دهید (که معمولاً در فرم‌ها انجام می‌شود)
        return formset

class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 1
    fields = ['image', 'caption']

# -----------------------------------------------------------
# 1. ادمین برای EventCategory (تاریخی ندارد)
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
    list_display = ('name', 'category', 'repeat_interval', 'first_occurrence_jalali', 'last_occurrence_jalali', 'is_active')
    list_filter = ('category', 'repeat_interval', 'is_active')
    search_fields = ('name', 'description')
    date_hierarchy = 'first_occurrence'

    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'is_active')
        }),
        ('زمان بندی', {
            'fields': ('repeat_interval', 'first_occurrence', 'last_occurrence', 'reminder_interval'),
            'classes': ('collapse',)
        }),
    )

    # متد برای نمایش تاریخ شمسی first_occurrence
    def first_occurrence_jalali(self, obj):
        return to_jalali(obj.first_occurrence)
    first_occurrence_jalali.short_description = 'اولین رویداد (شمسی)'
    first_occurrence_jalali.admin_order_field = 'first_occurrence'

    # متد برای نمایش تاریخ شمسی last_occurrence
    def last_occurrence_jalali(self, obj):
        return to_jalali(obj.last_occurrence)
    last_occurrence_jalali.short_description = 'آخرین رویداد (شمسی)'
    last_occurrence_jalali.admin_order_field = 'last_occurrence'

# -----------------------------------------------------------
# 3. ادمین برای EventDetail
# -----------------------------------------------------------
@admin.register(EventDetail)
class EventDetailAdmin(admin.ModelAdmin):
    list_display = ('event', 'occurrence_date_jalali', 'status_relative_to_schedule', 'report_snippet')
    list_filter = ('event__category', 'event', 'status_relative_to_schedule', 'occurrence_date')
    search_fields = ('event__name', 'report')
    date_hierarchy = 'occurrence_date'
    inlines = [ResolutionInline, EventImageInline]

    def report_snippet(self, obj):
        try:
            return obj.report[:50] + '...' if len(obj.report) > 50 else obj.report
        except:
            return '-'
    report_snippet.short_description = 'خلاصه گزارش'

    # متد برای نمایش تاریخ شمسی occurrence_date
    def occurrence_date_jalali(self, obj):
        return to_jalali(obj.occurrence_date)
    occurrence_date_jalali.short_description = 'تاریخ برگزاری (شمسی)'
    occurrence_date_jalali.admin_order_field = 'occurrence_date'

# -----------------------------------------------------------
# 4. ادمین برای Resolution
# -----------------------------------------------------------
@admin.register(Resolution)
class ResolutionAdmin(admin.ModelAdmin):
    list_display = ('text_snippet', 'event_detail', 'responsible_person', 'status', 'due_date_jalali', 'completed_date_jalali')
    list_filter = ('status', 'responsible_person', 'due_date')
    search_fields = ('text', 'event_detail__event__name', 'responsible_person__username')
    date_hierarchy = 'due_date'
    autocomplete_fields = ['responsible_person', 'event_detail']

    def text_snippet(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_snippet.short_description = 'متن مصوبه'

    # متد برای نمایش تاریخ شمسی due_date
    def due_date_jalali(self, obj):
        return to_jalali(obj.due_date)
    due_date_jalali.short_description = 'مهلت انجام (شمسی)'
    due_date_jalali.admin_order_field = 'due_date'

    # متد برای نمایش تاریخ شمسی completed_date
    def completed_date_jalali(self, obj):
        return to_jalali(obj.completed_date)
    completed_date_jalali.short_description = 'تاریخ انجام (شمسی)'
    completed_date_jalali.admin_order_field = 'completed_date'

# -----------------------------------------------------------
# 5. ادمین برای EventImage
# -----------------------------------------------------------
@admin.register(EventImage)
class EventImageAdmin(admin.ModelAdmin):
    list_display = ('event_detail', 'image_tag', 'caption', 'uploaded_at_jalali')
    list_filter = ('uploaded_at', 'event_detail__event__name')
    search_fields = ('caption', 'event_detail__report')
    readonly_fields = ('uploaded_at_jalali_display', 'image_tag')
    autocomplete_fields = ['event_detail']

    def image_tag(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="width: 100px; height: auto;" />')
        return "بدون تصویر"
    image_tag.short_description = 'تصویر'

    # متد برای نمایش تاریخ شمسی uploaded_at در لیست
    def uploaded_at_jalali(self, obj):
        if obj.uploaded_at:
            j_datetime = jdatetime.datetime.fromgregorian(datetime=obj.uploaded_at)
            return j_datetime.strftime('%Y/%m/%d %H:%M')
        return '-'
    uploaded_at_jalali.short_description = 'تاریخ آپلود (شمسی)'
    uploaded_at_jalali.admin_order_field = 'uploaded_at'

    # متد برای نمایش تاریخ شمسی uploaded_at در صفحه ویرایش (فقط خواندنی)
    def uploaded_at_jalali_display(self, obj):
        return self.uploaded_at_jalali(obj)
    uploaded_at_jalali_display.short_description = 'تاریخ آپلود (شمسی)'

# -----------------------------------------------------------
# 6. ادمین برای Reminder
# -----------------------------------------------------------
@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = [
        'content_object',
        'reminder_type',
        'scheduled_send_date_jalali',
        'is_sent',
        'sent_at_jalali',
        'created_at_jalali',
    ]

    list_filter = [
        'reminder_type',
        'is_sent',
        'scheduled_send_date',
    ]

    search_fields = [
        'content_type__model',
    ]

    readonly_fields = [
        'created_at_jalali_display',
        'sent_at_jalali_display',
        'content_object',
    ]

    fieldsets = (
        ('اطلاعات مربوط به شیء', {
            'fields': ('content_type', 'object_id', 'content_object')
        }),
        ('جزئیات یادآور', {
            'fields': ('reminder_type', 'scheduled_send_date', 'is_sent', 'sent_at_jalali_display')
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_at_jalali_display',),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ['content_type', 'object_id']
        return self.readonly_fields

    def content_object(self, obj):
        return str(obj.content_object)
    content_object.short_description = 'شیء مرتبط'
    content_object.admin_order_field = 'object_id'

    # --- متدهای تاریخ شمسی برای Reminder ---
    def scheduled_send_date_jalali(self, obj):
        return to_jalali(obj.scheduled_send_date)
    scheduled_send_date_jalali.short_description = 'تاریخ ارسال برنامه‌ریزی شده (شمسی)'
    scheduled_send_date_jalali.admin_order_field = 'scheduled_send_date'

    def sent_at_jalali(self, obj):
        if obj.sent_at:
            j_datetime = jdatetime.datetime.fromgregorian(datetime=obj.sent_at)
            return j_datetime.strftime('%Y/%m/%d %H:%M')
        return '-'
    sent_at_jalali.short_description = 'تاریخ ارسال واقعی (شمسی)'
    sent_at_jalali.admin_order_field = 'sent_at'

    def created_at_jalali(self, obj):
        if obj.created_at:
            j_datetime = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
            return j_datetime.strftime('%Y/%m/%d %H:%M')
        return '-'
    created_at_jalali.short_description = 'تاریخ ایجاد رکورد (شمسی)'
    created_at_jalali.admin_order_field = 'created_at'

    # --- متدهای نمایش در صفحه ویرایش (فقط خواندنی) ---
    def sent_at_jalali_display(self, obj):
        return self.sent_at_jalali(obj)
    sent_at_jalali_display.short_description = 'تاریخ ارسال واقعی (شمسی)'

    def created_at_jalali_display(self, obj):
        return self.created_at_jalali(obj)
    created_at_jalali_display.short_description = 'تاریخ ایجاد رکورد (شمسی)'
# events/models.py

from django.db import models
from django.utils import timezone # برای فیلدهای تاریخ و زمان

from custom_login.models import CustomUser


# -----------------------------------------------------------
# 1. مدل انواع رویدادها (EventCategory)
# -----------------------------------------------------------
class EventCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='نام دسته بندی رویداد')
    description = models.TextField(blank=True, verbose_name='توضیحات دسته بندی')

    class Meta:
        verbose_name = 'دسته بندی رویداد'
        verbose_name_plural = 'دسته بندی های رویداد'

    def __str__(self):
        return self.name

# -----------------------------------------------------------
# 2. مدل رویداد (Event)
# -----------------------------------------------------------
class Event(models.Model):
    # بازه های تکرار
    # برای مثال: weekly, monthly, quarterly, semi_annually, annually
    REPEAT_INTERVAL_CHOICES = [
        ('none', 'بدون تکرار'),
        ('daily', 'روزانه'),
        ('weekly', 'هفتگی'),
        ('biweekly', 'دو هفته یکبار'), # Added biweekly for more options
        ('monthly', 'ماهانه'),
        ('quarterly', 'فصلی'),
        ('semi_annually', 'شش ماهه'), # Semi-annually (دو بار در سال)
        ('annually', 'سالانه'),
    ]

    # فاصله زمانی یادآور
    # مثال: 0 روز قبل، 1 روز قبل، 3 روز قبل، 7 روز قبل
    REMINDER_INTERVAL_CHOICES = [
        (0, 'همان روز'),
        (1, 'یک روز قبل'),
        (3, 'سه روز قبل'),
        (7, 'یک هفته قبل'),
        (15, 'دو هفته قبل'),
        (30, 'یک ماه قبل'),
        (90, 'سه ماه قبل'),
        (180, 'شش ماه قبل'),
        (365, 'یک سال قبل'),
    ]

    category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='events', verbose_name='دسته بندی رویداد')
    name = models.CharField(max_length=200, verbose_name='نام رویداد')
    repeat_interval = models.CharField(max_length=20, choices=REPEAT_INTERVAL_CHOICES,
                                       default='none', verbose_name='بازه تکرار')
    first_occurrence = models.DateField(verbose_name='زمان اولین رویداد')
    last_occurrence = models.DateField(blank=True, null=True, verbose_name='زمان آخرین رویداد (اختیاری)')
    reminder_interval = models.IntegerField(choices=REMINDER_INTERVAL_CHOICES, default=0,
                                            verbose_name='فاصله زمانی یادآور (به روز قبل)')
    is_active = models.BooleanField(default=True, verbose_name='فعال است؟')

    class Meta:
        verbose_name = 'رویداد'
        verbose_name_plural = 'رویدادها'
        ordering = ['first_occurrence', 'name'] # مرتب سازی بر اساس تاریخ و نام

    def __str__(self):
        return f'{self.name} ({self.category.name if self.category else "بدون دسته بندی"})'

# -----------------------------------------------------------
# 3. مدل مصوبات (Resolution)
# (ابتدا این را تعریف می‌کنیم چون EventDetail به آن فارنکی دارد)
# -----------------------------------------------------------
class Resolution(models.Model):
    STATUS_CHOICES = [
        ('pending', 'انجام نشده'),
        ('completed', 'انجام شده'),
        ('cancelled', 'منتفی'),
    ]

    event_detail = models.ForeignKey('EventDetail', on_delete=models.CASCADE, related_name='resolutions', verbose_name='جزء رویداد مربوطه')
    text = models.TextField(verbose_name='متن مصوبه')
    responsible_person = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='resolutions', verbose_name='مسئول اجرا')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name='وضعیت انجام')
    due_date = models.DateField(blank=True, null=True, verbose_name='مهلت انجام (تاریخ)')
    completed_date = models.DateField(blank=True, null=True, verbose_name='تاریخ انجام')

    class Meta:
        verbose_name = 'مصوبه'
        verbose_name_plural = 'مصوبات'
        ordering = ['due_date', 'status']

    def __str__(self):
        return f'مصوبه: {self.text[:50]}... ({self.get_status_display()})'

# -----------------------------------------------------------
# 4. مدل جزئیات رویداد (EventDetail)
# -----------------------------------------------------------
class EventDetail(models.Model):
    STATUS_CHOICES = [
        ('not_held', 'برگزار نشده'),
        ('on_time', 'به موقع'),
        ('early', 'تعجیل'),
        ('late', 'تاخیر'),
    ]

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE,
        related_name='details', verbose_name='رویداد'
    )

    # تاریخ برنامه‌ای
    scheduled_date = models.DateField(
        verbose_name='تاریخ برنامه‌ای', null=True, blank=True, default=None
    )

    # تاریخ واقعی برگزاری (وقتی اتفاق افتاد)
    occurrence_date = models.DateField(
        verbose_name='تاریخ واقعی برگزاری', null=True, blank=True, default=None
    )

    # وضعیت (بر اساس occurrence_date در مقایسه با scheduled_date)
    status_relative_to_schedule = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='not_held',
        verbose_name='وضعیت برگزاری'
    )

    # شماره جزئیات (برای هر event از 1 شروع می‌شود)
    sequence_number = models.PositiveIntegerField(
        null=True, blank=True, default=None,
        verbose_name='شماره جزئیات'
    )

    report = models.TextField(
        blank=True, null=True, default=None,
        verbose_name='گزارش برگزاری'
    )

    class Meta:
        verbose_name = 'جزئیات رویداد'
        verbose_name_plural = 'جزئیات رویدادها'
        ordering = ['scheduled_date']
        unique_together = ('event', 'sequence_number')  # یک شماره یکتا در هر event

    def __str__(self):
        return f'{self.event.name} - نوبت {self.sequence_number} ({self.scheduled_date})'

    def save(self, *args, **kwargs):
        # اگر occurrence_date پر شد، وضعیت را محاسبه کن
        if self.occurrence_date and self.scheduled_date:
            if self.occurrence_date < self.scheduled_date:
                self.status_relative_to_schedule = 'early'
            elif self.occurrence_date > self.scheduled_date:
                self.status_relative_to_schedule = 'late'
            else:
                self.status_relative_to_schedule = 'on_time'
        elif not self.occurrence_date:
            self.status_relative_to_schedule = 'not_held'

        super().save(*args, **kwargs)


# -----------------------------------------------------------
# 5. مدل تصاویر (EventImage)
# -----------------------------------------------------------
def event_image_upload_path(instance, filename):
    # فایل های تصاویر را در مسیری سازماندهی شده ذخیره می کند
    return f'event_images/{instance.event_detail.event.name}/{instance.event_detail.occurrence_date}/{filename}'

class EventImage(models.Model):
    event_detail = models.ForeignKey(EventDetail, on_delete=models.CASCADE, related_name='images', verbose_name='جزء رویداد')
    image = models.ImageField(upload_to=event_image_upload_path, verbose_name='تصویر')
    caption = models.CharField(max_length=200, blank=True, verbose_name='توضیح تصویر')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ آپلود')

    class Meta:
        verbose_name = 'تصویر رویداد'
        verbose_name_plural = 'تصاویر رویداد'

    def __str__(self):
        return f'تصویر برای {self.event_detail}'
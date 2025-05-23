from django.db import models

from accounting.models import BedehiMoshtari
from django.db import models
from django.conf import settings
from datetime import datetime

# Create your models here.



class TrackKinde(models.Model):
    kind_name = models.CharField(blank=True, null=True,max_length=150, verbose_name='نوع پیگیری')
    kind_icon = models.CharField(blank=True, null=True,max_length=150, verbose_name='آیکون نوع پیگیری')
    kind_color = models.CharField(blank=True, null=True,max_length=150, verbose_name='رنگ نوع پیگیری')
    is_call_related = models.BooleanField(default=False, verbose_name="مربوط به تماس تلفنی")
    call_statuses = models.JSONField(blank=True, null=True, verbose_name="وضعیت‌های ممکن تماس")

    class Meta:
        verbose_name = 'نوع پیگیری'
        verbose_name_plural = 'انواع پیگیری'

    def __str__(self):
        return self.kind_name

class SampleSMS(models.Model):
    level = models.CharField(blank=True, null=True,max_length=50, verbose_name="سطح پیامک")  # فیلد جدید برای سطح پیامک
    text = models.TextField(blank=True, null=True,verbose_name="متن پیامک")
    is_active = models.BooleanField(default=True, verbose_name='فعال است')


    class Meta:
        verbose_name = "پیامک نمونه"
        verbose_name_plural = "پیامک‌های نمونه"

    def __str__(self):
        return f"{self.level} : {self.text[:150]} "  # نمایش متن پیامک و سطح آن



STATUS_DETAILS = {
    2: {"status": "Delivered ✅", "persian": "رسیده به گوشی", "color": "text-success", "icon": "fa-check"},
    4: {"status": "Discarded ❌", "persian": "رد شد", "color": "text-danger", "icon": "fa-times"},
    1: {"status": "Pending ⏳", "persian": "در انتظار ارسال", "color": "text-warning", "icon": "fa-clock"},
    3: {"status": "Failed ❌", "persian": "ناموفق", "color": "text-danger", "icon": "fa-exclamation-triangle"},
    0: {"status": "Sent 🚀", "persian": "ارسال شد", "color": "text-info", "icon": "fa-paper-plane"}
}

CALL_STATUS = {
    2: {"status": "Successful Call ✅", "persian": " تماس موفق", "color": "text-primary", "icon": "fa-check"},
    1: {"status": "No Answer ⏳", "persian": "عدم پاسخگویی", "color": "text-warning", "icon": "fa-clock"},
    0: {"status": "Wrong Number ❌", "persian": "شماره اشتباه", "color": "text-danger", "icon": "fa-times"},
    4: {"status": "Reminder ⏳", "persian": "صرفاً یادآوری", "color": "text-warning", "icon": "fa-clock"},}




class Tracking(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ و ساعت انجام")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="ایجاد کننده",
        null=True,
        blank=True
    )
    customer = models.ForeignKey(BedehiMoshtari, on_delete=models.CASCADE, verbose_name="مشتری")
    track_kind = models.ForeignKey(TrackKinde, on_delete=models.CASCADE, verbose_name="نوع پیگیری")
    next_reminder_date = models.DateField(blank=True, null=True, verbose_name="زمان یادآور پیگیری بعدی")
    message = models.TextField(blank=True, null=True, verbose_name="پیام تکمیلی")
    message_to_send = models.TextField(blank=True, null=True, verbose_name="متن پیام ارسالی")
    call_duration = models.IntegerField(blank=True, null=True, verbose_name="مدت زمان تماس تلفنی (ثانیه)")
    phone_number = models.CharField(blank=True, null=True,max_length=150, verbose_name="شماره تلفن")
    sample_sms = models.ForeignKey(
        SampleSMS,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="پیامک نمونه"
    )
    message_id = models.CharField(blank=True, null=True, max_length=50, verbose_name="شناسه پیامک")
    status_code = models.IntegerField(blank=True, null=True, verbose_name="کد وضعیت پیامک")

    call_status = models.IntegerField(
        blank=True,
        null=True,
        choices=[(key, value["persian"]) for key, value in CALL_STATUS.items()],
        verbose_name="وضعیت تماس"
    )
    call_description = models.TextField(blank=True, null=True, verbose_name="شرح تماس")



    class Meta:
        verbose_name = "پیگیری"
        verbose_name_plural = "پیگیری‌ها"

    def __str__(self):
        return f"{self.customer} - {self.track_kind} ({self.created_at})"

    def get_status_details(self):
        return STATUS_DETAILS.get(self.status_code,
                                  {"status": "Unknown", "persian": "نامشخص", "color": "text-secondary",
                                   "icon": "fa-question"})

    def get_call_status_details(self):
        return CALL_STATUS.get(self.call_status,
                               {"status": "Unknown", "persian": "نامشخص", "color": "text-secondary", "icon": "fa-question"})



    def reminder_status(self):
        from django.utils import timezone
        today = timezone.now().date()
        if self.next_reminder_date:
            if self.next_reminder_date < today:
                return False
            else:
                return True
        return False
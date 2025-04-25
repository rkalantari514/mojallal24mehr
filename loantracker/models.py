from django.db import models

from accounting.models import BedehiMoshtari


# Create your models here.



class TrackKinde(models.Model):
    kind_name = models.CharField(blank=True, null=True,max_length=150, verbose_name='نوع پیگیری')
    kind_icon = models.CharField(blank=True, null=True,max_length=150, verbose_name='آیکون نوع پیگیری')
    kind_color = models.CharField(blank=True, null=True,max_length=150, verbose_name='رنگ نوع پیگیری')

    class Meta:
        verbose_name = 'نوع پیگیری'
        verbose_name_plural = 'انواع پیگیری'

    def __str__(self):
        return self.kind_name

class SampleSMS(models.Model):
    level = models.CharField(blank=True, null=True,max_length=50, verbose_name="سطح پیامک")  # فیلد جدید برای سطح پیامک
    text = models.TextField(blank=True, null=True,verbose_name="متن پیامک")

    class Meta:
        verbose_name = "پیامک نمونه"
        verbose_name_plural = "پیامک‌های نمونه"

    def __str__(self):
        return f"{self.level} : {self.text[:150]} "  # نمایش متن پیامک و سطح آن

from django.db import models
from django.conf import settings
from datetime import datetime

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
    message = models.TextField(blank=True, null=True, verbose_name="متن پیام ارسالی")
    call_duration = models.IntegerField(blank=True, null=True, verbose_name="مدت زمان تماس تلفنی (ثانیه)")
    phone_number = models.CharField(blank=True, null=True,max_length=150, verbose_name="شماره تلفن")
    sample_sms = models.ForeignKey(
        SampleSMS,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="پیامک نمونه"
    )
    class Meta:
        verbose_name = "پیگیری"
        verbose_name_plural = "پیگیری‌ها"

    def __str__(self):
        return f"{self.customer} - {self.track_kind} ({self.created_at})"


from django.db import models

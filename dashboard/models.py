import os

from django.db import models

# Create your models here.

def get_filename_ext(filepath):
    base_name = os.path.basename(filepath)
    name, ext = os.path.splitext(base_name)
    return name, ext

def upload_image_path(instance, filename):
    name, ext = get_filename_ext(filename)
    final_name = f"{instance.id}{ext}"
    return f"site/{final_name}"


class MasterInfo(models.Model):
    acc_year = models.IntegerField(blank=True, null=True,verbose_name='سال مالی')
    company_name= models.CharField(max_length=255, null=True,verbose_name='نام شرکت')
    company_logo1 = models.ImageField(upload_to=upload_image_path, null=True, blank=True, verbose_name='لوگوی اصلی')
    is_active = models.BooleanField(default=False, verbose_name='فعال است؟')
    last_report_time=models.DateTimeField(blank=True, null=True,verbose_name='زمان آخرین ارسال گزاش')





    class Meta:
        verbose_name = 'تنظیمات سایت'
        verbose_name_plural = 'انواع تنظیمات'

    def __str__(self):
        return str(self.acc_year)

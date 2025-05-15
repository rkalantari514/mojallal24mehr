# Create your models here.
from django.db import models
from django.db import models
from mahakupdate.models import Factor, Person  # فرض بر اینکه مدل Factor در اپلیکیشن 'mahakupdate' قرار دارد


class Festival(models.Model):
    name = models.CharField(max_length=255, verbose_name='نام جشنواره')
    start_date = models.DateField(verbose_name='تاریخ شروع')
    end_date = models.DateField(verbose_name='تاریخ پایان')
    min_invoice_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name='حداقل مبلغ فاکتور برای امتیاز')
    points_per_purchase_ratio = models.DecimalField(max_digits=15, decimal_places=0, default=1, verbose_name='ارزش هر چند ریال برای یک امتیاز')
    is_active = models.BooleanField(default=True, verbose_name='فعال')  # افزودن فیلد is_active

    class Meta:
        verbose_name = 'جشنواره'
        verbose_name_plural = 'جشنواره‌ها'

    def __str__(self):
        return self.name




class CustomerPoints(models.Model):
    festival = models.ForeignKey(Festival, on_delete=models.CASCADE, related_name='customer_points', verbose_name='جشنواره')
    customer = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='customer_points', verbose_name='مشتری')
    factor = models.ForeignKey(Factor, on_delete=models.CASCADE, related_name='customer_points', verbose_name='فاکتور')
    points_awarded = models.IntegerField(default=0, verbose_name='امتیاز تعلق گرفته')
    award_date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ تعلق')

    class Meta:
        verbose_name = 'امتیاز مشتری'
        verbose_name_plural = 'امتیازات مشتریان'
        unique_together = ('festival', 'customer', 'factor') # برای جلوگیری از ثبت چند امتیاز برای یک فاکتور در یک جشنواره توسط یک مشتری

    def __str__(self):
        return f'{self.customer} - {self.festival} ({self.points_awarded} امتیاز)'
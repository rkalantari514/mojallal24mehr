# Create your models here.
from django.db import models
from django.db import models
from mahakupdate.models import Factor, Person  # فرض بر اینکه مدل Factor در اپلیکیشن 'mahakupdate' قرار دارد
from django.db.models import Sum, F
from django.utils import timezone
from django.db.models import Count, Q

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

    def days(self):
        return (self.end_date - self.start_date).days

    def points_sum(self):
        result = CustomerPoints.objects.filter(festival=self).aggregate(total_points=Sum('points_awarded'))
        return result['total_points'] if result['total_points'] else 0

    def factor_sum(self):
        result = CustomerPoints.objects.filter(festival=self).annotate(
            net_amount=F('factor__mablagh_factor') - F('factor__takhfif')
        ).aggregate(total_sales=Sum('net_amount'))
        return result['total_sales']/10000000 if result['total_sales'] else 0

    def sms_status_counts(self):
        return CustomerPoints.objects.filter(festival=self).aggregate(
            not_sent=Count('status_code', filter=Q(status_code=None)),
            no_verified_number=Count('status_code', filter=Q(status_code=404)),
            sent=Count('status_code', filter=Q(status_code=0)),
            pending=Count('status_code', filter=Q(status_code=1)),
            delivered=Count('status_code', filter=Q(status_code=2)),
            failed=Count('status_code', filter=Q(status_code=3)),
            discarded=Count('status_code', filter=Q(status_code=4)),
        )




    @property
    def status_info(self):
        today = timezone.now().date()
        if self.start_date <= today <= self.end_date:
            return {'label': 'در حال اجرا', 'class': 'badge badge-success'}
        elif today > self.end_date:
            return {'label': 'پایان یافته', 'class': 'badge badge-warning'}
        else:  # today < self.start_date
            return {'label': 'شروع نشده', 'class': 'badge badge-primary'}




STATUS_DETAILS = {
    2: {"status": "Delivered ✅", "persian": "رسیده به گوشی", "color": "text-success", "icon": "fa-check"},
    4: {"status": "Discarded ❌", "persian": "رد شد", "color": "text-danger", "icon": "fa-times"},
    1: {"status": "Pending ⏳", "persian": "در انتظار ارسال", "color": "text-warning", "icon": "fa-clock"},
    3: {"status": "Failed ❌", "persian": "ناموفق", "color": "text-danger", "icon": "fa-exclamation-triangle"},
    0: {"status": "Sent 🚀", "persian": "ارسال شد", "color": "text-info", "icon": "fa-paper-plane"},
    None: {"status": "Not Sent 🚫", "persian": "ارسال نشد", "color": "text-secondary", "icon": "fa-envelope-o"},
    404: {"status": "No Verified Number 📵", "persian": "فاقد شماره تائید شده", "color": "text-warning",
          "icon": "fa-phone-slash"}

}




class CustomerPoints(models.Model):
    festival = models.ForeignKey(Festival, on_delete=models.CASCADE, related_name='customer_points', verbose_name='جشنواره')
    customer = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='customer_points', verbose_name='مشتری')
    factor = models.ForeignKey(Factor, on_delete=models.CASCADE, related_name='customer_points', verbose_name='فاکتور')
    points_awarded = models.IntegerField(default=0, verbose_name='امتیاز تعلق گرفته')
    award_date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ تعلق')
    message_id = models.CharField(blank=True, null=True, max_length=50, verbose_name="شناسه پیامک")
    phone_number = models.CharField(blank=True, null=True, max_length=150, verbose_name="شماره تلفن")
    status_code = models.IntegerField(blank=True, null=True, verbose_name="کد وضعیت پیامک")

    class Meta:
        verbose_name = 'امتیاز مشتری'
        verbose_name_plural = 'امتیازات مشتریان'
        unique_together = ('festival', 'customer', 'factor') # برای جلوگیری از ثبت چند امتیاز برای یک فاکتور در یک جشنواره توسط یک مشتری

    def __str__(self):
        return f'{self.customer} - {self.festival} ({self.points_awarded} امتیاز)'

    def get_status_details(self):
        return STATUS_DETAILS.get(self.status_code,
                                  {"status": "Unknown", "persian": "نامشخص", "color": "text-secondary",
                                   "icon": "fa-question"})

    def total_point_global(self):
        result = CustomerPoints.objects.filter(customer=self.customer).aggregate(total_points=Sum('points_awarded'))
        return result['total_points'] if result['total_points'] else 0

    def total_point_this_festival(self):
        result = CustomerPoints.objects.filter(customer=self.customer, festival=self.festival).aggregate(total_points=Sum('points_awarded'))
        return result['total_points'] if result['total_points'] else 0